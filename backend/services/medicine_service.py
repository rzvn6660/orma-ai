from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
from pydantic import BaseModel
from typing import List, Optional
import datetime
import pytz
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

def resolve_medication_daily_status(
    reminder: MedicineReminder,
    target_date: Optional[datetime.date] = None,
    tz_name: Optional[str] = None
) -> bool:
    """
    Determines whether a medication is taken for a specific calendar date (defaults to today in user timezone).
    Recurring medications marked taken on an earlier day roll over to PENDING (False) for today's occurrence,
    while their historical taken_at timestamp is preserved.
    """
    if not getattr(reminder, "taken_status", False):
        return False

    taken_at = getattr(reminder, "taken_at", None)
    if not taken_at:
        return bool(reminder.taken_status)

    tz_str = tz_name or getattr(reminder, "timezone", "UTC") or "UTC"
    try:
        user_tz = pytz.timezone(tz_str)
    except Exception:
        user_tz = pytz.utc

    # Normalize taken_at to local date
    if taken_at.tzinfo is None:
        taken_at_utc = pytz.utc.localize(taken_at)
    else:
        taken_at_utc = taken_at.astimezone(pytz.utc)
    taken_local_date = taken_at_utc.astimezone(user_tz).date()

    if target_date is None:
        target_date = datetime.datetime.now(user_tz).date()

    freq = (getattr(reminder, "frequency", "") or "").strip().lower()
    if freq in ("one-time", "once", "single"):
        return True

    # For recurring medications, taken status only applies if taken on the target date
    return taken_local_date == target_date

def get_reminders_for_users(db: Session, subject_ids: list[str], skip: int = 0, limit: int = 100):
    reminders = db.query(MedicineReminder).filter(
        (MedicineReminder.subject_id.in_(subject_ids)) | (MedicineReminder.elder_id.in_(subject_ids))
    ).offset(skip).limit(limit).all()

    results = []
    for r in reminders:
        effective_taken = resolve_medication_daily_status(r)
        results.append(ReminderResponse(
            id=r.id,
            medicine_name=r.medicine_name,
            dosage=r.dosage,
            reminder_time=r.reminder_time,
            purpose=r.purpose,
            frequency=r.frequency,
            notes=r.notes,
            taken_status=effective_taken,
            taken_at=r.taken_at,
            created_at=r.created_at,
            timezone=r.timezone or "UTC",
            adherence_pattern_flags=r.adherence_pattern_flags,
            confirmation_method=r.confirmation_method,
        ))
    return results

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
        db_reminder.is_caregiver_notified = False
        db_reminder.caregiver_notified_at = None
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

def get_latest_pending_medicine(db: Session, user_id: Optional[str] = None):
    query = db.query(MedicineReminder)
    if user_id:
        query = query.filter((MedicineReminder.subject_id == user_id) | (MedicineReminder.elder_id == user_id))
    all_meds = query.all()
    for m in all_meds:
        if not resolve_medication_daily_status(m):
            return m
    return None

def get_all_pending_medicines(db: Session, user_id: Optional[str] = None):
    query = db.query(MedicineReminder)
    if user_id:
        query = query.filter((MedicineReminder.subject_id == user_id) | (MedicineReminder.elder_id == user_id))
    all_meds = query.all()
    return [m for m in all_meds if not resolve_medication_daily_status(m)]

def get_all_taken_medicines(db: Session, user_id: Optional[str] = None):
    query = db.query(MedicineReminder)
    if user_id:
        query = query.filter((MedicineReminder.subject_id == user_id) | (MedicineReminder.elder_id == user_id))
    all_meds = query.all()
    return [m for m in all_meds if resolve_medication_daily_status(m)]

def mark_latest_pending_taken(db: Session, user_id: Optional[str] = None):
    """
    Finds the most recent pending medicine for today and marks it as taken.
    Useful for voice confirmation without knowing the exact ID.
    """
    db_reminder = get_latest_pending_medicine(db, user_id=user_id)
    if db_reminder:
        db_reminder = calculate_confidence_score(db_reminder, "voice")
        db_reminder.taken_status = True
        db_reminder.taken_at = datetime.datetime.utcnow()
        db_reminder.adherence_pattern_flags = None
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
