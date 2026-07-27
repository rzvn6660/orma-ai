from typing import Dict, List
from .intent_definitions import IntentType, RetrieverType

# Mapping from detected intent to the required retrievers
INTENT_TO_RETRIEVERS_MAP: Dict[IntentType, List[RetrieverType]] = {
    IntentType.MEDICATION_QUERY: [
        RetrieverType.MEDICATION_RETRIEVER
    ],
    IntentType.TIMELINE_QUERY: [
        RetrieverType.PLANNER_RETRIEVER,
        RetrieverType.HEALTH_RECORD_RETRIEVER,
        RetrieverType.MEMORY_RETRIEVER,
        RetrieverType.CONVERSATION_RETRIEVER
    ],
    IntentType.HEALTH_RECORD_QUERY: [
        RetrieverType.HEALTH_RECORD_RETRIEVER
    ],
    IntentType.MEMORY_QUERY: [
        RetrieverType.MEMORY_RETRIEVER
    ],
    IntentType.CONVERSATION_QUERY: [
        RetrieverType.CONVERSATION_RETRIEVER
    ],
    IntentType.EMERGENCY_QUERY: [
        RetrieverType.EMERGENCY_RETRIEVER,
        RetrieverType.HEALTH_RECORD_RETRIEVER
    ],
    IntentType.GENERAL_QUERY: [
        RetrieverType.MEMORY_RETRIEVER,
        RetrieverType.CONVERSATION_RETRIEVER
    ],
    IntentType.UNKNOWN: []
}
