from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from services import health_planner_service
from dependencies import get_current_user, get_elderly_user, get_current_context
from models.user import User, CaregiverRelationship
from services.websocket_manager import manager

router = APIRouter()

@router.post("/", response_model=health_planner_service.HealthEventResponse)
def create_event(event: health_planner_service.HealthEventCreate, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Add a new health event.
    """
    actor = ctx['authenticated_user']
    subject = ctx['resolved_subject']
    
    return health_planner_service.create_health_event(
        db=db, 
        event=event, 
        actor_id=actor.id, 
        subject_id=subject["id"],
        role=actor.role
    )

@router.get("/", response_model=List[health_planner_service.HealthEventResponse])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Retrieve health events for the active subject.
    """
    subject = ctx['resolved_subject']
    return health_planner_service.get_events_for_users(db, [subject["id"]], skip=skip, limit=limit)

@router.put("/{id}/completed", response_model=health_planner_service.HealthEventResponse)
async def complete_event(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Mark a health event as completed.
    """
    subject = ctx['resolved_subject']
    event = health_planner_service.mark_event_completed(db, event_id=id, subject_id=subject["id"])
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Notify caregivers
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "health_event_completed",
            "event_id": event.id,
            "title": event.title,
            "message": f"Event '{event.title}' was marked as completed."
        }, rel.caregiver_id)
        
    return event

@router.delete("/{id}")
async def delete_event(id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Delete a health event.
    """
    subject = ctx['resolved_subject']
    success = health_planner_service.delete_event(db, event_id=id, subject_id=subject["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Event not found or unauthorized")
        
    # Notify caregivers
    rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == subject["id"], CaregiverRelationship.status == "approved").all()
    for rel in rels:
        await manager.send_personal_message({
            "type": "health_event_deleted",
            "event_id": id,
            "message": "A health event was deleted."
        }, rel.caregiver_id)
        
    return {"status": "success", "message": "Event deleted"}
