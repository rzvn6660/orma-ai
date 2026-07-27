import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON
from database import Base
from .identity_mixin import IdentityMixin

class BehaviourProfile(Base, IdentityMixin):
    """
    Stores accepted behavioural preferences.
    Separate from long-term memory.
    """
    __tablename__ = "ale_behaviour_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, unique=True)
    
    preferred_language = Column(String(50), default="en")
    speaking_speed = Column(String(50), default="normal")
    conversation_style = Column(String(50), default="standard")
    reminder_behaviour = Column(String(50), default="standard")
    preferred_reminder_times = Column(JSON, default=dict)
    wake_time = Column(String(50), default="07:00")
    sleep_time = Column(String(50), default="22:00")
    preferred_contact_method = Column(String(50), default="voice")
    accessibility_preferences = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class LearningCandidate(Base, IdentityMixin):
    """
    Stores patterns detected that require user confirmation.
    """
    __tablename__ = "ale_learning_candidates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    pattern_type = Column(String(100)) # e.g., 'medicine_delay', 'language_preference'
    suggestion_text = Column(String(255))
    proposed_changes = Column(JSON) # e.g., {"preferred_language": "ml"}
    
    evidence = Column(String(512))
    confidence = Column(Float, default=0.0)
    last_observed = Column(DateTime, default=datetime.datetime.utcnow)
    
    status = Column(String(50), default="pending") # pending, accepted, rejected, postponed, never
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
