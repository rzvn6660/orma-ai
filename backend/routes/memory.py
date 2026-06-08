from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from services import memory_service

router = APIRouter()

@router.post("/", response_model=memory_service.MemoryResponse)
def create_memory(memory: memory_service.MemoryCreate, db: Session = Depends(get_db)):
    """
    Store a new memory event (e.g. daily medicine activity, appointments).
    """
    return memory_service.add_memory(db=db, memory=memory)

@router.get("/{user_id}", response_model=List[memory_service.MemoryResponse])
def get_memories(user_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve recent memories for a user.
    """
    return memory_service.get_user_memories(db, user_id=user_id, limit=limit)

@router.get("/{user_id}/context")
def get_memory_context(user_id: str, query: str, db: Session = Depends(get_db)):
    """
    Retrieve intelligent context for a specific query.
    """
    context = memory_service.retrieve_memory_context(db, query=query, user_id=user_id)
    return {"context": context}
