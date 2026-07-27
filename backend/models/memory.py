from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base
from .identity_mixin import IdentityMixin

class MemoryEvent(Base, IdentityMixin):
    __tablename__ = "memory_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Legacy/Compatibility
    visibility = Column(String, default="private") # 'private' or 'shared'
    
    event_type = Column(String, index=True) # e.g. "medicine", "appointment", "general"
    content = Column(String)
