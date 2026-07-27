import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.ale import BehaviourProfile, LearningCandidate
from ale.candidate_manager import candidate_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ale", tags=["Adaptive Learning Engine"])

@router.get("/profile/{user_id}")
def get_behaviour_profile(user_id: int, db: Session = Depends(get_db)):
    """Retrieves the user's active behaviour profile."""
    profile = db.query(BehaviourProfile).filter(BehaviourProfile.user_id == user_id).first()
    if not profile:
        profile = BehaviourProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/profile/{user_id}")
def update_behaviour_profile(user_id: int, updates: dict, db: Session = Depends(get_db)):
    """Manually edit or remove learned preferences."""
    profile = db.query(BehaviourProfile).filter(BehaviourProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    for k, v in updates.items():
        if hasattr(profile, k) and k not in ["id", "user_id"]:
            setattr(profile, k, v)
            
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/candidates/{user_id}")
def get_learning_candidates(user_id: int, status: Optional[str] = "pending", db: Session = Depends(get_db)):
    """Retrieves learning candidates."""
    query = db.query(LearningCandidate).filter(LearningCandidate.user_id == user_id)
    if status:
        query = query.filter(LearningCandidate.status == status)
        
    return query.all()

@router.post("/candidates/{candidate_id}/resolve")
def resolve_candidate(candidate_id: int, resolution: dict, user_id: int = 1, db: Session = Depends(get_db)):
    """
    Accept, decline, postpone, or never suggest again.
    Expects JSON: {"resolution": "accepted"}
    """
    action = resolution.get("resolution")
    if action not in ["accepted", "rejected", "postponed", "never"]:
        raise HTTPException(status_code=400, detail="Invalid resolution action")
        
    result = candidate_manager.resolve_candidate(db, candidate_id, user_id, action)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
        
    return result

@router.post("/test-generate")
def test_generate_candidate(user_id: int = 1, db: Session = Depends(get_db)):
    """Mock endpoint to test generation."""
    from ale.pattern_detector import pattern_detector
    pattern_detector.observe_interaction(db, user_id, "language_used", {"language": "ml"})
    pattern_detector.observe_interaction(db, user_id, "reminder_completed", {"scheduled_time": "08:00", "completed_time": "08:40"})
    return {"status": "success", "message": "Simulated pattern detection."}
