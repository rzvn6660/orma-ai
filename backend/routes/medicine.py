from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from database import get_db
from services import medicine_service
from services import scheduler_service
from ai.ocr_service import extract_text_from_image
from ai.medicine_parser import parse_medicine_text
from dependencies import get_current_user, get_elderly_user, get_current_context
from models.user import User, CaregiverRelationship
from services.websocket_manager import manager

router = APIRouter()

@router.post("/", response_model=medicine_service.ReminderResponse)
def create_reminder(reminder: medicine_service.ReminderCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Add a new medicine reminder (Supports Elder or Caregiver acting on behalf of Elder).
    """
    # Authorization handled by PermissionManager in context if needed
    # (Future iteration: check ctx['permissions'] for 'add_medicine')
    
    actor = ctx['authenticated_user']
    subject = ctx['resolved_subject']
    
    return medicine_service.create_reminder(
        db=db, 
        reminder=reminder, 
        actor_id=actor.id, 
        subject_id=subject["id"],
        role=actor.role
    )

@router.get("/pending-reminders")
def get_pending_reminders():
    """
    Get active reminders that have just triggered and clear the queue.
    """
    return scheduler_service.get_and_clear_pending_reminders()

@router.get("/", response_model=List[medicine_service.ReminderResponse])
def read_reminders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Retrieve medicine reminders for the active subject.
    """
    subject = ctx['resolved_subject']
    # Subject could be the caregiver themselves (if they manage their own health) or an elderly they manage.
    # We fetch specifically for the resolved subject. The ContextResolver already verified they have permission.
    return medicine_service.get_reminders_for_users(db, [subject["id"]], skip=skip, limit=limit)

@router.put("/{id}/taken", response_model=medicine_service.ReminderResponse)
async def take_medicine(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Mark a medicine reminder as taken.
    """
    subject = ctx['resolved_subject']
    # ensure it belongs to the subject
    reminder = medicine_service.mark_taken(db, reminder_id=id, subject_id=subject["id"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    # Notify caregivers
    # Notify caregivers if subject is elder
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "medicine_taken",
            "medicine_id": reminder.id,
            "medicine_name": reminder.medicine_name,
            "message": f"Medicine {reminder.medicine_name} was marked as taken."
        }, rel.caregiver_id)
        
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
        
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "medicine_missed",
            "medicine_id": reminder.id,
            "medicine_name": reminder.medicine_name,
            "message": f"Medicine {reminder.medicine_name} was missed."
        }, rel.caregiver_id)
        
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
        
    # Notify caregivers
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "medicine_updated",
            "medicine_id": id,
            "message": f"A medicine reminder was updated."
        }, rel.caregiver_id)
        
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
        
    # Notify caregivers
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "medicine_deleted",
            "medicine_id": id,
            "message": "A medicine reminder was deleted."
        }, rel.caregiver_id)
        
    return {"status": "success", "message": "Medicine deleted"}
@router.post("/parse-voice")
async def parse_voice_medicine(text: str = Form(...)):
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
async def parse_ocr_medicine(file: UploadFile = File(...)):
    """
    Extracts text via OCR and parses medicine details for human verification.
    """
    UPLOAD_DIR = "temp_uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        raw_text = extract_text_from_image(file_path)
        if not raw_text:
            return {"status": "error", "message": "Could not read text from image."}
            
        parsed = await parse_medicine_text(raw_text)
        return {"status": "success", "data": parsed, "raw_text": raw_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
