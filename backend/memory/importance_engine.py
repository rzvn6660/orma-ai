import logging

logger = logging.getLogger(__name__)

class ImportanceEngine:
    """
    Calculates the importance score of a memory candidate (0-100).
    """
    
    BASE_SCORES = {
        "Health": 90,
        "Medicine": 95,
        "Appointment": 85,
        "Important Event": 80,
        "Family": 75,
        "Personal": 70,
        "Preference": 60,
        "Conversation": 20,
        "Temporary": 10,
        "Custom": 50
    }

    def __init__(self):
        pass

    def calculate_importance(self, category: str, text: str) -> int:
        """
        Determines how important a memory is.
        """
        logger.info(f"[ImportanceEngine] Calculating importance for category '{category}'")
        
        score = self.BASE_SCORES.get(category, 50)
        
        text_lower = text.lower()
        
        # Boosters
        if any(w in text_lower for w in ["always", "never", "allergic", "emergency", "fatal"]):
            logger.info("[ImportanceEngine] High impact keyword detected. Boosting score.")
            score += 20
            
        # Penalties
        if any(w in text_lower for w in ["maybe", "guess", "think so", "not sure"]):
            logger.info("[ImportanceEngine] Uncertainty keyword detected. Penalizing score.")
            score -= 15
            
        # Clamp between 0 and 100
        final_score = max(0, min(100, score))
        logger.info(f"[ImportanceEngine] Final importance score: {final_score}")
        
        return final_score

importance_engine = ImportanceEngine()
