import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class ConfidenceEngine:
    """
    Evaluates how confident the system is in the extracted memory.
    Recommends: AUTO_SAVE, ASK_CONFIRMATION, or DISCARD.
    """
    def __init__(self):
        pass

    def evaluate_confidence(self, text: str, extraction_confidence: float) -> Tuple[float, str]:
        """
        Returns (confidence_score_0_to_1, recommendation).
        """
        logger.info(f"[ConfidenceEngine] Evaluating confidence. Base extraction confidence: {extraction_confidence}")
        
        confidence = extraction_confidence
        
        text_lower = text.lower()
        if any(w in text_lower for w in ["i think", "maybe", "probably", "not sure", "guess"]):
            confidence -= 0.3
            logger.info("[ConfidenceEngine] Uncertainty detected. Reduced confidence.")
            
        if any(w in text_lower for w in ["definitely", "always", "i am sure"]):
            confidence += 0.2
            logger.info("[ConfidenceEngine] Certainty detected. Increased confidence.")
            
        confidence = max(0.0, min(1.0, confidence))
        
        if confidence >= 0.8:
            recommendation = "AUTO_SAVE"
        elif confidence >= 0.4:
            recommendation = "ASK_CONFIRMATION"
        else:
            recommendation = "DISCARD"
            
        logger.info(f"[ConfidenceEngine] Final Confidence: {confidence:.2f} | Recommendation: {recommendation}")
        return confidence, recommendation

confidence_engine = ConfidenceEngine()
