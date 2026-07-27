import logging
from typing import Dict, Any, List, Optional
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class DuplicateEngine:
    """
    Detects duplicate memories.
    If duplicate, does not create a second memory, but instead returns an UPDATE action
    to increase confidence and usage count.
    """
    
    def detect(self, candidate: Dict[str, Any], existing_memories: List[OCMEMemory]) -> Optional[Dict[str, Any]]:
        """
        Returns a dict with action='UPDATE' and the existing memory id if a duplicate is found.
        Otherwise returns None.
        """
        title = candidate.get("title", "").lower()
        value = candidate.get("value", "").lower()
        
        for mem in existing_memories:
            # Exact match check
            if mem.title.lower() == title and mem.value.lower() == value:
                logger.info(f"[DuplicateEngine] Duplicate detected: {mem.title}")
                return {
                    "action": "UPDATE",
                    "reason": "Duplicate detected. Increasing confidence and usage count.",
                    "existing_memory": mem,
                    "updates": {
                        "confidence": min(1.0, mem.confidence + 0.1),
                        "usage_count": mem.usage_count + 1
                    }
                }
        return None

duplicate_engine = DuplicateEngine()
