import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from safety.engines import policy_engine, risk_engine
from safety.guards import consent_engine, privacy_engine, hallucination_guard
from safety.audit_engine import audit_engine

logger = logging.getLogger(__name__)

class GovernanceService:
    """
    Centralized Trust, Safety & Clinical Governance Platform (TSGP).
    Evaluates every request before execution.
    """
    
    def evaluate_request(self, db: Session, user_id: int, request_text: str, intent: str, role: str = "user") -> Dict[str, Any]:
        logger.info(f"[TSGP] Evaluating request: {intent}")
        
        # 1. Calculate Risk
        risk_score = risk_engine.calculate_risk(request_text, intent)
        
        # 2. Emergency Escalation
        if risk_score == "Critical":
            explanation = "I recommended contacting emergency services because your request indicates a critical health situation."
            audit_engine.log_interaction(db, user_id, intent, request_text, risk_score, "escalated", ["EMERGENCY_TRIGGER"], explanation)
            return {
                "action": "escalated",
                "explainability": explanation,
                "message": "Please seek immediate medical attention or call emergency services.",
                "trigger_emergency_agent": True
            }
            
        # 3. Policy Evaluation
        policy_result = policy_engine.evaluate(request_text, intent)
        if not policy_result["safe"]:
            explanation = f"I refused this request because it violates safety policies: {', '.join(policy_result['violations'])}. I cannot provide medical diagnoses or prescriptions."
            audit_engine.log_interaction(db, user_id, intent, request_text, risk_score, "blocked", policy_result["violations"], explanation)
            return {
                "action": "blocked",
                "explainability": explanation,
                "message": policy_result["reason"]
            }
            
        # 4. Success Pipeline
        explanation = "The request passed all safety checks."
        audit_engine.log_interaction(db, user_id, intent, request_text, risk_score, "allowed", [], explanation)
        
        return {
            "action": "allowed",
            "explainability": explanation,
            "risk_score": risk_score
        }

    def evaluate_response(self, response_text: str, evidence_sources: List[str]) -> Dict[str, Any]:
        """Before reaching the user, check for hallucinations."""
        guard_result = hallucination_guard.verify_evidence(response_text, evidence_sources)
        if not guard_result["verified"]:
            return {
                "safe": False,
                "message": guard_result["reason"]
            }
        return {"safe": True, "message": response_text}

governance_service = GovernanceService()
