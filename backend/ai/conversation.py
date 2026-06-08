import asyncio
import httpx
from sqlalchemy.orm import Session
from services.memory_service import retrieve_memory_context, extract_and_store_memory
from services.medicine_service import mark_latest_pending_taken, get_latest_pending_medicine
from ai.intent_service import detect_medicine_confirmation
from ai.adherence_service import calculate_confidence_score
import datetime

class ConversationService:
    def __init__(self):
        # Placeholder for LLM client initialization (e.g., OpenAI, Langchain API)
        pass
    
    async def generate_response(self, text: str, user_id: str = "default_user", language: str = "en", db: Session = None) -> str:
        """
        Takes user text and returns an AI response, tailored for elderly users.
        Uses Ollama (Llama 3) for inference.
        """
        memory_context = ""
        if db:
            # 0. Check Multimodal Medicine Confirmation Intent
            if detect_medicine_confirmation(text):
                med = get_latest_pending_medicine(db)
                if med:
                    # Let's check time diff to determine response style
                    now = datetime.datetime.utcnow()
                    time_diff = int((now - med.reminder_triggered_at).total_seconds()) if med.reminder_triggered_at else 100
                    
                    if time_diff < 5:
                        # Mark it, but adherence_service will flag it with a low confidence score
                        med = mark_latest_pending_taken(db)
                        if language == "ml":
                            return f"അത് വളരെ വേഗത്തിലാണല്ലോ. ശരിക്കും {med.medicine_name} കഴിച്ചോ? ഞാൻ തത്കാലം വോയ്സ് വഴി രേഖപ്പെടുത്തിയിട്ടുണ്ട്."
                        return f"That was very fast! Are you sure you actually took your {med.medicine_name}? I have marked it as voice-confirmed for now."
                    else:
                        # Normal confirmation
                        med = mark_latest_pending_taken(db)
                        if language == "ml":
                            return f"ശരി, {med.medicine_name} മരുന്ന് വോയ്സ് വഴി സ്ഥിരീകരിച്ചു."
                        return f"Okay, I've marked your {med.medicine_name} as voice-confirmed."
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
        
        if language == "ml":
            system_prompt += (
                " You MUST respond entirely in the Malayalam language (മലയാളം). "
                "CRITICAL: Use casual, conversational Kerala Malayalam. "
                "Do NOT use formal, robotic, or literary textbook Malayalam. "
                "Keep words simple and commonly spoken by elders. "
                "For example, instead of 'നിങ്ങൾ ഔഷധം എടുത്തിട്ടില്ല', say 'ഇന്ന് മരുന്ന് എടുത്തിട്ടില്ല'. "
                "Instead of 'താങ്കൾക്ക് സഹായം ആവശ്യമുണ്ടോ', say 'സഹായം വേണോ?'."
            )

        prompt = f"{system_prompt}\n\nUser: {text}\nOrma:"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("response", "").strip()
                    
                    # Memory save prepared for future
                    # memory_service.add_memory(...)
                    
                    return reply
                else:
                    return self._fallback_mock_response(text, language, memory_context)
                    
        except httpx.RequestError:
            print("Ollama is not running or accessible. Falling back to mock responses.")
            return self._fallback_mock_response(text, language, memory_context)

    def _fallback_mock_response(self, text: str, language: str, memory_context: str = "") -> str:
        text_lower = text.lower()
        if "pill" in text_lower or "medicine" in text_lower or "blood pressure" in text_lower or "മരുന്ന്" in text_lower:
            if memory_context and "Medicine Status for Today:" in memory_context:
                prefix = "Context Information from User's Database:\nMedicine Status for Today:\n"
                cleaned_context = memory_context.replace(prefix, "").replace("- ", "").strip()
                return cleaned_context

            if language == "ml":
                return "രാവിലെ മരുന്ന് കഴിച്ചിട്ടുണ്ട്."
            return "You took your medication this morning."
        elif "hello" in text_lower or "hi" in text_lower or "നമസ്കാരം" in text_lower:
            if language == "ml":
                return "നമസ്കാരം. എന്ത് സഹായം വേണം?"
            return "Hello. How can I help you today?"
        else:
            if language == "ml":
                return "ഞാൻ ഇവിടെയുണ്ട്. എന്ത് വേണം?"
            return "I am here. Please tell me what you need."

# Instantiate a singleton service
conversation_service = ConversationService()
