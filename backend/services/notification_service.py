from sqlalchemy.orm import Session
from models.notification import Notification
from models.user import User, CaregiverRelationship
from services.websocket_manager import manager
from services.notification_preference_service import get_user_notification_preferences
import asyncio

async def dispatch_notification(db: Session, elder_id: str, title: str, message: str, priority: str = "medium"):
    """
    Sends an alert to all approved linked caregivers, enforcing recipient preference settings.
    """
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == elder_id,
        CaregiverRelationship.status == "approved"
    ).all()
    
    for rel in rels:
        cg_user = db.query(User).filter(User.id == rel.caregiver_id).first()
        if cg_user:
            prefs = get_user_notification_preferences(db, cg_user)
            t_lower = title.lower()
            m_lower = message.lower()
            if "missed" in t_lower or "miss" in m_lower:
                if not prefs.missed_medication_alerts:
                    continue
            elif "adherence" in t_lower or "summary" in m_lower:
                if not prefs.medication_adherence_summary:
                    continue
            elif "reminder" in t_lower:
                if not prefs.medication_reminder_notifications:
                    continue

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
