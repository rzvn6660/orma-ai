from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.notification import Notification
from models.user import User
from dependencies import get_current_user, SECRET_KEY, ALGORITHM
from services.websocket_manager import manager
from services.notification_preference_service import (
    get_user_notification_preferences, 
    update_user_notification_preferences
)
import jwt

router = APIRouter()

class NotificationPreferencesPayload(BaseModel):
    medication_reminder_notifications: Optional[bool] = None
    medication_spoken_alerts: Optional[bool] = None
    missed_medication_alerts: Optional[bool] = None
    medication_adherence_summary: Optional[bool] = None
    reminder_language: Optional[str] = None
    voice_language: Optional[str] = None

@router.get("/preferences")
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = get_user_notification_preferences(db, current_user)
    return {
        "medication_reminder_notifications": prefs.medication_reminder_notifications,
        "medication_spoken_alerts": prefs.medication_spoken_alerts,
        "missed_medication_alerts": prefs.missed_medication_alerts,
        "medication_adherence_summary": prefs.medication_adherence_summary,
        "reminder_language": getattr(prefs, "reminder_language", "en-IN") or "en-IN",
        "voice_language": getattr(prefs, "voice_language", "auto") or "auto"
    }

@router.put("/preferences")
async def update_preferences(
    payload: NotificationPreferencesPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updates = payload.dict(exclude_unset=True)
    prefs = update_user_notification_preferences(db, current_user, updates)
    res = {
        "medication_reminder_notifications": prefs.medication_reminder_notifications,
        "medication_spoken_alerts": prefs.medication_spoken_alerts,
        "missed_medication_alerts": prefs.missed_medication_alerts,
        "medication_adherence_summary": prefs.medication_adherence_summary,
        "reminder_language": getattr(prefs, "reminder_language", "en-IN") or "en-IN",
        "voice_language": getattr(prefs, "voice_language", "auto") or "auto"
    }
    
    await manager.send_personal_message({
        "type": "notification_preferences_updated",
        "preferences": res
    }, current_user.id)
    
    return res

@router.get("/")
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieves all notification history for the authenticated user.
    """
    from sqlalchemy import or_
    notifications = db.query(Notification).filter(
        or_(
            Notification.caregiver_id == current_user.id,
            Notification.elder_id == current_user.id,
            Notification.subject_id == current_user.id,
            Notification.actor_id == current_user.id
        )
    ).order_by(Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.message,
            "message": n.message,
            "priority": n.priority,
            "read": n.is_read,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None
        } for n in notifications
    ]

@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks a single notification as read.
    """
    from sqlalchemy import or_
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        or_(
            Notification.caregiver_id == current_user.id,
            Notification.elder_id == current_user.id,
            Notification.subject_id == current_user.id,
            Notification.actor_id == current_user.id
        )
    ).first()
    if not notification:
        return {"status": "not_found"}
    
    notification.is_read = True
    db.commit()
    return {"status": "success"}

@router.put("/read-all")
def mark_all_notifications_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks all notifications as read for the user.
    """
    from sqlalchemy import or_
    db.query(Notification).filter(
        or_(
            Notification.caregiver_id == current_user.id,
            Notification.elder_id == current_user.id,
            Notification.subject_id == current_user.id,
            Notification.actor_id == current_user.id
        ),
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "success"}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Authenticated WebSocket endpoint for real-time notification streams.
    Strictly verifies JWT authentication, user identity binding, and token versioning.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_sub = payload.get("sub")
        if not token_sub or str(token_sub) != str(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = db.query(User).filter(User.id == token_sub).first()
        if not user or not getattr(user, "is_active", True):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check token version revocation
        token_ver = payload.get("ver")
        if getattr(user, "token_version", None) is not None:
            if token_ver is None or token_ver != user.token_version:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Handle incoming ping / messages with max size
            data = await websocket.receive_text()
            if len(data) > 4096:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                break
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)
