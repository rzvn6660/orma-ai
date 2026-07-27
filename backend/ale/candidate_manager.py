import logging
from sqlalchemy.orm import Session
from models.ale import LearningCandidate, BehaviourProfile
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CandidateManager:
    """
    Manages user responses to Learning Candidates.
    Applies accepted changes to the BehaviourProfile.
    """
    
    def resolve_candidate(self, db: Session, candidate_id: int, user_id: int, resolution: str) -> Dict[str, Any]:
        """
        resolution must be one of: 'accepted', 'rejected', 'postponed', 'never'
        """
        candidate = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id, LearningCandidate.user_id == user_id).first()
        if not candidate:
            return {"status": "error", "message": "Candidate not found."}
            
        logger.info(f"[ALE] User resolved candidate {candidate_id} with: {resolution}")
        
        candidate.status = resolution
        
        if resolution == "accepted":
            self._apply_behaviour_changes(db, user_id, candidate.proposed_changes)
            logger.info(f"[ALE] Candidate {candidate_id} changes applied to profile.")
            
        db.commit()
        return {"status": "success", "resolution": resolution}
        
    def _apply_behaviour_changes(self, db: Session, user_id: int, changes: dict):
        profile = db.query(BehaviourProfile).filter(BehaviourProfile.user_id == user_id).first()
        if not profile:
            profile = BehaviourProfile(user_id=user_id)
            db.add(profile)
            
        for key, value in changes.items():
            if hasattr(profile, key):
                # Handle JSON merges if necessary, but simple assignment for now
                setattr(profile, key, value)
                
candidate_manager = CandidateManager()
