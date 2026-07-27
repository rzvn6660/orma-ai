from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from database import Base
from .identity_mixin import IdentityMixin

class Notification(Base, IdentityMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    caregiver_id = Column(String, index=True)
    elder_id = Column(String, index=True)
    title = Column(String)
    message = Column(String)
    priority = Column(String) # low, medium, high
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
