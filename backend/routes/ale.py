import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.ale import BehaviourProfile, LearningCandidate
from models.user import User, CaregiverRelationship
from dependencies import get_current_user
from ale.candidate_manager import candidate_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ale", tags=["Adaptive Learning Engine"])

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
        detail="Access denied. You are not authorized to access this user's learning profile."
    )

@router.get("/profile/{user_id}")
def get_behaviour_profile(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves the user's active behaviour profile."""
    _verify_user_access(current_user, user_id, db)
    profile = db.query(BehaviourProfile).filter(BehaviourProfile.user_id == user_id).first()
    if not profile:
        profile = BehaviourProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/profile/{user_id}")
def update_behaviour_profile(user_id: str, updates: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Manually edit or remove learned preferences."""
    _verify_user_access(current_user, user_id, db)
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
def get_learning_candidates(user_id: str, status_filter: Optional[str] = "pending", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves learning candidates."""
    _verify_user_access(current_user, user_id, db)
    query = db.query(LearningCandidate).filter(LearningCandidate.user_id == user_id)
    if status_filter:
        query = query.filter(LearningCandidate.status == status_filter)
        
    return query.all()

@router.post("/candidates/{candidate_id}/resolve")
def resolve_candidate(candidate_id: int, resolution: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Accept, decline, postpone, or never suggest again.
    Expects JSON: {"resolution": "accepted"}
    """
    action = resolution.get("resolution")
    if action not in ["accepted", "rejected", "postponed", "never"]:
        raise HTTPException(status_code=400, detail="Invalid resolution action")
        
    cand = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Learning candidate not found")

    _verify_user_access(current_user, str(cand.user_id), db)
    result = candidate_manager.resolve_candidate(db, candidate_id, cand.user_id, action)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
        
    return result

@router.post("/test-generate")
def test_generate_candidate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Developer testing endpoint — restricted to non-production environments."""
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(status_code=404, detail="Test endpoints are disabled in production.")
    from ale.pattern_detector import pattern_detector
    pattern_detector.observe_interaction(db, current_user.id, "language_used", {"language": "ml"})
    pattern_detector.observe_interaction(db, current_user.id, "reminder_completed", {"scheduled_time": "08:00", "completed_time": "08:40"})
    return {"status": "success", "message": "Simulated pattern detection."}
