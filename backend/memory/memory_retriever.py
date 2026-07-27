import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class MemoryRetriever:
    """
    Intelligently retrieves the most relevant memories for the current context.
    """
    
    # Mapping orchestration intents to relevant memory categories
    INTENT_CATEGORY_MAP = {
        "Appointment": ["Appointment", "Health", "Doctor", "Important Event"],
        "Family": ["Family", "Caregiver", "Personal"],
        "Medicine": ["Medicine", "Health", "Preference"],
        "HealthRecord": ["Health", "Medicine", "Appointment"],
        "Emergency": ["Health", "Medicine", "Family", "Personal"],
        "GeneralChat": ["Personal", "Preference", "Conversation", "Family", "Important Event"],
        "Reminder": ["Temporary", "Preference", "Medicine", "Appointment"],
        "Memory": ["Personal", "Family", "Health", "Medicine", "Appointment", "Preference", "Important Event", "Temporary", "Conversation", "Custom"],
        "Caregiver": ["Family", "Caregiver", "Health", "Preference"],
        "Settings": ["Preference", "Custom"]
    }

    def __init__(self):
        pass

    def retrieve(self, db: Session, user_id: int, intent: str, limit: int = 5) -> List[OCMEMemory]:
        """
        Retrieves, ranks, and returns the top 3-5 most relevant memories.
        Automatically updates usage statistics.
        """
        logger.info(f"[MemoryRetriever] Retrieving memories for user {user_id} with intent '{intent}'")
        
        # 1. Category Filtering
        categories = self.INTENT_CATEGORY_MAP.get(intent, ["Personal", "Conversation", "Preference"])
        
        # 2. Query
        # We fetch all matching categories for the user (we could pre-filter if it's too large)
        memories = db.query(OCMEMemory).filter(
            OCMEMemory.user_id == user_id,
            OCMEMemory.category.in_(categories)
        ).all()
        
        if not memories:
            logger.info("[MemoryRetriever] No relevant memories found in DB.")
            return []
            
        # 3. Ranking
        ranked_memories = sorted(memories, key=self._calculate_rank_score, reverse=True)
        top_memories = ranked_memories[:limit]
        
        # 4. Usage Tracking
        self._update_usage(db, top_memories)
        
        logger.info(f"[MemoryRetriever] Retrieved {len(top_memories)} top memories.")
        return top_memories

    def _calculate_rank_score(self, memory: OCMEMemory) -> float:
        """
        Calculates a ranking score based on importance, confidence, usage, recency, and pinned status.
        """
        score = 0.0
        
        # Base importance (0-100) -> scale to 0-1
        score += (memory.importance / 100.0) * 0.4
        
        # Confidence (0-1) -> weight 0.2
        score += memory.confidence * 0.2
        
        # Pinned -> big boost
        if memory.pinned:
            score += 0.3
            
        # Usage Count -> diminish returns (0-1 max boost)
        usage_boost = min(memory.usage_count * 0.05, 0.1)
        score += usage_boost
        
        # Recency (decay over time since updated)
        now = datetime.utcnow()
        if memory.updated_at:
            days_old = (now - memory.updated_at).days
            if days_old < 7:
                score += 0.1
            elif days_old < 30:
                score += 0.05
                
        return score

    def _update_usage(self, db: Session, memories: List[OCMEMemory]):
        """Updates last_used and usage_count for retrieved memories."""
        now = datetime.utcnow()
        for memory in memories:
            memory.last_used = now
            memory.usage_count = (memory.usage_count or 0) + 1
            logger.info(f"[MemoryRetriever] Updated usage for Memory ID {memory.id}. Usage count: {memory.usage_count}")
        db.commit()

memory_retriever = MemoryRetriever()
