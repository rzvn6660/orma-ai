import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from memory.memory_models import OCMEMemory, OCMEMemoryCreate

logger = logging.getLogger(__name__)

class MemoryStore:
    """
    Clean repository abstraction for interacting with the database.
    Does NOT implement vector search or complex retrieval yet.
    """
    def __init__(self):
        pass

    def save_memory(self, db: Session, user_id: Any, memory_data: OCMEMemoryCreate) -> OCMEMemory:
        """Saves a new memory to the database."""
        logger.info(f"[MemoryStore] Saving memory '{memory_data.title}' for user {user_id}")
        db_memory = OCMEMemory(
            user_id=str(user_id),
            category=memory_data.category,
            title=memory_data.title,
            value=memory_data.value,
            importance=memory_data.importance,
            confidence=memory_data.confidence,
            visibility=memory_data.visibility,
            source=memory_data.source,
            trust_score=memory_data.trust_score,
            expires_at=memory_data.expires_at
        )
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        return db_memory

    def get_all_memories(self, db: Session, user_id: Any) -> List[OCMEMemory]:
        """Retrieves all memories for a user."""
        from sqlalchemy import or_
        filters = [OCMEMemory.user_id == str(user_id)]
        if str(user_id).isdigit():
            filters.append(OCMEMemory.user_id == int(user_id))
        return db.query(OCMEMemory).filter(or_(*filters)).all()

    def get_memories_by_category(self, db: Session, user_id: Any, category: str) -> List[OCMEMemory]:
        """Retrieves memories filtered by category."""
        from sqlalchemy import or_
        filters = [OCMEMemory.user_id == str(user_id)]
        if str(user_id).isdigit():
            filters.append(OCMEMemory.user_id == int(user_id))
        return db.query(OCMEMemory).filter(or_(*filters), OCMEMemory.category == category).all()

    def get_memory_by_id(self, db: Session, user_id: Any, memory_id: int) -> Optional[OCMEMemory]:
        """Retrieves a specific memory by ID."""
        from sqlalchemy import or_
        filters = [OCMEMemory.user_id == str(user_id)]
        if str(user_id).isdigit():
            filters.append(OCMEMemory.user_id == int(user_id))
        return db.query(OCMEMemory).filter(or_(*filters), OCMEMemory.id == memory_id).first()

    def delete_memory(self, db: Session, user_id: Any, memory_id: int) -> bool:
        """Deletes a specific memory."""
        memory = self.get_memory_by_id(db, user_id, memory_id)
        if memory:
            db.delete(memory)
            db.commit()
            logger.info(f"[MemoryStore] Deleted memory ID {memory_id} for user {user_id}")
            return True
        return False

memory_store = MemoryStore()
