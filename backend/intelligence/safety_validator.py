import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class SafetyValidator:
    """
    Validates healthcare constraints, detects missing data, and determines the next action.
    """
    # Define required fields per intent
    REQUIRED_FIELDS = {
        "Appointment": ["doctor_name", "date"], # Example: time can be default, but date/doctor is needed
        "Medicine": ["medicine_name"],
        "Reminder": ["title", "time"]
    }

    def __init__(self):
        pass

    def validate(self, intent: str, entities: Dict[str, Any], raw_text: str = "") -> Tuple[str, str, list]:
        """
        Returns (Decision, Reason, MissingFields)
        Decision can be: "Continue", "Clarify", "Reject", "Escalate"
        """
        logger.info(f"[SafetyValidator] Validating intent '{intent}' with entities: {entities}, raw_text: '{raw_text}'")
        
        # 1. Safety Checks (Reject / Escalate)
        if intent == "Medicine":
            # Very basic safety example: prevent dangerous dosage strings, or escalate if they ask about pain
            if entities.get("medicine_name", "").lower() in ["morphine", "fentanyl"]:
                return "Escalate", "High-risk medication mentioned. Requires human caregiver or doctor.", []

        low_text = raw_text.lower() if raw_text else ""
        query_words = ["did i", "do i", "what", "which", "when", "have i", "any", "?", "status", "due", "pending", "today", "show", "tell", "check", "list", "already", "morning", "afternoon", "evening", "night", "next", "remaining", "how many", "scheduled", "taken"]
        action_val = str(entities.get("action", "")).lower()
        is_query = action_val in ["query", "status", "check", "list", "view", "recall", "ask"] or any(w in low_text for w in query_words)
        is_create_command = any(w in low_text for w in ["create", "add new", "schedule a new", "remind me to", "set reminder", "new medicine", "new appointment"])

        if is_query and not is_create_command:
            logger.info(f"[SafetyValidator] Intent '{intent}' is an informational query. Validation passed.")
            return "Continue", "Validation passed for query.", []

        # 2. Completeness Checks (Clarify)
        required = self.REQUIRED_FIELDS.get(intent, [])
        missing = []
        for field in required:
            val = entities.get(field)
            if not val or val == "null":
                missing.append(field)
                
        if missing:
            logger.info(f"[SafetyValidator] Missing fields for {intent}: {missing}")
            return "Clarify", f"Missing required fields: {', '.join(missing)}", missing

        # 3. All good
        return "Continue", "Validation passed.", []

safety_validator = SafetyValidator()
