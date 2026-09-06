import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Maintains the state of ongoing interactions.
    Tracks context, current active task, and missing required information.
    """
    def __init__(self):
        # In a production environment, this would be backed by Redis or a DB
        # Mapping user_id -> context dictionary
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": [],
                "current_task": None,
                "missing_info": [],
                "entities": {},
                "pending_confirmation": None
            }
        return self.sessions[user_id]

    def set_pending_confirmation(self, user_id: str, confirmation_type: str, data: dict):
        """Sets an explicit pending confirmation state for user action (e.g. medication creation)."""
        session = self._get_or_create_session(user_id)
        session["pending_confirmation"] = {
            "type": confirmation_type,
            "data": data
        }
        logger.info(f"[ConversationManager] Set pending confirmation '{confirmation_type}' for user {user_id}")

    def get_pending_confirmation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active pending confirmation state."""
        return self._get_or_create_session(user_id).get("pending_confirmation")

    def clear_pending_confirmation(self, user_id: str):
        """Clears active pending confirmation state."""
        session = self._get_or_create_session(user_id)
        session["pending_confirmation"] = None
        logger.info(f"[ConversationManager] Cleared pending confirmation for user {user_id}")

    def add_message(self, user_id: str, role: str, content: str):
        """Adds a message to the conversation history."""
        session = self._get_or_create_session(user_id)
        session["history"].append({"role": role, "content": content})
        # Keep recent history
        if len(session["history"]) > 10:
            session["history"] = session["history"][-10:]

    def get_history(self, user_id: str) -> list:
        """Retrieves conversation history for a user."""
        return self._get_or_create_session(user_id)["history"]

    def set_current_task(self, user_id: str, task: str):
        """Sets the active intent/task for the user."""
        session = self._get_or_create_session(user_id)
        session["current_task"] = task
        logger.info(f"[ConversationManager] Task set to '{task}' for user {user_id}")

    def get_current_task(self, user_id: str) -> Optional[str]:
        """Gets the active task for the user."""
        return self._get_or_create_session(user_id).get("current_task")

    def clear_current_task(self, user_id: str):
        """Clears the active task after completion or cancellation."""
        session = self._get_or_create_session(user_id)
        session["current_task"] = None
        session["missing_info"] = []
        session["entities"] = {}
        session["pending_confirmation"] = None
        logger.info(f"[ConversationManager] Cleared task for user {user_id}")

    def update_missing_info(self, user_id: str, missing_keys: list):
        """Tracks what information is still required to complete the task."""
        session = self._get_or_create_session(user_id)
        session["missing_info"] = missing_keys

    def get_missing_info(self, user_id: str) -> list:
        return self._get_or_create_session(user_id).get("missing_info", [])

    def save_entities(self, user_id: str, entities: dict):
        """Saves extracted entities to the session state."""
        session = self._get_or_create_session(user_id)
        session["entities"].update(entities)

    def get_entities(self, user_id: str) -> dict:
        return self._get_or_create_session(user_id).get("entities", {})

    def save_interaction_context(self, user_id: str, context: dict):
        """Saves structured interaction context (e.g. medications discussed) for follow-up resolution."""
        session = self._get_or_create_session(user_id)
        session["last_interaction"] = context

    def get_last_interaction_context(self, user_id: str) -> Optional[dict]:
        """Retrieves structured interaction context from the previous turn."""
        return self._get_or_create_session(user_id).get("last_interaction")

    def clear_session(self, user_id: str):
        """Resets conversation history and interaction context for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]

conversation_manager = ConversationManager()
