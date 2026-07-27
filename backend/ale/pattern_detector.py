import logging
from sqlalchemy.orm import Session
from datetime import datetime
from models.ale import LearningCandidate, BehaviourProfile
import json

logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Observes interactions and detects behavioural patterns.
    Generates LearningCandidates when confidence is high.
    Never applies changes automatically.
    """
    
    def observe_interaction(self, db: Session, user_id: int, interaction_type: str, data: dict):
        """
        Log an observation. In a full system, this would write to an observations table.
        For this sprint, we'll simulate pattern detection based on the single event or memory state.
        
        interaction_type examples: 'reminder_completed', 'language_used', 'speech_speed_request'
        """
        logger.info(f"[ALE] Observation logged for user {user_id}: {interaction_type} | {data}")
        
        # Example 1: Medicine Delay Pattern
        if interaction_type == "reminder_completed":
            scheduled = data.get("scheduled_time")
            completed = data.get("completed_time")
            # If logic determines they are consistently late, we create a candidate.
            # Simulated check: if they were late by more than 30 mins, we assume it's a pattern for the sprint demo.
            if scheduled and completed:
                try:
                    # Simple mock time diff
                    diff_minutes = 40 # Mocking a 40 min delay pattern
                    if diff_minutes >= 30:
                        self._propose_candidate(
                            db, user_id, 
                            pattern_type="medicine_delay",
                            suggestion_text=f"I've noticed you usually take your morning medicine around 40 minutes late. Would you like me to remind you at a later time?",
                            proposed_changes={"preferred_reminder_times": {"morning": "shifted_by_40m"}},
                            evidence=f"User took morning medicine {diff_minutes} minutes late 5 times this week.",
                            confidence=0.85
                        )
                except Exception as e:
                    logger.error(f"[ALE] Error parsing time: {e}")

        # Example 2: Language Usage Pattern
        elif interaction_type == "language_used":
            lang = data.get("language")
            if lang == "ml":
                self._propose_candidate(
                    db, user_id,
                    pattern_type="language_preference",
                    suggestion_text="I've noticed you often speak in Malayalam. Would you like me to always reply in Malayalam?",
                    proposed_changes={"preferred_language": "ml"},
                    evidence="User initiated conversation in Malayalam 4 times today.",
                    confidence=0.90
                )
                
        # Example 3: Conversation Style
        elif interaction_type == "conversation_style":
            style = data.get("style")
            if style == "short":
                self._propose_candidate(
                    db, user_id,
                    pattern_type="conversation_style",
                    suggestion_text="I've noticed you prefer short answers. Would you like me to keep my responses brief?",
                    proposed_changes={"conversation_style": "short"},
                    evidence="User's average response length is under 5 words.",
                    confidence=0.80
                )

    def _propose_candidate(self, db: Session, user_id: int, pattern_type: str, suggestion_text: str, proposed_changes: dict, evidence: str, confidence: float):
        """
        Creates a Learning Candidate if confidence is high and it hasn't been rejected before.
        """
        # Check if already exists and is pending or rejected
        existing = db.query(LearningCandidate).filter(
            LearningCandidate.user_id == user_id, 
            LearningCandidate.pattern_type == pattern_type,
            LearningCandidate.status.in_(["pending", "rejected", "never"])
        ).first()
        
        if existing:
            if existing.status in ["rejected", "never"]:
                logger.info(f"[ALE] Candidate for '{pattern_type}' was previously rejected. Ignoring.")
                return
            
            # If pending, just update confidence and last observed
            existing.confidence = min(1.0, existing.confidence + 0.05)
            existing.last_observed = datetime.utcnow()
            db.commit()
            logger.info(f"[ALE] Updated existing candidate for '{pattern_type}'. Confidence: {existing.confidence}")
            return
            
        if confidence >= 0.75:
            new_candidate = LearningCandidate(
                user_id=user_id,
                pattern_type=pattern_type,
                suggestion_text=suggestion_text,
                proposed_changes=proposed_changes,
                evidence=evidence,
                confidence=confidence,
                status="pending"
            )
            db.add(new_candidate)
            db.commit()
            logger.info(f"[ALE] Generated new Learning Candidate: {pattern_type}")

pattern_detector = PatternDetector()
