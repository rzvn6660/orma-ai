from typing import Any, Dict
from sqlalchemy.orm import Session
from database import SessionLocal
from models.memory import MemoryEvent
from .retriever_base import BaseRetriever

class MemoryRetriever(BaseRetriever):
    """Retrieves AI memories and important events."""
    
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = query_context.get("user_id")
        
        db: Session = SessionLocal()
        try:
            query = db.query(MemoryEvent)
            if user_id:
                query = query.filter(MemoryEvent.user_id == user_id)
                
            memories = query.all()
            
            stored_ai_memories = []
            important_events = []
            user_preferences = []
            
            for m in memories:
                mem_dict = {
                    "id": m.id,
                    "event_type": m.event_type,
                    "content": m.content,
                }
                
                stored_ai_memories.append(mem_dict)
                
                if m.event_type == "appointment" or m.event_type == "important":
                    important_events.append(mem_dict)
                elif m.event_type == "preference":
                    user_preferences.append(mem_dict)

            return {
                "stored_ai_memories": stored_ai_memories,
                "important_events": important_events,
                "user_preferences": user_preferences
            }
        finally:
            db.close()
