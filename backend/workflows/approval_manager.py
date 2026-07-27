import logging
from sqlalchemy.orm import Session
from models.owe import ApprovalRequest, WorkflowAuditLog
from workflows.event_bus import event_bus
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ApprovalManager:
    """
    Support actions requiring confirmation before execution.
    Never automatically modify medications, delete memories, etc.
    """
    
    def request_approval(self, db: Session, log_id: int, action_type: str, payload: Dict[str, Any]) -> ApprovalRequest:
        logger.info(f"[ApprovalManager] Requesting approval for {action_type}")
        
        req = ApprovalRequest(
            workflow_log_id=log_id,
            action_type=action_type,
            payload=payload,
            status="pending"
        )
        db.add(req)
        
        # Update workflow log status
        wf_log = db.query(WorkflowAuditLog).filter(WorkflowAuditLog.id == log_id).first()
        if wf_log:
            wf_log.status = "pending_approval"
            
        db.commit()
        db.refresh(req)
        
        return req
        
    async def resolve_approval(self, db: Session, request_id: int, status: str):
        """
        status: approved or rejected
        Resumes workflow logic or cancels it.
        """
        req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return False
            
        req.status = status
        db.commit()
        
        # In a full robust engine, we'd hydrate the workflow context and resume execution here.
        # For Sprint 3.6, we will broadcast the resolution.
        await event_bus.publish("ApprovalResolved", {"request_id": request_id, "status": status, "payload": req.payload})
        return True

approval_manager = ApprovalManager()
