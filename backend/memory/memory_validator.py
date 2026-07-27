import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class MemoryValidator:
    """
    Validates candidates before saving. Checks for duplicates and conflicts.
    """
    def __init__(self):
        pass

    def validate_candidate(self, candidate: Dict[str, Any], existing_memories: list) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Returns (is_valid, reason, conflict_data).
        Checks if the candidate conflicts with or duplicates existing memories.
        """
        title = candidate.get("title", "").lower()
        value = candidate.get("value", "").lower()
        
        logger.info(f"[MemoryValidator] Validating candidate '{title}' against {len(existing_memories)} existing memories.")
        
        for mem in existing_memories:
            # Duplicate check
            if mem.title.lower() == title and mem.value.lower() == value:
                logger.info(f"[MemoryValidator] Duplicate memory detected: {title}")
                return False, "Duplicate memory detected", {}
                
            # Conflict check
            if mem.title.lower() == title and mem.value.lower() != value:
                logger.warning(f"[MemoryValidator] Conflict detected for '{title}'. New value: '{value}', Old value: '{mem.value}'")
                
                conflict_data = {
                    "existing_id": mem.id,
                    "existing_title": mem.title,
                    "existing_value": mem.value,
                    "new_value": candidate.get("value"),
                    "action_required": "ask_user"
                }
                
                return False, f"Conflict with existing memory: '{mem.value}'", conflict_data
                
        logger.info("[MemoryValidator] Validation passed. No duplicates or conflicts.")
        return True, "Valid", {}

memory_validator = MemoryValidator()
