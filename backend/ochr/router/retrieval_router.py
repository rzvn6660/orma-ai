import re
import logging
from typing import List, Optional
from .intent_definitions import IntentType, RetrieverType, RoutingDecision
from .routing_rules import INTENT_TO_RETRIEVERS_MAP

logger = logging.getLogger(__name__)

class RetrievalRouter:
    """
    Core logic for determining which retrievers to route a given query to.
    This uses heuristic/regex logic for the foundational sprint,
    which can be swapped out for LLM-based or classifier-based intent detection later.
    """
    
    def __init__(self):
        # A simple keyword-based intent mapping for the foundation.
        # Patterns are checked in order.
        self._keyword_mapping = [
            (r'\b(medicine|medication|pill|prescription|dose)\b', IntentType.MEDICATION_QUERY),
            (r'\b(emergency|hospital|ambulance|urgent|pain|bleeding)\b', IntentType.EMERGENCY_QUERY),
            (r'\b(before|after|yesterday|tomorrow|last week|schedule|timeline|happened)\b', IntentType.TIMELINE_QUERY),
            (r'\b(health record|report|test result|doctor|surgery|diagnosis)\b', IntentType.HEALTH_RECORD_QUERY),
            (r'\b(remember|memory|recall)\b', IntentType.MEMORY_QUERY),
            (r'\b(said|told me|conversation|talked|spoke)\b', IntentType.CONVERSATION_QUERY),
        ]

    def detect_intent(self, query: str) -> IntentType:
        """
        Detects the user's intent based on the natural language query.
        """
        query_lower = query.lower()
        
        # Determine intent by iterating over patterns
        for pattern, intent in self._keyword_mapping:
            if re.search(pattern, query_lower):
                logger.info(f"Detected intent '{intent.value}' for query: '{query}'")
                return intent
        
        logger.info(f"No specific intent detected, defaulting to GENERAL_QUERY for query: '{query}'")
        return IntentType.GENERAL_QUERY

    def route_query(self, query: str) -> RoutingDecision:
        """
        Routes a query to the appropriate retrievers based on the detected intent.
        """
        intent = self.detect_intent(query)
        retrievers = INTENT_TO_RETRIEVERS_MAP.get(intent, [])
        
        decision = RoutingDecision(
            intent=intent,
            retrievers=retrievers,
            confidence=0.8, # Placeholder for heuristic
            metadata={"query": query}
        )
        
        logger.info(f"Routing decision made: intent={decision.intent.value}, retrievers={[r.value for r in decision.retrievers]}")
        return decision
