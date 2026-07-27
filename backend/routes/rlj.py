import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models.rlj import JournalEntry, LifeEvent, CaregiverSummary
from rlj.reflection_engine import reflection_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rlj", tags=["Reflection & Life Journal Engine"])

@router.get("/journal/{user_id}")
def get_journal_entries(user_id: int, entry_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieves reflection journal entries (daily, weekly, monthly)."""
    query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)
    if entry_type:
        query = query.filter(JournalEntry.entry_type == entry_type)
    return query.order_by(JournalEntry.date.desc()).all()

@router.get("/timeline/{user_id}")
def get_life_timeline(user_id: int, db: Session = Depends(get_db)):
    """Retrieves chronological life timeline."""
    return db.query(LifeEvent).filter(LifeEvent.user_id == user_id).order_by(LifeEvent.event_date.desc()).all()

@router.get("/caregiver-summary/{user_id}")
def get_caregiver_summaries(user_id: int, db: Session = Depends(get_db)):
    """Retrieves concise, factual health summaries for caregivers (private memories excluded)."""
    return db.query(CaregiverSummary).filter(CaregiverSummary.user_id == user_id).order_by(CaregiverSummary.date.desc()).all()

@router.post("/generate/{user_id}")
def trigger_generation(user_id: int, reflection_type: str = "daily", db: Session = Depends(get_db)):
    """Manually triggers generation (for testing/demo)."""
    if reflection_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid reflection type")
        
    entry = reflection_engine.generate_reflection(db, user_id, reflection_type)
    return {"status": "success", "message": f"{reflection_type.capitalize()} reflection generated."}

@router.post("/timeline/{user_id}/mock-event")
def trigger_mock_event(user_id: int, db: Session = Depends(get_db)):
    """Creates a mock life event for testing/demo."""
    event = reflection_engine.add_life_event(
        db, user_id, 
        event_type="milestone", 
        title="Completed Heart Health Challenge", 
        description="Successfully logged blood pressure for 30 consecutive days.", 
        event_date=datetime.utcnow(), 
        source="Health Planner"
    )
    return {"status": "success", "event_id": event.id}
