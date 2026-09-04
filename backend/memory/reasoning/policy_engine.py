import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PolicyEngine:
    """
    Configurable policies for every memory category.
    Determines base expiration, auto-save rules, etc.
    """
    
    POLICIES = {
        "Family": {
            "action": "SAVE",
            "expires_in_days": None,
        },
        "Personal": {
            "action": "SAVE",
            "expires_in_days": None,
        },
        "Preference": {
            "action": "SAVE",
            "expires_in_days": None,
        },
        "Temporary": {
            "action": "SAVE",
            "expires_in_days": 1, # Expire automatically
        },
        "Conversation": {
            "action": "IGNORE",
        },
        "Medicine": {
            "action": "IGNORE", # Handled by ownership, but acts as a fallback
        },
        "Health": {
            "action": "IGNORE", # If health readings, do not create long-term memory
        }
    }

    def apply_policy(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns policy rules for the candidate.
        """
        category = candidate.get("category", "Custom")
        policy = self.POLICIES.get(category, {"action": "SAVE", "expires_in_days": None})
        
        logger.info(f"[PolicyEngine] Applied policy for '{category}': {policy}")
        return policy

policy_engine = PolicyEngine()
