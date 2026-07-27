import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OwnershipEngine:
    """
    Evaluates Memory Ownership Matrix.
    Ensures the Memory Reasoning Layer (MRL) doesn't duplicate data
    that belongs to another specialized agent (e.g., Medication Agent, Health Planner).
    """
    
    # Maps categories to their respective subsystems.
    # If the subsystem is not "OCME", the MRL will not save it.
    OWNERSHIP_MATRIX = {
        "Family": "OCME",
        "Personal": "OCME",
        "Preference": "OCME",
        "Custom": "OCME",
        "Conversation": "OCME",
        "Temporary": "OCME",
        "Medicine": "MedicationAgent",
        "Health": "HealthRecordsAgent", # Can be OCME if it's general health info, but strict rules say health records -> Health Records Agent. We'll handle it conditionally or strictly. 
        "Appointment": "HealthPlanner",
        "Emergency": "CaregiverAgent"
    }

    def evaluate(self, candidate: Dict[str, Any]) -> str:
        """
        Returns 'OCME' if it should be saved in memory.
        Returns 'IGNORE' if owned by another subsystem.
        """
        category = candidate.get("category", "Custom")
        owner = self.OWNERSHIP_MATRIX.get(category, "OCME")
        
        # Exception: Health category might just be general well-being vs an actual record.
        # But per specs: Medicine List -> Medication Agent, Health Records -> Health Records Agent, Appointments -> Health Planner.
        # If the category is strictly one of those, we ignore it in OCME to prevent duplication.
        
        if owner == "OCME":
            logger.info(f"[OwnershipEngine] OCME owns category '{category}'. Allowed.")
            return "OCME"
            
        logger.info(f"[OwnershipEngine] Category '{category}' is owned by {owner}. Ignored by OCME.")
        return "IGNORE"

ownership_engine = OwnershipEngine()
