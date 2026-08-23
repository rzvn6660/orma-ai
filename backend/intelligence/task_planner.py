import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

class TaskPlanner:
    """
    Guides multi-turn conversations to collect all required fields before agent invocation.
    """
    # Define required fields per intent for execution
    REQUIRED_FIELDS = {
        "Appointment": ["doctor_name", "date", "time"],
        "Medicine": ["medicine_name", "action"],
        "Reminder": ["title", "time"],
        "HealthRecord": ["test_name"],
        "Memory": ["query_subject"],
        "Caregiver": ["message_content"],
        "Emergency": [] # Emergency needs no fields, execute immediately
    }

    def __init__(self):
        pass

    def evaluate_task_readiness(self, intent: str, entities: Dict[str, Any], raw_text: str = "") -> Tuple[bool, List[str]]:
        """
        Checks if the collected entities satisfy the requirements for the given intent.
        Returns (is_ready, list_of_missing_fields)
        """
        logger.info(f"[TaskPlanner] Evaluating readiness for intent '{intent}' with entities: {entities}, raw_text: '{raw_text}'")
        
        low_text = raw_text.lower() if raw_text else ""
        query_words = ["did i", "do i", "what", "which", "when", "have i", "any", "?", "status", "due", "pending", "today", "show", "tell", "check", "list", "already", "morning", "afternoon", "evening", "night", "next", "remaining", "how many", "scheduled", "taken"]
        action_val = str(entities.get("action", "")).lower()
        
        is_query = action_val in ["query", "status", "check", "list", "view", "recall", "ask"] or any(w in low_text for w in query_words)
        is_create_command = any(w in low_text for w in ["create", "add new", "schedule a new", "remind me to", "set reminder", "new medicine", "new appointment"])
        
        # Informational queries never require missing fields
        if is_query and not is_create_command:
            logger.info(f"[TaskPlanner] Intent '{intent}' identified as an informational query. Ready for response.")
            return True, []

        required = self.REQUIRED_FIELDS.get(intent, [])
        missing = []
        
        for field in required:
            val = entities.get(field)
            if not val or str(val).lower() == "null" or str(val).strip() == "":
                missing.append(field)
                
        is_ready = len(missing) == 0
        
        if not is_ready:
            logger.info(f"[TaskPlanner] Task not ready. Missing fields: {missing}")
        else:
            logger.info(f"[TaskPlanner] Task ready for execution.")
            
        return is_ready, missing

task_planner = TaskPlanner()
