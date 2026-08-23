from sqlalchemy.orm import Session
from models.user import User, NotificationPreferences
from datetime import datetime

def get_user_notification_preferences(db: Session, user: User) -> NotificationPreferences:
    """
    Retrieves or creates default notification preferences for a user based on their role.
    
    Default Matrix:
    - Elderly:
        medication_reminder_notifications: True (ON)
        medication_spoken_alerts: True (ON)
        missed_medication_alerts: True (ON)
        medication_adherence_summary: True (ON)
        reminder_language: "en-IN"
        voice_language: "auto"
    - Caregiver:
        medication_reminder_notifications: False (OFF)
        medication_spoken_alerts: False (OFF)
        missed_medication_alerts: True (ON)
        medication_adherence_summary: True (ON)
        reminder_language: "en-IN"
        voice_language: "auto"
    """
    prefs = db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user.id).first()
    if not prefs:
        is_caregiver = (user.role == "caregiver")
        prefs = NotificationPreferences(
            user_id=user.id,
            medication_reminder_notifications=not is_caregiver,
            medication_spoken_alerts=not is_caregiver,
            missed_medication_alerts=True,
            medication_adherence_summary=True,
            reminder_language="en-IN",
            voice_language="auto"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    else:
        dirty = False
        if not prefs.reminder_language:
            prefs.reminder_language = "en-IN"
            dirty = True
        if not prefs.voice_language:
            prefs.voice_language = "auto"
            dirty = True
        if dirty:
            db.commit()
            db.refresh(prefs)
            
    return prefs

def update_user_notification_preferences(db: Session, user: User, updates: dict) -> NotificationPreferences:
    """
    Updates specified notification preferences for a user.
    """
    prefs = get_user_notification_preferences(db, user)
    
    for key, value in updates.items():
        if value is not None and hasattr(prefs, key):
            if key in ["reminder_language", "voice_language"]:
                setattr(prefs, key, str(value))
            else:
                setattr(prefs, key, bool(value))
            
    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs
