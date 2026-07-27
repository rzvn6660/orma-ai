from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base
from .identity_mixin import IdentityMixin

class HealthRecord(Base, IdentityMixin):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # Legacy/compatibility
    source = Column(String, default="Manual") # e.g. Manual, OCR, Voice, Caregiver, Wearable
    
    vital_type = Column(String, index=True)
    
    value = Column(String) 
    unit = Column(String)
    
    measured_by = Column(String) # Legacy field
    measurement_type = Column(String, nullable=True) 
    notes = Column(Text, nullable=True)
    
    date = Column(String) 
    time = Column(String) 
