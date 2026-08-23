from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from database import Base
import datetime
import enum

class HealthEventType(str, enum.Enum):
    MEDICINE = "medicine"
    DOCTOR_APPOINTMENT = "doctor_appointment"
    BLOOD_TEST = "blood_test"
    VACCINATION = "vaccination"
    BLOOD_PRESSURE_CHECK = "blood_pressure_check"
    BLOOD_SUGAR_CHECK = "blood_sugar_check"
    EXERCISE = "exercise"
    WATER_REMINDER = "water_reminder"
    SLEEP_REMINDER = "sleep_reminder"
    CUSTOM_REMINDER = "custom_reminder"

from .identity_mixin import IdentityMixin

class HealthEvent(Base, IdentityMixin):
    __tablename__ = "health_events"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(String, index=True, nullable=True)
    event_type = Column(String, default=HealthEventType.MEDICINE.value)
    
    # Common Fields (used to be medicine_name, dosage, etc.)
    title = Column(String, index=True) # E.g., medicine name, doctor name, test name
    description = Column(String, nullable=True) # dosage, specialty, etc.
    reminder_time = Column(String) # e.g. "08:00 AM"
    event_date = Column(String, nullable=True) # e.g. "2024-05-20", optional for daily events
    status = Column(Boolean, default=False) # completed / taken
    completed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    
    # Priority
    priority = Column(String, default="normal") # high, normal, low
    
    # Doctor Appointment specific fields
    location = Column(String, nullable=True) # Hospital/Clinic/Address
    contact_number = Column(String, nullable=True)
    reminder_timing_preference = Column(String, nullable=True) # "1 day before", "1 hour before"

    # Legacy / specific medicine fields (mapped for compatibility)
    purpose = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    
    # Adherence / Reminder Tracking
    confirmation_method = Column(String, nullable=True)
    confidence_score = Column(Integer, default=0)
    reminder_triggered_at = Column(DateTime, nullable=True)
    confirmation_time_difference = Column(Integer, nullable=True)
    adherence_pattern_flags = Column(String, nullable=True)
    is_caregiver_notified = Column(Boolean, default=False)
    caregiver_notified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
