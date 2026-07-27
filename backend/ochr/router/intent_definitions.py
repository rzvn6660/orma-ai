from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    MEDICATION_QUERY = "medication_query"
    TIMELINE_QUERY = "timeline_query"
    HEALTH_RECORD_QUERY = "health_record_query"
    MEMORY_QUERY = "memory_query"
    CONVERSATION_QUERY = "conversation_query"
    EMERGENCY_QUERY = "emergency_query"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"

class RetrieverType(str, Enum):
    MEDICATION_RETRIEVER = "medication_retriever"
    PLANNER_RETRIEVER = "planner_retriever"
    HEALTH_RECORD_RETRIEVER = "health_record_retriever"
    MEMORY_RETRIEVER = "memory_retriever"
    CONVERSATION_RETRIEVER = "conversation_retriever"
    EMERGENCY_RETRIEVER = "emergency_retriever"

class RoutingDecision(BaseModel):
    intent: IntentType
    retrievers: List[RetrieverType] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)
