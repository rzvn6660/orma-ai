import logging
import httpx
from typing import Tuple

logger = logging.getLogger(__name__)

class IntentDetector:
    """
    Hybrid Intent Detection: Rules first, LLM fallback.
    Returns (Intent, Confidence).
    """
    VALID_INTENTS = [
        "Medicine", "Appointment", "HealthRecord", "Reminder", 
        "Memory", "Caregiver", "Emergency", "GeneralChat", "Settings", "Unknown"
    ]

    def __init__(self, use_llm=True):
        self.use_llm = use_llm

    async def detect_intent(self, text: str) -> Tuple[str, float]:
        """
        Detects the intent and returns a confidence score.
        """
        logger.info(f"[IntentDetector] Analyzing text: '{text}'")
        
        # 1. Rule Engine
        rule_intent = self._rule_based_detect(text)
        if rule_intent != "Unknown":
            logger.info(f"[IntentDetector] Rule matched: {rule_intent} (Confidence: 0.95)")
            return rule_intent, 0.95

        # 2. LLM Fallback
        if not self.use_llm:
            return "Unknown", 0.0

        prompt = (
            "You are an intent classification system for an elderly healthcare app.\n"
            "Classify the text into exactly ONE of these intents:\n"
            f"{', '.join(self.VALID_INTENTS)}\n\n"
            "Respond ONLY with the exact name of the intent, no extra text.\n\n"
            f"Text: \"{text}\"\nIntent:"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.0}
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    intent = data.get("response", "").strip()
                    
                    for valid in self.VALID_INTENTS:
                        if valid.lower() in intent.lower():
                            logger.info(f"[IntentDetector] LLM detected: {valid} (Confidence: 0.85)")
                            return valid, 0.85
                
                return "Unknown", 0.0
        except Exception as e:
            logger.warning(f"[IntentDetector] LLM detection failed: {e}. Returning Unknown.")
            return "Unknown", 0.0

    def _rule_based_detect(self, text: str) -> str:
        text = text.lower()
        if any(word in text for word in ["help", "emergency", "pain", "hurt", "hospital", "ambulance"]):
            return "Emergency"
        elif any(word in text for word in ["pill", "medicine", "medication", "dosage", "tablet", "syrup"]):
            return "Medicine"
        elif any(word in text for word in ["appointment", "doctor", "schedule", "visit", "clinic", "checkup"]):
            return "Appointment"
        elif any(word in text for word in ["remind", "alarm", "wake", "sleep", "water", "exercise"]):
            return "Reminder"
        elif any(word in text for word in ["record", "report", "test", "result", "blood", "pressure"]):
            return "HealthRecord"
        elif any(word in text for word in ["son", "daughter", "caregiver", "family", "call my"]):
            return "Caregiver"
        elif any(word in text for word in ["remember", "forgot", "what did i", "when did i", "where is"]):
            return "Memory"
        elif any(word in text for word in ["setting", "change", "language", "voice", "profile"]):
            return "Settings"
        elif any(word in text for word in ["hello", "hi", "how are you", "good morning", "good night"]):
            return "GeneralChat"
        return "Unknown"

intent_detector = IntentDetector()
