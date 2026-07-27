import logging
from typing import Dict, Any

from .retrieval_router import RetrievalRouter
from .intent_definitions import RoutingDecision, IntentType

logger = logging.getLogger(__name__)

class RouterService:
    """
    Service layer wrapper for the Retrieval Router.
    This acts as the entry point for other parts of the ORMA system
    to request retrieval routing decisions.
    """

    def __init__(self):
        self.router = RetrievalRouter()
        logger.info("RouterService initialized.")

    def get_routing_decision(self, query: str) -> dict:
        """
        Analyzes a natural language query and returns a structured routing decision
        as a dictionary.
        
        Args:
            query (str): The user's input query.
            
        Returns:
            dict: A dictionary containing the intent and mapped retrievers.
        """
        if not query or not query.strip():
            logger.warning("Empty query received for routing.")
            return {
                "intent": IntentType.UNKNOWN.value,
                "retrievers": []
            }
            
        decision = self.router.route_query(query)
        return {
            "intent": decision.intent.value,
            "retrievers": [r.value for r in decision.retrievers]
        }
