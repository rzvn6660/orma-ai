import asyncio
import httpx
from sqlalchemy.orm import Session
from services.memory_service import retrieve_memory_context, extract_and_store_memory
from services.medicine_service import mark_latest_pending_taken, get_latest_pending_medicine, get_all_pending_medicines, get_all_taken_medicines, mark_taken
from ai.intent_service import detect_medicine_confirmation, detect_medicine_status_inquiry
from ai.adherence_service import calculate_confidence_score
from ai.confusion_service import detect_and_log_confusion
import datetime

class SessionMemoryManager:
    """
    Maintains short-term conversational context for seamless follow-ups.
    """
    def __init__(self):
        self.sessions = {} # user_id -> list of message dicts
        
    def add_message(self, user_id: str, role: str, content: str):
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        self.sessions[user_id].append({"role": role, "content": content})
        # Keep only the last 6 messages (3 turns)
        if len(self.sessions[user_id]) > 6:
            self.sessions[user_id] = self.sessions[user_id][-6:]
            
    def get_context_string(self, user_id: str) -> str:
        if user_id not in self.sessions or not self.sessions[user_id]:
            return ""
        context = "Recent Conversation History:\n"
        for msg in self.sessions[user_id]:
            prefix = "User" if msg["role"] == "user" else "Orma"
            context += f"{prefix}: {msg['content']}\n"
        return context

