from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ReasoningCategory(str, Enum):
    MEDICATION = "medication"
    HEALTH = "health"
    PLANNER = "planner"
    MEMORY = "memory"
    CONVERSATION = "conversation"
    EMERGENCY = "emergency"
    GENERAL = "general"

class SafetyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ReasoningPlan(BaseModel):
    reasoning_type: ReasoningCategory
    selected_prompt_template: str
    required_context_sections: List[str] = Field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.LOW
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    explanation_metadata: Dict[str, str] = Field(default_factory=dict)
