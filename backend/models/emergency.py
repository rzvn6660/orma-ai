from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
import uuid
from database import Base
from .identity_mixin import IdentityMixin

class EmergencyAlert(Base, IdentityMixin):
    __tablename__ = "emergency_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    elder_id = Column(String, index=True)
    caregiver_id = Column(String, nullable=True, index=True)
    status = Column(String, default="active", index=True) # active, acknowledged, resolved
    severity = Column(String, default="critical") # critical, high, medium
    alert_source = Column(String, default="Emergency SOS") # Emergency SOS, voice_detected, fall_detected
    message = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
