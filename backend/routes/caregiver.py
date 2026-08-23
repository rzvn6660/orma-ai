from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from services import caregiver_service
from models.user import User, CaregiverRelationship
from dependencies import get_current_context, get_caregiver_user

router = APIRouter()

def get_linked_elder_ids(db: Session, caregiver_id: str):
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.caregiver_id == caregiver_id,
        CaregiverRelationship.status == "approved"
    ).all()
    return [r.elder_id for r in rels]

class CaregiverPhoneUpdate(BaseModel):
    phone: str = None

@router.get("/profile")
def get_caregiver_profile(current_user: User = Depends(get_caregiver_user), db: Session = Depends(get_db)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "phone": current_user.phone,
        "timezone": current_user.timezone,
        "country": current_user.country
    }

@router.put("/profile/phone")
def update_caregiver_phone(data: CaregiverPhoneUpdate, current_user: User = Depends(get_caregiver_user), db: Session = Depends(get_db)):
    clean_phone = data.phone.strip() if data.phone else None
    current_user.phone = clean_phone if clean_phone != "" else None
    db.commit()
    db.refresh(current_user)
    return {
        "status": "success",
        "message": "Caregiver phone updated successfully.",
        "phone": current_user.phone,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "phone": current_user.phone
        }
    }

@router.get("/summary")
def get_summary(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    return caregiver_service.get_summary(db, [subject["id"]])

@router.get("/adherence")
def get_adherence(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    return caregiver_service.get_adherence(db, [subject["id"]])

@router.get("/emergencies")
def get_emergencies(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    return caregiver_service.get_emergencies(db, [subject["id"]])

@router.get("/behavior")
def get_behavior(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    subject = ctx['resolved_subject']
    return caregiver_service.get_behavior(db, [subject["id"]])
