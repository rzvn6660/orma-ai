import logging
from typing import Dict, Any
from datetime import datetime, timezone
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class ForgettingEngine:
    """
    Supports Expire, Archive, Delete based on category and age.
    This can be run passively (e.g., cron) or during retrieval.
    """
    
    def evaluate_memory(self, memory: OCMEMemory) -> Optional[str]:
        """
        Evaluates a memory and returns 'DELETE', 'ARCHIVE', or None if it should be kept.
        """
        now = datetime.utcnow()
        
        if memory.expires_at and memory.expires_at < now:
            logger.info(f"[ForgettingEngine] Memory {memory.id} has expired.")
            
            # Policy: if it was temporary, we might delete. If it was important, maybe archive.
            if memory.category == "Temporary":
                return "DELETE"
            else:
                return "ARCHIVE"
                
        # We could add age-based forgetting (e.g. not used in 5 years -> archive).
        if memory.last_used:
            days_unused = (now - memory.last_used).days
            if days_unused > 365 and not memory.pinned:
                logger.info(f"[ForgettingEngine] Memory {memory.id} untouched for 1 year. Archiving.")
                return "ARCHIVE"
                
        return None

forgetting_engine = ForgettingEngine()
