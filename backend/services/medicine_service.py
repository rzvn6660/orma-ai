from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
from pydantic import BaseModel
from typing import List, Optional
import datetime
from ai.adherence_service import calculate_confidence_score

# Pydantic models for request/response
class ReminderCreate(BaseModel):
    medicine_name: str
    dosage: str
    reminder_time: str
    purpose: Optional[str] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None

class ReminderResponse(BaseModel):
    id: int
    medicine_name: str
    dosage: Optional[str] = None
    reminder_time: str
    purpose: Optional[str] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None
    taken_status: bool
    taken_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

def create_reminder(db: Session, reminder: ReminderCreate):
    db_reminder = MedicineReminder(
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        reminder_time=reminder.reminder_time,
        purpose=reminder.purpose,
        frequency=reminder.frequency,
        notes=reminder.notes,
        taken_status=False
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def get_reminders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MedicineReminder).offset(skip).limit(limit).all()

def mark_taken(db: Session, reminder_id: int):
    db_reminder = db.query(MedicineReminder).filter(MedicineReminder.id == reminder_id).first()
    if db_reminder:
        db_reminder = calculate_confidence_score(db_reminder, "manual")
        db_reminder.taken_status = True
        db_reminder.taken_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def get_latest_pending_medicine(db: Session):
    return db.query(MedicineReminder).filter(MedicineReminder.taken_status == False).first()

def mark_latest_pending_taken(db: Session):
    """
    Finds the most recent pending medicine and marks it as taken.
    Useful for voice confirmation without knowing the exact ID.
    """
    db_reminder = db.query(MedicineReminder).filter(MedicineReminder.taken_status == False).first()
    if db_reminder:
        db_reminder = calculate_confidence_score(db_reminder, "voice")
        db_reminder.taken_status = True
        db_reminder.taken_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_reminder)
    return db_reminder
