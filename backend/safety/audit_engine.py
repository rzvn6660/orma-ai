import logging
from sqlalchemy.orm import Session
from models.tsgp import TSGPAuditLog

logger = logging.getLogger(__name__)

class AuditEngine:
    def log_interaction(self, db: Session, user_id: int, intent: str, request_text: str, 
                       risk_score: str, action_taken: str, policies_applied: list, explainability: str) -> TSGPAuditLog:
        
        log = TSGPAuditLog(
            user_id=user_id,
            intent=intent,
            request_text=request_text,
            risk_score=risk_score,
            action_taken=action_taken,
            policies_applied=policies_applied,
            explainability=explainability
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

audit_engine = AuditEngine()
