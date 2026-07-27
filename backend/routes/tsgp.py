import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.tsgp import TSGPAuditLog, PolicyConfiguration
from safety.governance_service import governance_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tsgp", tags=["Trust, Safety & Clinical Governance"])

@router.get("/audit")
def get_safety_audits(limit: int = 50, db: Session = Depends(get_db)):
    """Developer Tools: Internal Safety Dashboard"""
    return db.query(TSGPAuditLog).order_by(TSGPAuditLog.created_at.desc()).limit(limit).all()

@router.post("/evaluate-request")
def evaluate_request(request_text: str, intent: str, user_id: int = 1, role: str = "user", db: Session = Depends(get_db)):
    """Simulates hitting the TSGP middleware before an action executes."""
    result = governance_service.evaluate_request(db, user_id, request_text, intent, role)
    return result

@router.post("/evaluate-response")
def evaluate_response(response_text: str, has_evidence: bool = True):
    """Simulates Hallucination Guard."""
    evidence = ["Simulated Source"] if has_evidence else []
    result = governance_service.evaluate_response(response_text, evidence)
    return result
