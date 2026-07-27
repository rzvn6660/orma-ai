from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class UnifiedContext(BaseModel):
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    planner: List[Dict[str, Any]] = Field(default_factory=list)
    health_records: List[Dict[str, Any]] = Field(default_factory=list)
    memories: List[Dict[str, Any]] = Field(default_factory=list)
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retrieval_sources: List[str] = Field(default_factory=list)
