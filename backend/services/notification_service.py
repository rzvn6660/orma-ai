from sqlalchemy.orm import Session
from models.notification import Notification
from services.websocket_manager import manager
from models.user import CaregiverRelationship
import asyncio

async def dispatch_notification(db: Session, elder_id: str, title: str, message: str, priority: str = "medium"):
    """
    Sends an alert to all linked caregivers.
    Prepares architecture for FCM/OneSignal push notifications.
    """
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == elder_id,
        CaregiverRelationship.status == "approved"
    ).all()
    
    for rel in rels:
        notif = Notification(
            caregiver_id=rel.caregiver_id,
            elder_id=elder_id,
            title=title,
            message=message,
            priority=priority
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        
        payload = {
            "type": "notification",
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "priority": notif.priority,
            "created_at": notif.created_at.isoformat()
        }
        await manager.send_personal_message(payload, rel.caregiver_id)
        
        # Future architecture endpoint:
        # await firebase_push_service.send_to_user(rel.caregiver_id, payload)
