from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EvidenceItem(BaseModel):
    category: str
    content: Dict[str, Any]
    source_name: str
    provider: str
    confidence: float
    timestamp: Optional[str] = None
    is_medical: bool = False

class ExplanationResult(BaseModel):
    reasoning_category: str
    confidence_score: float
    safety_level: str
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    contributing_context_sections: List[str] = Field(default_factory=list)
    medical_sources: List[str] = Field(default_factory=list)
    explanation_summary: str
