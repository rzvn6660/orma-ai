from sqlalchemy.orm import Session
from models.notification import Notification
from models.user import User, CaregiverRelationship
from services.websocket_manager import manager
from services.notification_preference_service import get_user_notification_preferences
from datetime import datetime, timedelta
import asyncio

async def dispatch_notification(db: Session, elder_id: str, title: str, message: str, priority: str = "medium"):
    """
    Sends an alert to the elder and all approved linked caregivers, enforcing recipient preference settings
    and deduplicating identical notifications within a 15-minute window.
    """
    # 1. Deduplication check: prevent duplicate notification records in DB.
    # For missed medication occurrences, enforce calendar-day scoping (one notification record per occurrence per day).
    # For other transient notifications, enforce a 15-minute deduplication window.
    t_lower_check = title.lower()
    if "missed" in t_lower_check:
        recent_cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        recent_cutoff = datetime.utcnow() - timedelta(minutes=15)

    elder_filters = [
        Notification.elder_id == elder_id,
        Notification.title == title,
        Notification.created_at >= recent_cutoff
    ]
    if "missed" in t_lower_check:
        elder_filters.append(Notification.message == message)

    existing_elder_notif = db.query(Notification).filter(*elder_filters).first()

    if not existing_elder_notif:
        # Create persistent notification record for the elder
        elder_notif = Notification(
            elder_id=elder_id,
            subject_id=elder_id,
            title=title,
            message=message,
            priority=priority,
            is_read=False
        )
        db.add(elder_notif)
        db.commit()
        db.refresh(elder_notif)

        # Broadcast in real-time to elder's websocket stream
        payload = {
            "type": "notification",
            "id": elder_notif.id,
            "title": elder_notif.title,
            "message": elder_notif.message,
            "priority": elder_notif.priority,
            "created_at": elder_notif.created_at.isoformat()
        }
        await manager.send_personal_message(payload, elder_id)

    # 2. Dispatch to linked caregivers (with caregiver preference checks)
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == elder_id,
        CaregiverRelationship.status == "approved"
    ).all()

    for rel in rels:
        # Check deduplication for caregiver
        cg_filters = [
            Notification.caregiver_id == rel.caregiver_id,
            Notification.elder_id == elder_id,
            Notification.title == title,
            Notification.created_at >= recent_cutoff
        ]
        if "missed" in t_lower_check:
            cg_filters.append(Notification.message == message)

        existing_cg = db.query(Notification).filter(*cg_filters).first()
        if existing_cg:
            continue

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

        cg_notif = Notification(
            caregiver_id=rel.caregiver_id,
            elder_id=elder_id,
            subject_id=elder_id,
            title=title,
            message=message,
            priority=priority,
            is_read=False
        )
        db.add(cg_notif)
        db.commit()
        db.refresh(cg_notif)

        cg_payload = {
            "type": "notification",
            "id": cg_notif.id,
            "title": cg_notif.title,
            "message": cg_notif.message,
            "priority": cg_notif.priority,
            "created_at": cg_notif.created_at.isoformat()
        }
        await manager.send_personal_message(cg_payload, rel.caregiver_id)
