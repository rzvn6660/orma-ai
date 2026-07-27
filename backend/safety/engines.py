import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PolicyEngine:
    """Evaluates requests against clinical safety rules."""
    
    def evaluate(self, request_text: str, intent: str) -> Dict[str, Any]:
        """
        ORMA must NEVER:
        - Diagnose diseases.
        - Prescribe medication.
        - Change medicine dosage.
        - Replace professional medical advice.
        """
        request_lower = request_text.lower()
        violations = []
        
        if "diagnose" in request_lower or "what disease" in request_lower:
            violations.append("NO_DIAGNOSIS")
        if "prescribe" in request_lower or "what medicine should i take" in request_lower:
            violations.append("NO_PRESCRIPTION")
        if "change my dose" in request_lower or "increase my dose" in request_lower:
            violations.append("NO_DOSAGE_CHANGE")
            
        if violations:
            return {
                "safe": False,
                "violations": violations,
                "reason": "Request violates clinical boundaries. Recommending healthcare professional contact."
            }
        return {"safe": True, "violations": [], "reason": "No policy violations detected."}

class RiskEngine:
    """Assigns configurable risk scores to requests."""
    
    def calculate_risk(self, request_text: str, intent: str) -> str:
        text_lower = request_text.lower()
        
        # Critical
        if any(w in text_lower for w in ["chest pain", "heart attack", "stroke", "cannot breathe", "collapsed", "kill myself"]):
            return "Critical"
            
        # High
        if "change" in text_lower and "dose" in text_lower:
            return "High"
            
        # Medium
        if intent in ["Health Summary", "MemoryQuery"]:
            return "Medium"
            
        return "Low"

policy_engine = PolicyEngine()
risk_engine = RiskEngine()
