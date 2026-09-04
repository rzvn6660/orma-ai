import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoryClassifier:
    """
    Classifies raw memory candidates into predefined categories.
    """
    VALID_CATEGORIES = [
        "Personal", "Family", "Health", "Medicine", "Appointment",
        "Preference", "Important Event", "Temporary", "Conversation", "Custom"
    ]

    def __init__(self):
        pass

    def classify(self, text: str, context_intent: str = "", title: str = "") -> str:
        """
        Classifies the memory based on text, title, and original orchestration intent.
        """
        logger.info(f"[MemoryClassifier] Classifying memory candidate: '{text}' | Title: '{title}' (Intent: {context_intent})")
        
        # Rule-based matching
        combined = f"{title} {text}".lower().strip()
        
        if context_intent == "Medicine" or any(w in combined for w in ["pill", "dosage", "tablet", "capsule"]):
            return "Medicine"
            
        if context_intent == "Appointment" or any(w in combined for w in ["doctor", "clinic", "hospital", "appointment"]):
            return "Appointment"
            
        if context_intent == "HealthRecord" or any(w in combined for w in ["blood", "test", "pressure", "reading"]):
            return "Health"
            
        if any(w in combined for w in ["son", "daughter", "wife", "husband", "grandson", "granddaughter", "brother", "sister", "mother", "father", "caregiver", "family"]):
            return "Family"
            
        if any(w in combined for w in ["like", "prefer", "hate", "favorite", "preference", "language", "reminder language"]):
            return "Preference"
            
        if any(w in combined for w in ["birthday", "anniversary", "passed away", "wedding"]):
            return "Important Event"
            
        if any(w in combined for w in ["name is", "live in", "born in", "allergy", "allergic"]):
            return "Personal"
            
        # Default fallback
        logger.info("[MemoryClassifier] No specific category matched, falling back to Conversation")
        return "Conversation"

memory_classifier = MemoryClassifier()
