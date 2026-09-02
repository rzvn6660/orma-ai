import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.tsgp import TSGPAuditLog, PolicyConfiguration
from models.user import User
from dependencies import get_current_user
from safety.governance_service import governance_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tsgp", tags=["Trust, Safety & Clinical Governance"])

@router.get("/audit")
def get_safety_audits(limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Safety Audit Logs for authenticated user."""
    return db.query(TSGPAuditLog).order_by(TSGPAuditLog.created_at.desc()).limit(limit).all()

@router.post("/evaluate-request")
def evaluate_request(request_text: str, intent: str, role: str = "user", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Simulates hitting the TSGP middleware before an action executes."""
    result = governance_service.evaluate_request(db, current_user.id, request_text, intent, role or current_user.role)
    return result

@router.post("/evaluate-response")
def evaluate_response(response_text: str, has_evidence: bool = True, current_user: User = Depends(get_current_user)):
    """Simulates Hallucination Guard."""
    evidence = ["Simulated Source"] if has_evidence else []
    result = governance_service.evaluate_response(response_text, evidence)
    return result
