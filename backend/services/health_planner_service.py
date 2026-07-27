from sqlalchemy.orm import Session
from models.health_event import HealthEvent, HealthEventType
from pydantic import BaseModel
from typing import List, Optional
import datetime
from ai.adherence_service import calculate_confidence_score

class HealthEventCreate(BaseModel):
    event_type: HealthEventType = HealthEventType.MEDICINE
    title: str
    description: Optional[str] = None
    reminder_time: str
    event_date: Optional[str] = None
    notes: Optional[str] = None
    timezone: str = "UTC"
    priority: str = "normal"
    location: Optional[str] = None
    contact_number: Optional[str] = None
    reminder_timing_preference: Optional[str] = None
    purpose: Optional[str] = None
    frequency: Optional[str] = None

class HealthEventResponse(BaseModel):
    id: int
    event_type: HealthEventType
    title: str
    description: Optional[str] = None
    reminder_time: str
    event_date: Optional[str] = None
    status: bool
    completed_at: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    timezone: str = "UTC"
    priority: str
    location: Optional[str] = None
    contact_number: Optional[str] = None
    reminder_timing_preference: Optional[str] = None
    purpose: Optional[str] = None
    frequency: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

def create_health_event(db: Session, event: HealthEventCreate, actor_id: str, subject_id: str, role: str):
    db_event = HealthEvent(
        subject_id=subject_id,
        owned_by=subject_id,
        actor_id=actor_id,
        created_by=actor_id,
        role=role,
        elder_id=subject_id, # Keep for legacy compatibility
        event_type=event.event_type.value,
        title=event.title,
        description=event.description,
        reminder_time=event.reminder_time,
        event_date=event.event_date,
        notes=event.notes,
        timezone=event.timezone,
        priority=event.priority,
        location=event.location,
        contact_number=event.contact_number,
        reminder_timing_preference=event.reminder_timing_preference,
        purpose=event.purpose,
        frequency=event.frequency,
        status=False
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_events_for_users(db: Session, subject_ids: list[str], skip: int = 0, limit: int = 100):
    return db.query(HealthEvent).filter(HealthEvent.subject_id.in_(subject_ids)).offset(skip).limit(limit).all()

def mark_event_completed(db: Session, event_id: int, subject_id: str):
    db_event = db.query(HealthEvent).filter(HealthEvent.id == event_id, HealthEvent.subject_id == subject_id).first()
    if db_event:
        db_event.status = True
        db_event.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int, subject_id: str):
    db_event = db.query(HealthEvent).filter(HealthEvent.id == event_id, HealthEvent.subject_id == subject_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
        return True
    return False

def get_all_pending_events(db: Session):
    return db.query(HealthEvent).filter(HealthEvent.status == False).all()
