from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import caregiver_service
from models.user import User, CaregiverRelationship
from dependencies import get_current_context

router = APIRouter()

def get_linked_elder_ids(db: Session, caregiver_id: str):
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.caregiver_id == caregiver_id,
        CaregiverRelationship.status == "approved"
    ).all()
    return [r.elder_id for r in rels]

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
