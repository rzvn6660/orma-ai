import logging
from sqlalchemy.orm import Session
from memory.memory_models import OCMEAudit
from typing import Optional

logger = logging.getLogger(__name__)

class AuditEngine:
    """
    Tracks all memory changes (created, updated, merged, pinned, shared, explained, deleted, archived)
    with timestamps and source.
    """
    
    def log_action(self, db: Session, memory_id: int, action: str, source: str = "AI", details: Optional[str] = None):
        """
        Creates an audit record.
        """
        logger.info(f"[AuditEngine] Auditing action '{action}' for memory {memory_id} by {source}")
        
        audit_entry = OCMEAudit(
            memory_id=memory_id,
            action=action,
            source=source,
            details=details
        )
        db.add(audit_entry)
        db.commit()

audit_engine = AuditEngine()
