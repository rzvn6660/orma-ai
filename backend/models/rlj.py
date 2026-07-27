import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from database import Base
from .identity_mixin import IdentityMixin

class JournalEntry(Base, IdentityMixin):
    """
    Stores Daily, Weekly, and Monthly reflections.
    """
    __tablename__ = "rlj_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    entry_type = Column(String(50)) # daily, weekly, monthly
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    content = Column(Text) # The generated factual summary
    sources_used = Column(JSON) # Array of data sources used to generate this (Explainability)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LifeEvent(Base, IdentityMixin):
    """
    Chronological timeline of significant life events.
    """
    __tablename__ = "rlj_life_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    event_type = Column(String(50)) # appointment, vaccination, memory, milestone
    title = Column(String(255))
    description = Column(Text)
    event_date = Column(DateTime)
    
    source = Column(String(100)) # What module created this event
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CaregiverSummary(Base, IdentityMixin):
    """
    Concise, factual summaries suitable for authorized caregivers.
    Never exposes private memories.
    """
    __tablename__ = "rlj_caregiver_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    summary_type = Column(String(50)) # daily, weekly
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    content = Column(Text)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
