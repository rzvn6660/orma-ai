from dataclasses import dataclass
from typing import Any, Dict
from sqlalchemy.orm import Session

@dataclass
class WorkflowContext:
    """
    State context passed to workflow templates during execution.
    """
    db: Session
    workflow_id: str
    idempotency_key: str
    payload: Dict[str, Any]
    log_id: int
    actor: str = "system"
