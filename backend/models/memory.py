from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    event_type = Column(String, index=True) # e.g. "medicine", "appointment", "general"
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
