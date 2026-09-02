import logging
import asyncio
import os
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.owe import WorkflowAuditLog, ApprovalRequest
from models.user import User, CaregiverRelationship
from dependencies import get_current_user, SECRET_KEY, ALGORITHM
from workflows.approval_manager import approval_manager
from workflows.event_bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/owe", tags=["Action & Workflow Engine"])

def _verify_user_access(current_user: User, target_user_id: str, db: Session):
    target_str = str(target_user_id)
    if str(current_user.id) == target_str:
        return True
    if current_user.role == "caregiver":
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.elder_id == target_str,
            CaregiverRelationship.status == "approved"
        ).first()
        if rel:
            return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. You are not authorized for this workflow action."
    )

@router.get("/audit")
def get_audit_logs(limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves workflow audit logs for the authenticated user or linked elders."""
    if current_user.role == "caregiver":
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.status == "approved"
        ).all()
        allowed_ids = [str(r.elder_id) for r in rels] + [str(current_user.id)]
        return db.query(WorkflowAuditLog).filter(
            WorkflowAuditLog.user_id.in_(allowed_ids)
        ).order_by(WorkflowAuditLog.created_at.desc()).limit(limit).all()
    else:
        return db.query(WorkflowAuditLog).filter(
            WorkflowAuditLog.user_id == str(current_user.id)
        ).order_by(WorkflowAuditLog.created_at.desc()).limit(limit).all()

@router.get("/approvals")
def get_pending_approvals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves pending approvals for authenticated user or linked subjects."""
    if current_user.role == "caregiver":
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.status == "approved"
        ).all()
        allowed_ids = [r.elder_id for r in rels] + [current_user.id]
        return db.query(ApprovalRequest).filter(
            ApprovalRequest.user_id.in_(allowed_ids),
            ApprovalRequest.status == "pending"
        ).all()
    else:
        return db.query(ApprovalRequest).filter(
            ApprovalRequest.user_id == current_user.id,
            ApprovalRequest.status == "pending"
        ).all()

@router.post("/approvals/{request_id}/resolve")
async def resolve_approval(request_id: int, resolution: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    status_val = resolution.get("status")
    if status_val not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    _verify_user_access(current_user, str(req.user_id), db)

    success = await approval_manager.resolve_approval(db, request_id, status_val)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    return {"status": "success", "message": f"Request {status_val}"}

@router.post("/test-trigger")
async def test_trigger_workflow(event_name: str, action: str = "create", current_user: User = Depends(get_current_user)):
    """Developer endpoint to trigger a workflow event — disabled in production."""
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(status_code=404, detail="Test endpoints are disabled in production.")
    await event_bus.publish(event_name, {
        "event_name": event_name,
        "action": action,
        "user_id": current_user.id,
        "details": "Triggered from API"
    })
    return {"status": "success", "message": f"Triggered {event_name}"}

@router.get("/events")
async def sse_events(request: Request, db: Session = Depends(get_db)):
    """
    Authenticated Server-Sent Events endpoint for dashboard automatic updates.
    """
    token = request.query_params.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required for SSE stream.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user or (payload.get("ver") and payload.get("ver") != user.token_version):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or revoked session")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def event_generator():
        queue = asyncio.Queue()
        
        async def on_event(payload):
            # Only push events relevant to user
            if str(payload.get("user_id", "")) in [str(user_id), ""]:
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
