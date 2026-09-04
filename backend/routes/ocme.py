import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from dependencies import get_current_context
from memory.memory_models import OCMEMemoryResponse, OCMEMemory
from memory.memory_store import memory_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["OCME"])

# Note: user_id comes from auth dependencies (get_current_context)

@router.get("", response_model=List[OCMEMemoryResponse])
@router.get("/", response_model=List[OCMEMemoryResponse])
def get_memories(
    category: Optional[str] = None,
    search: Optional[str] = None,
    visibility: Optional[str] = None,
    sort_by: Optional[str] = "recently_used", # importance, recently_used, alphabetical, pinned
    db: Session = Depends(get_db),
    ctx: dict = Depends(get_current_context)
):
    """Retrieves memories with search, filtering, and sorting."""
    user_id = ctx['resolved_subject']['id']
    from sqlalchemy import or_
    filters = [OCMEMemory.user_id == str(user_id)]
    if str(user_id).isdigit():
        filters.append(OCMEMemory.user_id == int(user_id))
    query = db.query(OCMEMemory).filter(or_(*filters))
    
    if category:
        query = query.filter(OCMEMemory.category == category)
    if visibility:
        query = query.filter(OCMEMemory.visibility == visibility)
    if search:
        search_term = f"%{search.lower()}%"
        # simple ILIKE search (sqlite compatible by using lower())
        query = query.filter(
            (OCMEMemory.title.ilike(search_term)) | (OCMEMemory.value.ilike(search_term))
        )
        
    memories = query.all()
    
    # Python-side sorting for flexibility in this sprint
    if sort_by == "importance":
        memories.sort(key=lambda x: x.importance, reverse=True)
    elif sort_by == "recently_used":
        # Handle None for last_used
        from datetime import datetime
        min_date = datetime.min
        memories.sort(key=lambda x: x.last_used or min_date, reverse=True)
    elif sort_by == "alphabetical":
        memories.sort(key=lambda x: x.title.lower())
    elif sort_by == "pinned":
        memories.sort(key=lambda x: (x.pinned, x.importance), reverse=True)

    logger.info(f"[OCME API] Retrieved {len(memories)} memories for user {user_id}")
    return memories

@router.get("/{memory_id}", response_model=OCMEMemoryResponse)
def get_memory(memory_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    memory = memory_store.get_memory_by_id(db, user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory

@router.put("/{memory_id}", response_model=OCMEMemoryResponse)
def update_memory(memory_id: int, updates: dict, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    memory = memory_store.get_memory_by_id(db, user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    for key, val in updates.items():
        if hasattr(memory, key) and key not in ["id", "user_id"]:
            setattr(memory, key, val)
            
    db.commit()
    db.refresh(memory)
    logger.info(f"[OCME API] Updated memory {memory_id}")
    return memory

@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    success = memory_store.delete_memory(db, user_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    logger.info(f"[OCME API] Deleted memory {memory_id}")
    return {"status": "success"}

@router.post("/{memory_id}/pin", response_model=OCMEMemoryResponse)
def pin_memory(memory_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    memory = memory_store.get_memory_by_id(db, user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    memory.pinned = not memory.pinned
    db.commit()
    db.refresh(memory)
    logger.info(f"[OCME API] Toggled pin for memory {memory_id} to {memory.pinned}")
    return memory

@router.post("/{memory_id}/share", response_model=OCMEMemoryResponse)
def share_memory(memory_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    memory = memory_store.get_memory_by_id(db, user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    # Toggle visibility
    if memory.visibility == "private":
        memory.visibility = "shared"
    else:
        memory.visibility = "private"
        
    db.commit()
    db.refresh(memory)
    logger.info(f"[OCME API] Toggled share for memory {memory_id} to {memory.visibility}")
    return memory

@router.post("/{memory_id}/explain")
def explain_memory(memory_id: int, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    user_id = ctx['resolved_subject']['id']
    memory = memory_store.get_memory_by_id(db, user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    # Fetch audit trails
    from memory.memory_models import OCMEAudit
    audit_logs = db.query(OCMEAudit).filter(OCMEAudit.memory_id == memory_id).order_by(OCMEAudit.timestamp.desc()).all()
    
    # Construct explanation
    date_str = memory.created_at.strftime("%d %B %Y")
    confidence_pct = int(memory.confidence * 100)
    trust_score = getattr(memory, 'trust_score', 50)
    
    explanation = f"I remembered '{memory.title}' as a {memory.category} memory because you mentioned it during a {memory.source.lower()}."
    explanation += f"\n\nMemory Stats:\n- Trust Score: {trust_score:.1f}/100\n- Confidence: {confidence_pct}%\n- Used: {memory.usage_count} times"
    
    if audit_logs:
        explanation += "\n\nReasoning & Audit Trail:"
        for log in audit_logs[:3]: # Show top 3 recent actions
            log_time = log.timestamp.strftime("%Y-%m-%d")
            explanation += f"\n- {log_time} [{log.action.upper()}] by {log.source}: {log.details or 'No details'}"
            
    logger.info(f"[OCME API] Explained memory {memory_id}")
    return {"explanation": explanation}
