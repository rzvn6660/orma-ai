import logging
import re
from typing import Dict, Any, Optional, List
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)

class FallbackProvider(BaseAIProvider):
    """
    Deterministic rule-based fallback provider for ORMA AI when cloud & local services are offline.
    Intelligently inspects database context in the prompt to answer questions about medicines,
    schedules, adherence, and healthcare accurately without hallucination.
    """
    @property
    def provider_name(self) -> str:
        return "fallback"

    @property
    def is_available(self) -> bool:
        return True

    def _extract_user_query(self, prompt: str) -> str:
        """Extracts the actual user query line from the prompt."""
        patterns = [
            r"User:\s*(.*?)(?:\n|$)",
            r"User Query:\s*\"?(.*?)\"?(?:\n|$)",
            r"User Question:\s*\"?(.*?)\"?(?:\n|$)",
            r"Text:\s*\"(.*?)\""
        ]
        for p in patterns:
            match = re.search(p, prompt, re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
        return prompt

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

        is_malayalam = "language preference is 'ml'" in (system_prompt or "").lower() or "മലയാളം" in full_text_lower or "respond in natural malayalam" in full_text_lower

        is_greeting = "user is greeting" in full_text_lower or any(g in query_lower for g in ["hello", "hi", "hey", "good morning", "good evening", "how do we do", "നമസ്കാരം", "ഹലോ"]) and not any(k in query_lower for k in ["medicine", "pill", "medication", "dosage", "മരുന്ന്"])

        if is_greeting:
            reply = "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ ഓർമ AI ഹെൽത്ത് അസിസ്റ്റന്റ് ആണ്. ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?" if is_malayalam else "Hello! I am Orma, your healthcare companion. How can I help you today?"
        elif "medication schedule" in full_text_lower:
            med_records = self._extract_medicine_records(prompt)
            if not med_records:
                reply = "ഈ സമയത്തേക്ക് നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_malayalam else "You have no medicines scheduled for this time period."
            else:
                med_list_str = ", ".join(f"{m['name_dosage']} at {m['time']}" for m in med_records)
                reply = f"നിങ്ങളുടെ ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഇവയാണ്: {med_list_str}." if is_malayalam else f"Your scheduled medicines for this time are: {med_list_str}."
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
        elif "medication adherence summary" in full_text_lower:
            med_records = self._extract_medicine_records(prompt)
            total = len(med_records)
            taken = sum(1 for m in med_records if m["is_taken"])
            pct = int((taken / total) * 100) if total > 0 else 100
            reply = f"ഇന്ന് നിങ്ങൾക്ക് {total} മരുന്നുകളിൽ {taken} എണ്ണം പൂർത്തിയായി ({pct}% അഡ്ഹെറൻസ്)." if is_malayalam else f"Today you have taken {taken} out of {total} scheduled medicines ({pct}% adherence)."
        elif "untrusted patient document context" in full_text_lower or "document excerpt" in full_text_lower:
            # Extract excerpts from prompt
            excerpts = re.findall(r"---\s*\[Document Excerpt.*?\]\s*---\s*(.*?)\s*---", prompt, re.DOTALL)
            if not excerpts:
                # Check for general document lines
                excerpts = [p.strip() for p in prompt.split("\n") if "diet" in p.lower() or "salt" in p.lower() or "protein" in p.lower() or "instruction" in p.lower()]
            
            if excerpts:
                # Find excerpt matching query keywords
                matched_snippet = None
                for exc in excerpts:
                    cleaned_exc = exc.strip()
                    if any(k in cleaned_exc.lower() for k in query_lower.split() if len(k) > 3):
                        matched_snippet = cleaned_exc
                        break
                if not matched_snippet and excerpts:
                    matched_snippet = excerpts[0].strip()

                # Clean and take first 1-2 key sentences
                first_sentences = " ".join([s.strip() for s in matched_snippet.split("\n") if s.strip() and not s.startswith("---")][:2])
                reply = f"According to your document: {first_sentences}."
            else:
                reply = "എന്റെ പക്കലുള്ള രേഖകളിൽ ആ വിവരങ്ങൾ കണ്ടെത്താൻ കഴിഞ്ഞില്ല." if is_malayalam else "I couldn't find that information in the documents I have."
        elif any(e in query_lower for e in ["pain", "hurt", "emergency", "ambulance", "hospital", "വേദന", "അപകടം"]):
            reply = "അടിയന്തിര സാഹചര്യമാണെങ്കിൽ ദയവായി ശാന്തരായിരിക്കുക. ഞാൻ നിങ്ങളുടെ കെയർഗിവറെ ഉടൻ അറിയിക്കാം." if is_malayalam else "If you need immediate assistance, please remain calm. I can notify your caregiver right away."
        else:
            reply = "നിങ്ങളുടെ ആരോഗ്യം, മരുന്നുകൾ, ഷെഡ്യൂൾ എന്നിവയിൽ സഹായിക്കാൻ ഞാൻ ഇവിടെയുണ്ട്." if is_malayalam else "I am here to assist you with your medicines, health reminders, and daily schedule."

        return {
            "text": reply,
            "provider": self.provider_name,
            "model": "rule-fallback-1.0",
            "success": True,
            "error": None,
            "fallback_used": True
        }