class ConversationService:
    def __init__(self):
        self.session_manager = SessionMemoryManager()
        # Placeholder for LLM client initialization (e.g., OpenAI, Langchain API)
        pass
    
    async def generate_response(self, text: str, user_id: str = "default_user", language_preference: str = "auto", detected_language: str = "en", db: Session = None) -> str:
        """
        Takes user text and returns an AI response, tailored for elderly users.
        Uses Ollama (Llama 3) for inference.
        """
        memory_context = ""
        is_confused = False
        
        # Determine final response language intent
        if language_preference == "en":
            final_language = "en"
        elif language_preference == "ml":
            final_language = "ml"
        else:
            final_language = detected_language
        
        if db:
            is_confused = detect_and_log_confusion(db, text, user_id)
            
            # Handle Medicine Status Inquiry Intent
            if detect_medicine_status_inquiry(text):
                pending = get_all_pending_medicines(db)
                taken = get_all_taken_medicines(db)
                
                if pending:
                    med = pending[0]
                    if final_language == "ml":
                        reply = f"ഇല്ല, ഇന്ന് നിങ്ങളുടെ {med.medicine_name} എടുത്തതായി രേഖപ്പെടുത്തിയിട്ടില്ല."
                    else:
                        reply = f"No, your {med.medicine_name} is still pending."
                elif taken:
                    med = taken[-1]
                    if final_language == "ml":
                        reply = f"അതെ, നിങ്ങൾ {med.medicine_name} എടുത്തിട്ടുണ്ട്."
                    else:
                        reply = f"Yes, you already took {med.medicine_name}."
                else:
                    if final_language == "ml":
                        reply = "ഇന്ന് മരുന്നുകളൊന്നും ഷെഡ്യൂൾ ചെയ്തിട്ടില്ല."
                    else:
                        reply = "No medicines are scheduled for today."
                
                self.session_manager.add_message(user_id, "user", text)
                self.session_manager.add_message(user_id, "assistant", reply)
                return reply

            # Handle Medicine Confirmation Intent
            if detect_medicine_confirmation(text):
                pending = get_all_pending_medicines(db)
                if not pending:
                    if final_language == "ml":
                        reply = "പെൻഡിങ് മരുന്നുകൾ ഒന്നുമില്ല."
                    else:
                        reply = "You have no pending medicines to take."
                elif pending:
                    # Try to find a matching medicine by name in the user text
                    matched_med = None
                    text_lower = text.lower()
                    for med in pending:
                        if med.medicine_name.lower() in text_lower:
                            matched_med = med
                            break
                    
                    if matched_med:
                        mark_taken(db, matched_med.id)
                        if final_language == "ml":
                            reply = f"ശരി, നിങ്ങളുടെ {matched_med.medicine_name} എടുത്തതായി രേഖപ്പെടുത്തി."
                        else:
                            reply = f"Okay, I've marked {matched_med.medicine_name} as taken."
                    elif len(pending) == 1:
                        med = pending[0]
                        mark_taken(db, med.id)
                        if final_language == "ml":
                            reply = f"ശരി, നിങ്ങളുടെ {med.medicine_name} എടുത്തതായി രേഖപ്പെടുത്തി."
                        else:
                            reply = f"Okay, I've marked {med.medicine_name} as taken."
                    else:
                        if final_language == "ml":
                            reply = "ഏത് മരുന്നാണ് നിങ്ങൾ എടുത്തത്?"
                        else:
                            reply = "Which medicine did you take?"
                        
                self.session_manager.add_message(user_id, "user", text)
                self.session_manager.add_message(user_id, "assistant", reply)
                return reply
            # 1. Run rule-based memory extraction on the user's speech
            extract_and_store_memory(db, text, user_id)
            # 2. Retrieve any relevant memories to answer the user
            memory_context = retrieve_memory_context(db, text, user_id)
        
        system_prompt = (
            "You are Orma, a calm, supportive, and highly concise AI healthcare assistant for elderly users. "
            "CRITICAL INSTRUCTIONS FOR EVERY RESPONSE:\n"
            "- Responses MUST be extremely short and direct (1-2 short sentences max).\n"
            "- Do NOT use overly conversational filler, fake empathy, or long paragraphs (e.g., avoid 'Don't worry!').\n"
            "- Be clear, factual, and calm.\n"
            "- Focus strictly on medicine status or the user's direct question.\n"
            "- Do NOT hallucinate medical advice or make up facts. Stick to the database context.\n"
            "- Use simple language to minimize cognitive load.\n"
            "Example Good Response: 'You have not taken Amlodipine yet today.'\n"
            "Example Bad Response: 'Oh no! Don't worry, we can work on getting you caught up. You haven't taken...'"
        )
        
        if memory_context:
            system_prompt += f"\n{memory_context}"
            
        # 3. Add short-term session history for context continuity
        session_history = self.session_manager.get_context_string(user_id)
        if session_history:
            system_prompt += f"\n{session_history}"
            
        if is_confused:
            system_prompt += (
                "\nCRITICAL STATE: The user is exhibiting signs of cognitive confusion or repeating questions. "
                "You MUST drastically simplify your response. Be extremely gentle, reassuring, and calm. "
                "Do NOT point out that they asked this already. Answer directly and softly."
            )
        system_prompt += (
            "\n\nCRITICAL MULTILINGUAL INSTRUCTIONS:\n"
            "You are ORMA AI.\n"
            f"The user's language preference is '{language_preference}'.\n"
            f"The detected language of the user's message by the speech engine is '{detected_language}'.\n"
            "Always respond in the language determined by the user's language preference.\n"
            "If the preference is 'auto':\n"
            "  - Respond in the same language as the user's message.\n"
            "  - IF the user's message is in Manglish (Malayalam written in English characters), you MUST respond natively in Malayalam script (മലയാളം).\n"
            "Never change the language unless the user changes the setting.\n"
            "Never mix English and Malayalam unless absolutely necessary.\n"
            "Always keep medicine names consistent in English characters (e.g. Metformin, Amlodipine, Paracetamol).\n"
            "Do NOT translate or transliterate medicine names to Malayalam script.\n"
            "Always retrieve medicine information from the database before answering."
        )

        prompt = f"{system_prompt}\n\nUser: {text}\nOrma:"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 40
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("response", "").strip()
                    
                    # Memory save prepared for future
                    # memory_service.add_memory(...)
                    
                    # Save to short term session
                    self.session_manager.add_message(user_id, "user", text)
                    self.session_manager.add_message(user_id, "assistant", reply)
                    
                    return reply
                else:
                    reply = self._fallback_mock_response(text, final_language, memory_context)
                    self.session_manager.add_message(user_id, "user", text)
                    self.session_manager.add_message(user_id, "assistant", reply)
                    return reply
                    
        except httpx.RequestError:
            print("Ollama is not running or accessible. Falling back to mock responses.")
            reply = self._fallback_mock_response(text, language, memory_context)
            self.session_manager.add_message(user_id, "user", text)
            self.session_manager.add_message(user_id, "assistant", reply)
            return reply

    def _fallback_mock_response(self, text: str, final_language: str, memory_context: str = "") -> str:
        text_lower = text.lower()
        if "pill" in text_lower or "medicine" in text_lower or "blood pressure" in text_lower or "മരുന്ന്" in text_lower:
            if memory_context and "Medicine Status for Today:" in memory_context:
                prefix = "Context Information from User's Database:\nMedicine Status for Today:\n"
                cleaned_context = memory_context.replace(prefix, "").replace("- ", "").strip()
                return cleaned_context

            if final_language == "ml":
                return "രാവിലെ മരുന്ന് കഴിച്ചിട്ടുണ്ട്."
            return "You took your medication this morning."
        elif "hello" in text_lower or "hi" in text_lower or "നമസ്കാരം" in text_lower:
            if final_language == "ml":
                return "നമസ്കാരം. എന്ത് സഹായം വേണം?"
            return "Hello. How can I help you today?"
        else:
            if final_language == "ml":
                return "ഞാൻ ഇവിടെയുണ്ട്. എന്ത് വേണം?"
            return "I am here. Please tell me what you need."

# Instantiate a singleton service
conversation_service = ConversationService()
