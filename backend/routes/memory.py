from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from services import memory_service
from dependencies import get_current_user
from models.user import User, CaregiverRelationship

router = APIRouter()

@router.post("/", response_model=memory_service.MemoryResponse)
def create_memory(memory: memory_service.MemoryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Store a new memory event (e.g. daily medicine activity, appointments).
    """
    target_user_id = memory.user_id
    if target_user_id != current_user.id:
        if current_user.role == "caregiver":
            rel = db.query(CaregiverRelationship).filter(
                CaregiverRelationship.caregiver_id == current_user.id,
                CaregiverRelationship.elder_id == target_user_id,
                CaregiverRelationship.status == "approved"
            ).first()
            if not rel:
                raise HTTPException(status_code=403, detail="Access denied. Not authorized for this subject.")
        else:
            raise HTTPException(status_code=403, detail="Access denied. Cannot create memories for other users.")
            
    return memory_service.add_memory(db=db, memory=memory)

@router.get("/{user_id}", response_model=List[memory_service.MemoryResponse])
def get_memories(user_id: str, limit: int = 10, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve recent memories for a user.
    """
    if user_id != current_user.id:
        if current_user.role == "caregiver":
            rel = db.query(CaregiverRelationship).filter(
                CaregiverRelationship.caregiver_id == current_user.id,
                CaregiverRelationship.elder_id == user_id,
                CaregiverRelationship.status == "approved"
            ).first()
            if not rel:
                raise HTTPException(status_code=403, detail="Access denied. Not authorized for this subject.")
        else:
            raise HTTPException(status_code=403, detail="Access denied. Cannot access other users' memories.")
            
    return memory_service.get_user_memories(db, user_id=user_id, limit=limit)

@router.get("/{user_id}/context")
def get_memory_context(user_id: str, query: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve intelligent context for a specific query.
    """
    if user_id != current_user.id:
        if current_user.role == "caregiver":
            rel = db.query(CaregiverRelationship).filter(
                CaregiverRelationship.caregiver_id == current_user.id,
                CaregiverRelationship.elder_id == user_id,
                CaregiverRelationship.status == "approved"
            ).first()
            if not rel:
                raise HTTPException(status_code=403, detail="Access denied. Not authorized for this subject.")
        else:
            raise HTTPException(status_code=403, detail="Access denied. Cannot access other users' memory context.")
            
    context = memory_service.retrieve_memory_context(db, query=query, user_id=user_id)
    return {"context": context}
