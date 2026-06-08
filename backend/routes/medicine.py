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

router = APIRouter()

@router.post("/", response_model=medicine_service.ReminderResponse)
def create_reminder(reminder: medicine_service.ReminderCreate, db: Session = Depends(get_db)):
    """
    Add a new medicine reminder.
    """
    return medicine_service.create_reminder(db=db, reminder=reminder)

@router.get("/pending-reminders")
def get_pending_reminders():
    """
    Get active reminders that have just triggered and clear the queue.
    """
    return scheduler_service.get_and_clear_pending_reminders()

@router.get("/", response_model=List[medicine_service.ReminderResponse])
def read_reminders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all medicine reminders.
    """
    return medicine_service.get_reminders(db, skip=skip, limit=limit)

@router.put("/{id}/taken", response_model=medicine_service.ReminderResponse)
def take_medicine(id: int, db: Session = Depends(get_db)):
    """
    Mark a medicine reminder as taken.
    """
    reminder = medicine_service.mark_taken(db, reminder_id=id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

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
