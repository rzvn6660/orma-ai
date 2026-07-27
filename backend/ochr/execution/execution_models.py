from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ochr.explainability.explanation_models import ExplanationResult

class LLMResponse(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseModel):
    is_successful: bool
    response_text: str
    validation_status: str
    confidence: float
    explanation: Optional[ExplanationResult] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FormattedPrompt(BaseModel):
    system_instruction: str
    personal_context: str
    medical_context: str
    user_query: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
