from pydantic import BaseModel, Field
from typing import List, Dict, Any

class TimelineEvent(BaseModel):
    id: str
    timestamp: str
    title: str
    category: str
    severity: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TimelineResult(BaseModel):
    events: List[TimelineEvent] = Field(default_factory=list)
    date_range: Dict[str, str] = Field(default_factory=dict)
    summary: str = ""
    statistics: Dict[str, int] = Field(default_factory=dict)
