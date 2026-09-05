from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from database import get_db
from services import medicine_service
from services import scheduler_service
from ai.ocr_service import extract_text_from_image
from ai.medicine_parser import parse_medicine_text
from dependencies import get_current_user, get_elderly_user, get_current_context
from models.user import User, CaregiverRelationship
from services.websocket_manager import manager

router = APIRouter()

class SnoozePayload(BaseModel):
    minutes: Optional[int] = 10

async def broadcast_medicine_event(db: Session, subject_id: str, event_data: dict):
    """
    Broadcasts real-time medicine updates to both the elder (subject) and all linked caregivers.
    """
    try:
        # 1. Send to the subject (elder)
        await manager.send_personal_message(event_data, subject_id)
        
        # 2. Send to all linked approved caregivers
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.elder_id == subject_id, 
            CaregiverRelationship.status == "approved"
        ).all()
        for rel in rels:
            await manager.send_personal_message(event_data, rel.caregiver_id)
    except Exception as e:
        print(f"[WS BROADCAST WARN] Failed to broadcast medicine event: {e}")

@router.post("/", response_model=medicine_service.ReminderResponse)
async def create_reminder(reminder: medicine_service.ReminderCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Add a new medicine reminder (Supports Elder or Caregiver acting on behalf of Elder).
    """
    actor = ctx['authenticated_user']
    subject = ctx['resolved_subject']
    
    new_reminder = medicine_service.create_reminder(
        db=db, 
        reminder=reminder, 
        actor_id=actor.id, 
        subject_id=subject["id"],
        role=actor.role
    )

    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_created",
        "medicine_id": new_reminder.id,
        "medicine_name": new_reminder.medicine_name,
        "reminder_time": new_reminder.reminder_time,
        "message": f"New medicine {new_reminder.medicine_name} scheduled for {new_reminder.reminder_time}."
    })
    
    return new_reminder

@router.get("/pending-reminders")
def get_pending_reminders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get active reminders that have just triggered for the authenticated user, enforcing recipient preferences & relationships.
    """
    from services.notification_preference_service import get_user_notification_preferences
    prefs = get_user_notification_preferences(db, current_user)
    
    if not prefs.medication_reminder_notifications:
        return []
        
    reminders = scheduler_service.get_and_clear_pending_reminders()
    if not reminders:
        return []
        
    if current_user.role == 'elderly':
        return [r for r in reminders if r.get('elder_id') == current_user.id or r.get('subject_id') == current_user.id]
    elif current_user.role == 'caregiver':
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.status == "approved"
        ).all()
        approved_elder_ids = set(r.elder_id for r in rels)
        return [r for r in reminders if (r.get('elder_id') in approved_elder_ids or r.get('subject_id') in approved_elder_ids)]
        
    return []

@router.get("/", response_model=List[medicine_service.ReminderResponse])
def read_reminders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Retrieve medicine reminders for the active subject.
    """
    subject = ctx['resolved_subject']
    return medicine_service.get_reminders_for_users(db, [subject["id"]], skip=skip, limit=limit)

@router.put("/{id}/taken", response_model=medicine_service.ReminderResponse)
async def take_medicine(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Mark a medicine reminder as taken.
    """
    subject = ctx['resolved_subject']
    reminder = medicine_service.mark_taken(db, reminder_id=id, subject_id=subject["id"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_taken",
        "medicine_id": reminder.id,
        "medicine_name": reminder.medicine_name,
        "message": f"Medicine {reminder.medicine_name} was marked as taken."
    })
        
    return reminder

@router.put("/{id}/missed", response_model=medicine_service.ReminderResponse)
async def miss_medicine(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Mark a medicine reminder as missed.
    """
    subject = ctx['resolved_subject']
    reminder = medicine_service.mark_missed(db, reminder_id=id, subject_id=subject["id"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_missed",
        "medicine_id": reminder.id,
        "medicine_name": reminder.medicine_name,
        "message": f"Medicine {reminder.medicine_name} was missed."
    })

    from services.notification_service import dispatch_notification
    await dispatch_notification(
        db=db,
        elder_id=subject["id"],
        title=f"Missed Medication: {reminder.medicine_name}",
        message=f"Medication {reminder.medicine_name} scheduled for {reminder.reminder_time} was marked as missed.",
        priority="high"
    )
        
    return reminder

@router.put("/{id}/skipped", response_model=medicine_service.ReminderResponse)
async def skip_medicine(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Mark a medicine reminder as skipped.
    """
    subject = ctx['resolved_subject']
    reminder = medicine_service.mark_skipped(db, reminder_id=id, subject_id=subject["id"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_skipped",
        "medicine_id": reminder.id,
        "medicine_name": reminder.medicine_name,
        "message": f"Medicine {reminder.medicine_name} was skipped."
    })
        
    return reminder

@router.put("/{id}/snooze", response_model=medicine_service.ReminderResponse)
async def snooze_medicine(id: int, payload: Optional[SnoozePayload] = None, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Snooze a medicine reminder.
    """
    subject = ctx['resolved_subject']
    minutes = payload.minutes if payload and payload.minutes else 10
    reminder = medicine_service.snooze_reminder(db, reminder_id=id, subject_id=subject["id"], minutes=minutes)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_snoozed",
        "medicine_id": reminder.id,
        "medicine_name": reminder.medicine_name,
        "minutes": minutes,
        "message": f"Medicine {reminder.medicine_name} was snoozed for {minutes} minutes."
    })

    return reminder

@router.put("/{id}", response_model=medicine_service.ReminderResponse)
async def update_medicine(id: int, reminder: medicine_service.ReminderCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Update a medicine reminder.
    """
    subject = ctx['resolved_subject']
    updated_reminder = medicine_service.update_reminder(db, reminder_id=id, subject_id=subject["id"], updates=reminder.dict(exclude_unset=True))
    if not updated_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found or unauthorized")
        
    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_updated",
        "medicine_id": id,
        "medicine_name": updated_reminder.medicine_name,
        "message": f"Medicine {updated_reminder.medicine_name} was updated."
    })
        
    return updated_reminder

@router.delete("/{id}")
async def delete_medicine(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Delete a medicine reminder.
    """
    subject = ctx['resolved_subject']
    success = medicine_service.delete_reminder(db, reminder_id=id, subject_id=subject["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found or unauthorized")
        
    await broadcast_medicine_event(db, subject["id"], {
        "type": "medicine_deleted",
        "medicine_id": id,
        "message": "A medicine reminder was deleted."
    })
        
    return {"status": "success", "message": "Medicine deleted"}
@router.post("/parse-voice")
async def parse_voice_medicine(text: str = Form(...), current_user: User = Depends(get_current_user)):
    """
    Parses medicine details from a transcribed voice intent.
    Returns structured data for the user to verify.
    """
    try:
        parsed = await parse_medicine_text(text)
        return {"status": "success", "data": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-ocr")
async def parse_ocr_medicine(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """
    Extracts text via OCR and parses medicine details for human verification.
    """
    UPLOAD_DIR = "temp_uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    raw_filename = file.filename or "image.jpg"
    ext = os.path.splitext(raw_filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        ext = ".jpg"
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds 20 MB size limit.")
            
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        raw_text = extract_text_from_image(file_path)
        if not raw_text:
            return {"status": "error", "message": "Could not read text from image."}
            
        parsed = await parse_medicine_text(raw_text)
        return {"status": "success", "data": parsed, "raw_text": raw_text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
