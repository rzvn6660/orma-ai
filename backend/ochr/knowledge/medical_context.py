from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class MedicalSourceMetadata(BaseModel):
    source_name: str
    provider: str
    confidence: float = 1.0
    publication_date: Optional[str] = None
    url: Optional[str] = None

class MedicalKnowledgeItem(BaseModel):
    query: str
    category: str  # e.g., "drug", "condition"
    content: Dict[str, Any]
    metadata: MedicalSourceMetadata

class MedicalContext(BaseModel):
    drugs: List[MedicalKnowledgeItem] = Field(default_factory=list)
    conditions: List[MedicalKnowledgeItem] = Field(default_factory=list)
    general_health: List[MedicalKnowledgeItem] = Field(default_factory=list)
