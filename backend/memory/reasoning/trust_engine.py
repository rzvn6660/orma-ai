import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TrustEngine:
    """
    Calculates a Memory Trust Score (0-100) using:
    Confidence, Importance, Verification, Consistency, Usage, Recency
    """
    
    def calculate_score(self, memory: Dict[str, Any]) -> float:
        """
        Calculates the initial or updated trust score.
        """
        score = 0.0
        
        # 1. Confidence (0.0-1.0) -> Max 30 points
        conf = memory.get("confidence", 0.5)
        score += conf * 30.0
        
        # 2. Importance (0-100) -> Max 20 points
        imp = memory.get("importance", 50)
        score += (imp / 100.0) * 20.0
        
        # 3. Verification -> 10 points
        verified = memory.get("verified", False)
        if verified:
            score += 10.0
            
        # 4. Usage -> Max 20 points
        usage = memory.get("usage_count", 0)
        score += min(20.0, usage * 2.0)
        
        # 5. Source / Consistency -> 10 points for certain sources
        source = memory.get("source", "system")
        if source == "user_explicit" or source == "caregiver":
            score += 10.0
        elif source == "AI":
            score += 5.0
            
        # 6. Recency -> 10 points max
        last_used = memory.get("last_used")
        if last_used:
            # Assuming last_used is datetime
            now = datetime.utcnow()
            days = (now - last_used).days
            if days < 7:
                score += 10.0
            elif days < 30:
                score += 5.0
                
        logger.info(f"[TrustEngine] Calculated Trust Score: {score:.1f}")
        return min(100.0, max(0.0, score))

trust_engine = TrustEngine()
