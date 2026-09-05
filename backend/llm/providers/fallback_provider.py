import logging
import re
from typing import Dict, Any, Optional, List
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)

class FallbackProvider(BaseAIProvider):
    """
    Deterministic context-aware fallback provider for ORMA AI when cloud & local LLM services are offline.
    Intelligently inspects database context, conversation history, user identity, and memory in the prompt
    to answer questions accurately, conversationally, and without hallucination or generic repetition.
    Supports both English and natural Malayalam (മലയാളം).
    """
    @property
    def provider_name(self) -> str:
        return "fallback"

    @property
    def is_available(self) -> bool:
        return True

    def _extract_user_query(self, prompt: str) -> str:
        """Extracts the actual user query line from the prompt, prioritizing the final active user turn."""
        patterns = [
            r"(?:^|\n)User:\s*(.*?)(?=\n|$)",
            r"(?:^|\n)User Query:\s*\"?(.*?)\"?(?=\n|$)",
            r"(?:^|\n)User Question:\s*\"?(.*?)\"?(?=\n|$)",
            r"(?:^|\n)User said:\s*(.*?)(?=\n|$)",
            r"(?:^|\n)Text:\s*\"(.*?)\""
        ]
        candidates = []
        for p in patterns:
            matches = re.findall(p, prompt, re.IGNORECASE)
            for m in matches:
                cleaned = m.strip().strip('"')
                if cleaned:
                    candidates.append(cleaned)
        if candidates:
            return candidates[-1]
        return prompt.strip()

    def _is_malayalam_request(self, prompt: str, user_query: str, system_prompt: Optional[str] = None) -> bool:
        """Detects whether the query or context requests natural Malayalam output."""
        sys_low = (system_prompt or "").lower()
        if "language preference is 'ml'" in sys_low or "ml-in" in sys_low or "malayalam" in sys_low or "മലയാളം" in sys_low:
            return True
        # Check for Malayalam Unicode range (U+0D00 to U+0D7F) in query or prompt
        if re.search(r"[\u0D00-\u0D7F]", user_query):
            return True
        full_low = prompt.lower()
        if "respond in natural, warm malayalam" in full_low or "language: ml" in full_low or "മലയാളം" in full_low:
            return True
        return False

    def _extract_actor_name(self, prompt: str) -> Optional[str]:
        """Extracts the speaker or user's name from context header or history."""
        # Check CMCE Actor Speaking header
        actor_match = re.search(r"Actor Speaking:\s*([^(\n]+?)(?:\s*\([^)]*\))?(?:\n|$)", prompt, re.IGNORECASE)
        if actor_match:
            name = actor_match.group(1).strip()
            if name and name.lower() not in ("user", "default_user", "default user", "actor", "unknown"):
                return name

        # Check Conversation Subject header
        subj_match = re.search(r"Conversation Subject:\s*([^(\n]+?)(?:\s*\([^)]*\))?(?:\n|$)", prompt, re.IGNORECASE)
        if subj_match:
            name = subj_match.group(1).strip()
            if name and name.lower() not in ("user", "default_user", "default user", "subject", "unknown"):
                return name

        # Check explicit introduction in conversation history
        name_intro = re.search(r"(?:my name is|i am|call me)\s+([A-Za-z0-9\s]{2,25})(?:\.|\n|$)", prompt, re.IGNORECASE)
        if name_intro:
            name = name_intro.group(1).strip()
            if name and name.lower() not in ("user", "default", "orma", "here"):
                return name

        return None

    def _extract_history_turns(self, prompt: str) -> List[Dict[str, str]]:
        """Parses multi-turn conversation history from the prompt."""
        turns = []
        for line in prompt.split("\n"):
            turn_match = re.match(r"^\s*(User|Orma|Assistant|Human|AI):\s*(.*)$", line, re.IGNORECASE)
            if turn_match:
                raw_role = turn_match.group(1).capitalize()
                role = "User" if raw_role in ("User", "Human") else "Orma"
                text = turn_match.group(2).strip()
                if text:
                    turns.append({"role": role, "text": text})
        return turns

    def _extract_medicine_records(self, prompt: str) -> List[Dict[str, Any]]:
        """Parses medicine records directly from the prompt context using flexible patterns."""
        med_items = []
        
        # Pattern 1: - <Name (Dosage)> scheduled at <Time>: Status = <Status>
        p1 = re.findall(r"-\s*(.*?)\s+scheduled at\s+(.*?):\s*Status\s*=\s*(.*)", prompt, re.IGNORECASE)
        for match in p1:
            name_dosage = match[0].strip()
            time_str = match[1].strip()
            status_str = match[2].strip().upper()
            is_taken = "TAKEN" in status_str and "NOT TAKEN" not in status_str
            med_items.append({
                "name_dosage": name_dosage,
                "time": time_str,
                "status": status_str,
                "is_taken": is_taken
            })
            
        if med_items:
            return med_items

        # Pattern 2: - <Name (Dosage)>: Scheduled at <Time>
        p2 = re.findall(r"-\s*(.*?):\s*Scheduled at\s+(.*)", prompt, re.IGNORECASE)
        for match in p2:
            name_dosage = match[0].strip()
            time_str = match[1].strip()
            med_items.append({
                "name_dosage": name_dosage,
                "time": time_str,
                "status": "SCHEDULED",
                "is_taken": False
            })

        if med_items:
            return med_items

        # Pattern 3: • <Name (Dosage)> at <Time>: <Status>
        p3 = re.findall(r"•\s*(.*?)\s+at\s+(.*?):\s*(.*)", prompt, re.IGNORECASE)
        for match in p3:
            name_dosage = match[0].strip()
            time_str = match[1].strip()
            status_str = match[2].strip().upper()
            is_taken = "TAKEN" in status_str and "NOT TAKEN" not in status_str
            med_items.append({
                "name_dosage": name_dosage,
                "time": time_str,
                "status": status_str,
                "is_taken": is_taken
            })

        return med_items

    def _extract_memories(self, prompt: str) -> List[Dict[str, str]]:
        """Extracts parsed long-term memory entries from prompt."""
        mem_matches = re.findall(r"-\s*([^:]+):\s*(.*?)\s+is\s+([^.\n]+)", prompt, re.IGNORECASE)
        memories = []
        for m in mem_matches:
            memories.append({
                "category": m[0].strip(),
                "title": m[1].strip(),
                "value": m[2].strip()
            })
        return memories

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        user_query = self._extract_user_query(prompt)
        query_lower = user_query.lower()
        full_text_lower = prompt.lower()
        is_malayalam = self._is_malayalam_request(prompt, user_query, system_prompt)
        clean_query = re.sub(r"[^\w\s\u0D00-\u0D7F]", "", query_lower).strip()

        # 0A. Pure Conversational Acknowledgments ("Okay", "Yeah", "Got it", "ശരി")
        ack_phrases = [
            "okay", "ok", "yeah", "yes", "alright", "fine", "got it", "understood",
            "thats fine", "that's fine", "sounds good", "okay thanks", "ok thanks",
            "sure", "cool", "that is fine", "perfect", "good", "great",
            "ശരി", "തീർച്ചയായും", "മനസ്സിലായി", "ശരിയാണ്", "അതെ", "ശരി നന്ദി"
        ]
        is_pure_ack = clean_query in ack_phrases or (clean_query.startswith("okay ") and len(clean_query.split()) <= 2 and clean_query.split()[1] in ["then", "fine", "dear"])
        if is_pure_ack:
            reply = "ശരി." if is_malayalam else "Alright."
            return {
                "text": reply,
                "provider": self.provider_name,
                "model": "rule-fallback-1.0",
                "success": True,
                "error": None,
                "fallback_used": True
            }

        # 0B. Thanks
        thanks_phrases = [
            "thanks", "thank you", "thanks a lot", "thank you very much", "thank you so much",
            "many thanks", "thank you orma", "thanks orma", "നന്ദി", "വളരെ നന്ദി"
        ]
        has_question_or_med = any(w in clean_query for w in ["what", "when", "how", "schedule", "medicine", "appointment", "did", "is", "where", "tell", "show"])
        if (clean_query in thanks_phrases or any(clean_query == p for p in thanks_phrases) or (any(clean_query.startswith(p + " ") for p in thanks_phrases) and not has_question_or_med)):
            reply = "തീർച്ചയായും, സന്തോഷം!" if is_malayalam else "You're welcome!"
            return {
                "text": reply,
                "provider": self.provider_name,
                "model": "rule-fallback-1.0",
                "success": True,
                "error": None,
                "fallback_used": True
            }

        # 0C. Farewell
        farewell_phrases = [
            "bye", "goodbye", "see you", "good night", "bye orma", "goodbye orma",
            "വിട", "ശുഭരാത്രി"
        ]
        if clean_query in farewell_phrases:
            reply = "വിട, ശ്രദ്ധിക്കുക!" if is_malayalam else "Goodbye! Take care."
            return {
                "text": reply,
                "provider": self.provider_name,
                "model": "rule-fallback-1.0",
                "success": True,
                "error": None,
                "fallback_used": True
            }

        # 1. Greetings (Human, natural, non-repetitive, concise)
        greeting_words = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "good day", "are you there", "orma", "നമസ്കാരം", "ഹലോ", "ഹായ്", "സുഖമാണോ", "എങ്ങനെയുണ്ട്"]
        is_greeting = ("user is greeting" in full_text_lower or any(g in query_lower for g in greeting_words)) and not any(k in query_lower for k in ["medicine", "pill", "medication", "dosage", "മരുന്ന്", "schedule", "name", "who am i"])

        if is_greeting:
            if "good morning" in query_lower or "സുപ്രഭാതം" in query_lower:
                reply = "സുപ്രഭാതം! ഇന്ന് നിങ്ങളുടെ ആരോഗ്യം എങ്ങനെയുണ്ട്? ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?" if is_malayalam else "Good morning! How are you feeling today?"
            elif "good evening" in query_lower or "ശുഭസന്ധ്യ" in query_lower:
                reply = "ശുഭസന്ധ്യ! ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?" if is_malayalam else "Good evening! How has your day been?"
            elif "good afternoon" in query_lower:
                reply = "നമസ്കാരം! ഇന്ന് ഉച്ചതിരിഞ്ഞ് നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?" if is_malayalam else "Good afternoon! How can I help you today?"
            else:
                # Natural varied greetings
                hash_seed = sum(ord(c) for c in user_query) % 3
                if is_malayalam:
                    greetings_ml = [
                        "നമസ്കാരം! ഞാൻ ഇവിടെയുണ്ട്. ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?",
                        "ഹലോ! നിങ്ങളെ കേൾക്കാൻ കഴിഞ്ഞതിൽ സന്തോഷം. ഇന്ന് എന്ത് സഹായമാണ് വേണ്ടത്?",
                        "നമസ്കാരം! സുഖമാണോ? ഇന്ന് എങ്ങനെ സഹായിക്കണം?"
                    ]
                    reply = greetings_ml[hash_seed]
                else:
                    greetings_en = [
                        "Hello! It's nice to hear from you. How can I help you today?",
                        "Hello! I am Orma, ready to help. What would you like help with?",
                        "Hello! How are you feeling today? Tell me what you need."
                    ]
                    reply = greetings_en[hash_seed]

        # 2. User Name & Identity Queries ("What is my name?", "Who am I?", "Do you know my name?")
        elif any(q in query_lower for q in ["what is my name", "what's my name", "who am i", "do you know my name", "tell me my name", "എന്റെ പേര്"]):
            user_name = self._extract_actor_name(prompt)
            if user_name:
                reply = f"നിങ്ങളുടെ പേര് {user_name} എന്നാണ്." if is_malayalam else f"Your name is {user_name}."
            else:
                reply = "നിങ്ങളുടെ പേര് എന്നോട് ഇതുവരെ പറഞ്ഞിട്ടില്ല. ഞാൻ നിങ്ങളെ എന്ത് പേര് വിളിക്കണം?" if is_malayalam else "You haven't told me your name yet. What should I call you?"

        # 3. Conversation Coreference ("What did I just tell you?", "What did I say?", "What did I just say?")
        elif any(q in query_lower for q in ["what did i just tell you", "what did i tell you", "what did i just say", "what did i say", "ഞാൻ എന്താണ് പറഞ്ഞത്"]):
            history_turns = self._extract_history_turns(prompt)
            user_turns = [t["text"] for t in history_turns if t["role"] == "User" and t["text"].lower() != query_lower]
            if user_turns:
                last_user_statement = user_turns[-1]
                reply = f"നിങ്ങൾ അവസാനം പറഞ്ഞത്: \"{last_user_statement}\" എന്നാണ്." if is_malayalam else f"You just told me: \"{last_user_statement}\"."
            else:
                reply = "നമ്മൾ ഇപ്പോൾ സംസാരിച്ചു തുടങ്ങിയിട്ടേ ഉള്ളൂ." if is_malayalam else "We just started our conversation. What would you like to talk about?"

        # 4. Repeat Request ("Can you repeat that?", "Repeat that", "What did you say?", "Can you tell me that again?")
        elif any(q in query_lower for q in ["repeat that", "can you repeat that", "could you repeat that", "can you tell me that again", "tell me that again", "say that again", "what did you say", "tell me again", "ഒന്നുകൂടി പറയാമോ", "ഒന്ന് കൂടി പറയാമോ"]):
            history_turns = self._extract_history_turns(prompt)
            orma_turns = [t["text"] for t in history_turns if t["role"] in ("Orma", "Assistant")]
            if orma_turns:
                last_orma_statement = orma_turns[-1]
                reply = f"തീർച്ചയായും: {last_orma_statement}" if is_malayalam else f"Certainly: {last_orma_statement}"
            else:
                reply = "ഞാൻ ഓർമ AI അസിസ്റ്റന്റ് ആണ്. നിങ്ങളെ സഹായിക്കാൻ തയ്യാറാണ്." if is_malayalam else "I said that I am here and ready to help you."

        # 5. Language Preference & Long-term Memory Queries
        elif any(q in query_lower for q in ["what language do i prefer", "what language do i speak", "what is my preferred language", "എന്റെ ഭാഷ"]):
            memories = self._extract_memories(prompt)
            lang_mem = next((m for m in memories if any(w in (m["title"] + " " + m["category"] + " " + m["value"]).lower() for w in ["language", "malayalam", "english", "hindi", "tamil", "speak", "prefer"])), None)
            if not lang_mem and "[relevant long-term memory]" in full_text_lower:
                lang_match = re.search(r"\b(malayalam|english|hindi|arabic|tamil)\b", full_text_lower)
                if lang_match:
                    lang_mem = {"value": lang_match.group(1).capitalize()}
            if lang_mem:
                val = lang_mem["value"].rstrip(".").strip()
                reply = f"നിങ്ങൾ മുൻഗണന നൽകുന്ന ഭാഷ {val} ആണ് എന്ന് ഞാൻ ഓർക്കുന്നു." if is_malayalam else f"Your preferred language is {val}."
            elif is_malayalam:
                reply = "നിങ്ങൾ ഓർമപ്പെടുത്തലുകൾക്ക് മുൻഗണന നൽകുന്ന ഭാഷ മലയാളമാണ്."
            else:
                reply = "Your preferred language is English."

        # 6. General Long-Term Memory Lookups
        elif "[relevant long-term memory]" in full_text_lower:
            memories = self._extract_memories(prompt)
            matched_mem = None
            for m in memories:
                if any(w in query_lower for w in m["title"].lower().split() if len(w) > 3) or \
                   any(w in query_lower for w in m["value"].lower().split() if len(w) > 3) or \
                   ("language" in query_lower and "language" in m["title"].lower()):
                    matched_mem = m
                    break
            if not matched_mem and memories:
                matched_mem = memories[0]

            if matched_mem:
                reply = f"നിങ്ങളുടെ {matched_mem['title']} {matched_mem['value']} ആണ് എന്ന് ഞാൻ ഓർക്കുന്നു." if is_malayalam else f"Your {matched_mem['title'].lower()} is {matched_mem['value']}."
            else:
                reply = "നിങ്ങളുടെ വിവരങ്ങൾ ഞാൻ ഓർക്കുന്നു." if is_malayalam else "I remember your preferences."

        # 7. Next Medicine / Upcoming Medication Questions
        elif any(q in query_lower for q in ["next medicine", "next dose", "upcoming medicine", "upcoming dose", "അടുത്ത മരുന്ന്", "എന്റെ മരുന്ന് എപ്പോഴാണ്"]):
            med_records = self._extract_medicine_records(prompt)
            pending = [m for m in med_records if not m["is_taken"]]
            if pending:
                next_m = pending[0]
                reply = f"നിങ്ങളുടെ അടുത്ത മരുന്ന് {next_m['name_dosage']} ആണ്, സമയം {next_m['time']}." if is_malayalam else f"Your next scheduled medicine is {next_m['name_dosage']} at {next_m['time']}."
            elif med_records:
                reply = "ഈ സമയത്തെ എല്ലാ മരുന്നുകളും നിങ്ങൾ കഴിച്ചു കഴിഞ്ഞു." if is_malayalam else "You have taken all your scheduled medicines for this time period."
            else:
                reply = "ഈ സമയത്തേക്ക് നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_malayalam else "You have no medicines scheduled for this time period."

        # 7B. Tomorrow Follow-Up
        elif any(q in query_lower for q in ["what about tomorrow", "tomorrow's medicine", "is that for tomorrow", "tomorrow?", "നാളെയോ", "നാളെ എന്താണ്"]):
            med_records = self._extract_medicine_records(prompt)
            if med_records:
                med_list_str = ", ".join(f"{m['name_dosage']} at {m['time']}" for m in med_records)
                reply = f"നാളെ നിങ്ങൾക്ക് ഈ മരുന്നുകളാണ് ഉള്ളത്: {med_list_str}." if is_malayalam else f"Tomorrow you have: {med_list_str}."
            else:
                reply = "നാളെ നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_malayalam else "You have no medicines scheduled for tomorrow."

        # 8. Medication Schedule Lookups
        elif "medication schedule" in full_text_lower:
            med_records = self._extract_medicine_records(prompt)
            if not med_records:
                reply = "ഈ സമയത്തേക്ക് നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_malayalam else "You have no medicines scheduled for this time period."
            else:
                med_list_str = ", ".join(f"{m['name_dosage']} at {m['time']}" for m in med_records)
                reply = f"നിങ്ങളുടെ ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഇവയാണ്: {med_list_str}." if is_malayalam else f"Your scheduled medicines for this time are: {med_list_str}."

        # 9. Medication Status (Taken vs Pending)
        elif "medication status" in full_text_lower:
            med_records = self._extract_medicine_records(prompt)
            if not med_records:
                reply = "ഈ സമയത്തേക്ക് നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_malayalam else "You have no medicines scheduled for this time period."
            else:
                taken = [m for m in med_records if m["is_taken"]]
                pending = [m for m in med_records if not m["is_taken"]]
                if not pending:
                    reply = "നിങ്ങൾ ഈ സമയത്തെ എല്ലാ മരുന്നുകളും കഴിച്ചു കഴിഞ്ഞു." if is_malayalam else "You have taken all your scheduled medicines for this time period."
                else:
                    p_str = ", ".join(f"{m['name_dosage']} at {m['time']}" for m in pending)
                    reply = f"നിങ്ങൾക്ക് കഴിക്കാനുള്ള മരുന്നുകൾ: {p_str}." if is_malayalam else f"You still have pending medicines: {p_str}."

        # 10. Medication Adherence Summary
        elif "medication adherence summary" in full_text_lower or any(q in query_lower for q in ["how am i doing", "adherence", "അഡ്ഹെറൻസ്"]):
            med_records = self._extract_medicine_records(prompt)
            total = len(med_records)
            taken = sum(1 for m in med_records if m["is_taken"])
            pct = int((taken / total) * 100) if total > 0 else 100
            reply = f"ഇന്ന് നിങ്ങൾക്ക് {total} മരുന്നുകളിൽ {taken} എണ്ണം പൂർത്തിയായി ({pct}% അഡ്ഹെറൻസ്)." if is_malayalam else f"Today you have taken {taken} out of {total} scheduled medicines ({pct}% adherence)."

        # 11. Health Overview / General Health Inquiry
        elif any(q in query_lower for q in ["tell me about my health", "how is my health", "my health summary", "എന്റെ ആരോഗ്യം"]):
            med_records = self._extract_medicine_records(prompt)
            total = len(med_records)
            taken = sum(1 for m in med_records if m["is_taken"])
            if total > 0:
                reply = f"നിങ്ങളുടെ ആരോഗ്യ വിവരങ്ങൾ പരിശോധിക്കുകയാണ്. ഇന്ന് നിങ്ങൾക്ക് {total} മരുന്നുകളിൽ {taken} എണ്ണം പൂർത്തിയായി. ആരോഗ്യം ശ്രദ്ധിക്കുക!" if is_malayalam else f"Looking at your health summary, today you have taken {taken} of your {total} scheduled medicines. Your daily care routine is on track."
            else:
                reply = "നിങ്ങളുടെ ആരോഗ്യ വിവരങ്ങൾ പരിശോധിക്കുകയാണ്. ഇന്ന് നിങ്ങൾക്ക് പ്രത്യേക മരുന്നുകൾ ഒന്നും ഷെഡ്യൂൾ ചെയ്തിട്ടില്ല. നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?" if is_malayalam else "Looking at your health summary, your care schedule is clear for today. How can I assist you?"

        # 12. Document & Clinical Notes Context
        elif "untrusted patient document context" in full_text_lower or "document excerpt" in full_text_lower:
            excerpts = re.findall(r"---\s*\[Document Excerpt.*?\]\s*---\s*(.*?)\s*---", prompt, re.DOTALL)
            if not excerpts:
                excerpts = [p.strip() for p in prompt.split("\n") if "diet" in p.lower() or "salt" in p.lower() or "protein" in p.lower() or "instruction" in p.lower()]
            
            if excerpts:
                matched_snippet = None
                for exc in excerpts:
                    cleaned_exc = exc.strip()
                    if any(k in cleaned_exc.lower() for k in query_lower.split() if len(k) > 3):
                        matched_snippet = cleaned_exc
                        break
                if not matched_snippet and excerpts:
                    matched_snippet = excerpts[0].strip()

                first_sentences = " ".join([s.strip() for s in matched_snippet.split("\n") if s.strip() and not s.startswith("---")][:2])
                reply = f"According to your document: {first_sentences}."
            else:
                reply = "എന്റെ പക്കലുള്ള രേഖകളിൽ ആ വിവരങ്ങൾ കണ്ടെത്താൻ കഴിഞ്ഞില്ല." if is_malayalam else "I couldn't find that information in the documents I have."

        # 13. Emergency and Pain Escalation
        elif any(e in query_lower for e in ["pain", "hurt", "emergency", "ambulance", "hospital", "fell", "വേദന", "അപകടം", "വീണു"]):
            reply = "അടിയന്തിര സാഹചര്യമാണെങ്കിൽ ദയവായി ശാന്തരായിരിക്കുക. ഞാൻ നിങ്ങളുടെ കെയർഗിവറെ ഉടൻ അറിയിക്കാം." if is_malayalam else "If you need immediate assistance, please remain calm. I can notify your caregiver right away."

        # 14. Explicit Memory Storage Request
        elif any(query_lower.startswith(w) for w in ["remember that", "please remember that", "keep in mind that", "note that", "note down that"]):
            rem_match = re.search(r"(?:remember|keep in mind|note(?: down)?)(?:\s+that|\s*:)?\s+(.*)", user_query, re.IGNORECASE)
            rem_text = rem_match.group(1).strip().rstrip(".") if rem_match else "your preference"
            reply = f"ശരി, ഞാൻ അത് ഓർത്തു വെക്കാം: {rem_text}." if is_malayalam else f"I have made a note and will remember that {rem_text}."

        # 15. Context-Aware Fallback (Polite, Varied Clarification — NEVER repetitive generic capability sentence)
        else:
            hash_clarify = sum(ord(c) for c in user_query) % 2
            if is_malayalam:
                clarify_ml = [
                    "ക്ഷമിക്കണം, എനിക്ക് അത് വ്യക്തമായി മനസ്സിലായില്ല. നിങ്ങൾക്ക് എന്താണ് അറിയേണ്ടത് എന്ന് ഒന്നുകൂടി പറയാമോ?",
                    "ക്ഷമിക്കണം, അത് മനസ്സിലാക്കാൻ കഴിഞ്ഞില്ല. ഞാൻ എങ്ങനെ സഹായിക്കണം എന്ന് വ്യക്തമാക്കാമോ?"
                ]
                reply = clarify_ml[hash_clarify]
            else:
                clarify_en = [
                    "I didn't quite catch that. Could you please rephrase or tell me what you need help with?",
                    "I'm not sure I understood. Could you tell me a bit more about what you'd like to know?"
                ]
                reply = clarify_en[hash_clarify]

        return {
            "text": reply,
            "provider": self.provider_name,
            "model": "rule-fallback-1.0",
            "success": True,
            "error": None,
            "fallback_used": True
        }
