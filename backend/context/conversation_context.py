from typing import Optional, List
from pydantic import BaseModel

class ConversationContext(BaseModel):
    actor_id: str
    actor_name: str
    actor_role: str
    
    subject_id: str
    subject_name: str
    subject_role: str
    
    permissions: List[str]
    
    requires_clarification: bool = False
    clarification_message: Optional[str] = None
