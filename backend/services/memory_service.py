from sqlalchemy.orm import Session
from models.memory import MemoryEvent
from models.medicine import MedicineReminder
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MemoryCreate(BaseModel):
    user_id: str
    event_type: str
    content: str

class MemoryResponse(BaseModel):
    id: int
    user_id: str
    event_type: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

def add_memory(db: Session, memory: MemoryCreate):
    db_memory = MemoryEvent(
        user_id=memory.user_id,
        event_type=memory.event_type,
        content=memory.content
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return db_memory

def get_user_memories(db: Session, user_id: str, limit: int = 10):
    """
    Retrieve recent memories for a user.
    """
    return db.query(MemoryEvent).filter(MemoryEvent.user_id == user_id).order_by(MemoryEvent.timestamp.desc()).limit(limit).all()

def retrieve_memory_context(db: Session, query: str, user_id: str) -> str:
    """
    Retrieves relevant memory context based on a user's query.
    Intelligently injects database state (like medicine status) into the AI's context.
    """
    query_lower = query.lower()
    context_parts = []

    # 1. Detect Medicine Keywords
    medicine_keywords = ["medicine", "pill", "tablet", "medication", "dosage", "prescriptions", "മരുന്ന്"]
    if any(k in query_lower for k in medicine_keywords):
        context_parts.append(_get_medicine_memory(db))

    # 2. Detect Appointment Keywords
    appointment_keywords = ["appointment", "doctor", "visit", "hospital", "ഡോക്ടർ"]
    if any(k in query_lower for k in appointment_keywords):
        context_parts.append(_get_appointment_memory(db, user_id))
        
    # 3. General episodic memory fallback
    if not context_parts:
        memories = db.query(MemoryEvent).filter(MemoryEvent.user_id == user_id).order_by(MemoryEvent.timestamp.desc()).limit(3).all()
        if memories:
            episodic = "Recent General Memories:\n" + "\n".join([f"- {m.content}" for m in memories])
            context_parts.append(episodic)

    if not context_parts:
        return ""
        
    return "\n\nContext Information from User's Database:\n" + "\n\n".join(context_parts)

def _get_medicine_memory(db: Session) -> str:
    """
    Medicine memory service to retrieve today's medicine status and missed medicines.
    """
    medicines = db.query(MedicineReminder).all()
    if not medicines:
        return "Medicine Status: No medicines are currently scheduled in the database."
        
    context = "Medicine Status for Today:\n"
    for med in medicines:
        if med.taken_status and med.taken_at:
            status_text = f"Taken at {med.taken_at.strftime('%I:%M %p')}"
        else:
            status_text = "NOT TAKEN YET (Missed/Pending)"
            
        dosage_text = f" ({med.dosage})" if med.dosage else ""
        context += f"- {med.medicine_name}{dosage_text}: Scheduled for {med.reminder_time}. Status: {status_text}.\n"
        
    return context

def _get_appointment_memory(db: Session, user_id: str) -> str:
    """
    Retrieve appointment memories for the user.
    """
    appointments = db.query(MemoryEvent).filter(MemoryEvent.event_type == "appointment", MemoryEvent.user_id == user_id).order_by(MemoryEvent.timestamp.desc()).limit(3).all()
    if not appointments:
        return "Appointment Status: No upcoming appointments found in memory."
        
    context = "Appointments found in memory:\n"
    for appt in appointments:
        context += f"- {appt.content}\n"
        
    return context

def extract_and_store_memory(db: Session, text: str, user_id: str):
    """
    Rule-based memory extraction. Detects if the user says something like 
    'my appointment is' and saves it to the database automatically.
    """
    text_lower = text.lower()
    
    if "my appointment is" in text_lower:
        idx = text_lower.find("my appointment is")
        content = text[idx:].strip()
        add_memory(db, MemoryCreate(user_id=user_id, event_type="appointment", content=content))
    elif "remember that" in text_lower:
        idx = text_lower.find("remember that")
        content = text[idx + len("remember that"):].strip()
        add_memory(db, MemoryCreate(user_id=user_id, event_type="general", content=content))
