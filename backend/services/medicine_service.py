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
    timezone: str = "UTC"

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
    timezone: str = "UTC"
    adherence_pattern_flags: Optional[str] = None
    confirmation_method: Optional[str] = None

    class Config:
        from_attributes = True

def create_reminder(db: Session, reminder: ReminderCreate, actor_id: str, subject_id: str, role: str):
    db_reminder = MedicineReminder(
        subject_id=subject_id,
        owned_by=subject_id,
        actor_id=actor_id,
        created_by=actor_id,
        role=role,
        elder_id=subject_id, # Keep for legacy compatibility
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        reminder_time=reminder.reminder_time,
        purpose=reminder.purpose,
        frequency=reminder.frequency,
        notes=reminder.notes,
        timezone=reminder.timezone,
        taken_status=False
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def get_reminders_for_users(db: Session, subject_ids: list[str], skip: int = 0, limit: int = 100):
    return db.query(MedicineReminder).filter(
        (MedicineReminder.subject_id.in_(subject_ids)) | (MedicineReminder.elder_id.in_(subject_ids))
    ).offset(skip).limit(limit).all()

def mark_taken(db: Session, reminder_id: int, subject_id: str):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        db_reminder = calculate_confidence_score(db_reminder, "manual")
        db_reminder.taken_status = True
        db_reminder.taken_at = datetime.datetime.utcnow()
        db_reminder.adherence_pattern_flags = None # Clear missed status if taken
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def mark_missed(db: Session, reminder_id: int, subject_id: str):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        db_reminder.adherence_pattern_flags = "missed"
        db_reminder.confirmation_method = "unverified"
        db_reminder.taken_status = False
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def mark_skipped(db: Session, reminder_id: int, subject_id: str):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        db_reminder.adherence_pattern_flags = "skipped"
        db_reminder.confirmation_method = "manual"
        db_reminder.taken_status = False
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def snooze_reminder(db: Session, reminder_id: int, subject_id: str, minutes: int = 10):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        db_reminder.adherence_pattern_flags = "snoozed"
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def update_reminder(db: Session, reminder_id: int, subject_id: str, updates: dict):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        for key, value in updates.items():
            if hasattr(db_reminder, key):
                setattr(db_reminder, key, value)
        db.commit()
        db.refresh(db_reminder)
    return db_reminder

def get_latest_pending_medicine(db: Session):
    return db.query(MedicineReminder).filter(MedicineReminder.taken_status == False).first()

def get_all_pending_medicines(db: Session):
    # For today only optimally, but just getting all pending for now
    return db.query(MedicineReminder).filter(MedicineReminder.taken_status == False).all()

def get_all_taken_medicines(db: Session):
    # Today's taken medicines
    today = datetime.datetime.utcnow().date()
    # If taken_at is set, it's taken
    return db.query(MedicineReminder).filter(MedicineReminder.taken_status == True).all()

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

def delete_reminder(db: Session, reminder_id: int, subject_id: str):
    db_reminder = db.query(MedicineReminder).filter(
        MedicineReminder.id == reminder_id, 
        (MedicineReminder.subject_id == subject_id) | (MedicineReminder.elder_id == subject_id)
    ).first()
    if db_reminder:
        db.delete(db_reminder)
        db.commit()
        return True
    return False
