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

    def validate(self, intent: str, entities: Dict[str, Any]) -> Tuple[str, str, list]:
        """
        Returns (Decision, Reason, MissingFields)
        Decision can be: "Continue", "Clarify", "Reject", "Escalate"
        """
        logger.info(f"[SafetyValidator] Validating intent '{intent}' with entities: {entities}")
        
        # 1. Safety Checks (Reject / Escalate)
        if intent == "Medicine":
            # Very basic safety example: prevent dangerous dosage strings, or escalate if they ask about pain
            if entities.get("medicine_name", "").lower() in ["morphine", "fentanyl"]:
                return "Escalate", "High-risk medication mentioned. Requires human caregiver or doctor.", []

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
