import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.owe import WorkflowAuditLog, ApprovalRequest
from workflows.approval_manager import approval_manager
from workflows.event_bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/owe", tags=["Action & Workflow Engine"])

@router.get("/audit")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(WorkflowAuditLog).order_by(WorkflowAuditLog.created_at.desc()).limit(limit).all()

@router.get("/approvals")
def get_pending_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").all()

@router.post("/approvals/{request_id}/resolve")
async def resolve_approval(request_id: int, resolution: dict, db: Session = Depends(get_db)):
    status = resolution.get("status")
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    success = await approval_manager.resolve_approval(db, request_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    return {"status": "success", "message": f"Request {status}"}

@router.post("/test-trigger")
async def test_trigger_workflow(event_name: str, action: str = "create"):
    """Developer endpoint to trigger a workflow event."""
    await event_bus.publish(event_name, {
        "event_name": event_name,
        "action": action,
        "details": "Triggered from API"
    })
    return {"status": "success", "message": f"Triggered {event_name}"}

@router.get("/events")
async def sse_events(request: Request):
    """
    Server-Sent Events endpoint for dashboard automatic updates.
    """
    async def event_generator():
        queue = asyncio.Queue()
        
        async def on_event(payload):
            await queue.put(payload)
            
        event_bus.subscribe("WorkflowCompleted", on_event)
        event_bus.subscribe("ApprovalResolved", on_event)
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                payload = await queue.get()
                yield f"data: {str(payload)}\n\n"
        except asyncio.CancelledError:
            pass
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
