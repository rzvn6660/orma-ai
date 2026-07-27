import logging
from typing import Dict, Any, List, Optional
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class ConflictEngine:
    """
    Detects contradictory information.
    Never overwrites automatically. Asks the user to resolve conflicts.
    """
    
    def detect(self, candidate: Dict[str, Any], existing_memories: List[OCMEMemory]) -> Optional[Dict[str, Any]]:
        """
        Returns action='ASK_USER' if a conflict is found.
        """
        title = candidate.get("title", "").lower()
        new_value = candidate.get("value", "").lower()
        
        for mem in existing_memories:
            # Same title but different value indicates a potential conflict
            if mem.title.lower() == title and mem.value.lower() != new_value:
                logger.warning(f"[ConflictEngine] Conflict detected for '{mem.title}'. Existing: '{mem.value}', New: '{candidate.get('value')}'")
                return {
                    "action": "ASK_USER",
                    "reason": "Contradictory information detected.",
                    "conflict_data": {
                        "existing_id": mem.id,
                        "existing_title": mem.title,
                        "existing_value": mem.value,
                        "new_value": candidate.get("value")
                    }
                }
        return None

conflict_engine = ConflictEngine()
