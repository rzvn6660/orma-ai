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
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "type": n.type,
            "read": n.read,
            "data": n.data,
            "created_at": n.created_at.isoformat()
        } for n in notifications
    ]

@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks a single notification as read.
    """
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not notification:
        return {"status": "not_found"}
    
    notification.read = True
    db.commit()
    return {"status": "success"}

@router.put("/read-all")
def mark_all_notifications_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks all notifications as read for the user.
    """
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read == False).update({"read": True})
    db.commit()
    return {"status": "success"}
