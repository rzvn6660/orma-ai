import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models.rlj import JournalEntry, LifeEvent, CaregiverSummary
from models.user import User, CaregiverRelationship
from dependencies import get_current_user
from rlj.reflection_engine import reflection_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rlj", tags=["Reflection & Life Journal Engine"])

def _verify_user_access(current_user: User, target_user_id: str, db: Session):
    target_str = str(target_user_id)
    if str(current_user.id) == target_str:
        return True
    if current_user.role == "caregiver":
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.elder_id == target_str,
            CaregiverRelationship.status == "approved"
        ).first()
        if rel:
            return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. You are not authorized to access this user's journal records."
    )

@router.get("/journal/{user_id}")
def get_journal_entries(user_id: str, entry_type: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves reflection journal entries (daily, weekly, monthly)."""
    _verify_user_access(current_user, user_id, db)
    query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)
    if entry_type:
        query = query.filter(JournalEntry.entry_type == entry_type)
    return query.order_by(JournalEntry.date.desc()).all()

@router.get("/timeline/{user_id}")
def get_life_timeline(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves chronological life timeline."""
    _verify_user_access(current_user, user_id, db)
    return db.query(LifeEvent).filter(LifeEvent.user_id == user_id).order_by(LifeEvent.event_date.desc()).all()

@router.get("/caregiver-summary/{user_id}")
def get_caregiver_summaries(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves concise, factual health summaries for caregivers (private memories excluded)."""
    _verify_user_access(current_user, user_id, db)
    return db.query(CaregiverSummary).filter(CaregiverSummary.user_id == user_id).order_by(CaregiverSummary.date.desc()).all()

@router.post("/generate/{user_id}")
def trigger_generation(user_id: str, reflection_type: str = "daily", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Triggers generation for the authenticated user or linked elder."""
    _verify_user_access(current_user, user_id, db)
    if reflection_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid reflection type")
        
    entry = reflection_engine.generate_reflection(db, user_id, reflection_type)
    return {"status": "success", "message": f"{reflection_type.capitalize()} reflection generated."}

@router.post("/timeline/{user_id}/mock-event")
def trigger_mock_event(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a mock life event for testing in non-production environments."""
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(status_code=404, detail="Test endpoints are disabled in production.")
    _verify_user_access(current_user, user_id, db)
    event = reflection_engine.add_life_event(
        db, user_id, 
        event_type="milestone", 
        title="Completed Heart Health Challenge", 
        description="Successfully logged blood pressure for 30 consecutive days.", 
        event_date=datetime.utcnow(), 
        source="Health Planner"
    )
    return {"status": "success", "event_id": event.id}
