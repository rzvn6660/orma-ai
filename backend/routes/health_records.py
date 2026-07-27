from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.health_record import HealthRecord
from dependencies import get_current_user, get_current_context

router = APIRouter()

class HealthRecordCreate(BaseModel):
    vital_type: str
    value: str
    unit: str
    measured_by: str
    measurement_type: Optional[str] = None
    notes: Optional[str] = None
    date: str
    time: str

class HealthRecordResponse(HealthRecordCreate):
    id: int
    subject_id: Optional[str] = None
    user_id: Optional[str] = None # Legacy support
    timestamp: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=HealthRecordResponse)
def create_record(record: HealthRecordCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    actor = ctx['authenticated_user']
    subject = ctx['resolved_subject']
    
    db_record = HealthRecord(
        subject_id=subject["id"],
        owned_by=subject["id"],
        actor_id=actor.id,
        created_by=actor.id,
        role=actor.role,
        user_id=subject["id"], # Legacy
        **record.model_dump()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/", response_model=List[HealthRecordResponse])
def get_records(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    # Get all records for subject, ordered by timestamp desc
    records = db.query(HealthRecord).filter(HealthRecord.subject_id == subject["id"]).order_by(HealthRecord.id.desc()).all()
    if not records: # Fallback to user_id for legacy rows
        records = db.query(HealthRecord).filter(HealthRecord.user_id == subject["id"]).order_by(HealthRecord.id.desc()).all()
    return records

@router.delete("/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    db_record = db.query(HealthRecord).filter(HealthRecord.id == record_id).filter(
        (HealthRecord.subject_id == subject["id"]) | (HealthRecord.user_id == subject["id"])
    ).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(db_record)
    db.commit()
    return {"message": "Record deleted"}

@router.put("/{record_id}", response_model=HealthRecordResponse)
def update_record(record_id: int, record: HealthRecordCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    db_record = db.query(HealthRecord).filter(HealthRecord.id == record_id).filter(
        (HealthRecord.subject_id == subject["id"]) | (HealthRecord.user_id == subject["id"])
    ).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    for key, value in record.model_dump().items():
        setattr(db_record, key, value)
        
    db.commit()
    db.refresh(db_record)
    return db_record
