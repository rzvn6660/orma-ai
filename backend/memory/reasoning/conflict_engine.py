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
                # If the memory is a User Preference, an explicit statement is an update rather than an unresolvable contradiction
                if mem.category == "Preference" or candidate.get("category") == "Preference":
                    logger.info(f"[ConflictEngine] Preference update detected for '{mem.title}'. Updating to '{candidate.get('value')}'.")
                    return {
                        "action": "UPDATE",
                        "reason": "User updated preference.",
                        "existing_memory": mem,
                        "updates": {
                            "value": candidate.get("value"),
                            "confidence": candidate.get("confidence", 0.95),
                            "usage_count": (mem.usage_count or 0) + 1
                        }
                    }

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
