from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
import datetime

class MedicineReminder(Base):
    __tablename__ = "medicine_reminders"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, index=True)
    dosage = Column(String)
    reminder_time = Column(String) # e.g. "08:00 AM"
    taken_status = Column(Boolean, default=False)
    taken_at = Column(DateTime, nullable=True)
    purpose = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    # Adherence Tracking Fields
    confirmation_method = Column(String, nullable=True) # 'voice', 'manual', 'unverified'
    confidence_score = Column(Integer, default=0) # 0 to 100
    reminder_triggered_at = Column(DateTime, nullable=True)
    confirmation_time_difference = Column(Integer, nullable=True) # Seconds between trigger and confirm
    adherence_pattern_flags = Column(String, nullable=True) # 'suspiciously_fast', 'delayed', etc.
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
