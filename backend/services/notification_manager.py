import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
import datetime

logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Centralized Notification Manager for ORMA AI.
    Handles routing of reminders and alerts to appropriate channels.
    Prepares the architecture for Firebase, WhatsApp, SMS, Email, Android, and iOS.
    """
    
    def __init__(self):
        self.channels = ['in_app', 'browser_push', 'voice'] # Active channels
        # Future channels placeholder
        self.future_channels = ['firebase', 'sms', 'whatsapp', 'email', 'smartwatch', 'alexa', 'google_home']
        
    async def notify_user(self, db: Optional[Session] = None, reminder: Any = None, channels=None):
        """
        Dispatches a reminder to the requested channels.
        If no channels specified, uses default active channels.
        Allows db to be None for background threads/async execution.
        """
        if channels is None:
            channels = self.channels
            
        rem_id = getattr(reminder, "id", None)
        logger.info(f"NotificationManager routing reminder {rem_id} via channels: {channels}")
        
        # 1. Log Reminder Sent history
        self.log_reminder_event(db, rem_id, "Reminder Sent")
        
        # 2. Dispatch to In-App / Browser Push (currently handled via frontend polling, 
        # but architecture routes it through here for future WebSocket direct push)
        if 'in_app' in channels or 'browser_push' in channels or 'voice' in channels:
            from services.scheduler_service import pending_reminders
            # Push to the queue for the frontend to consume
            if not any(r['id'] == rem_id for r in pending_reminders):
                is_health_event = hasattr(reminder, 'event_type') and getattr(reminder, 'event_type', 'medicine') != 'medicine'
                raw_title = getattr(reminder, 'title', None) if is_health_event else getattr(reminder, 'medicine_name', None)
                clean_name = raw_title.strip() if (raw_title and isinstance(raw_title, str)) else None
                desc = getattr(reminder, 'description', None) if is_health_event else getattr(reminder, 'dosage', None)
                event_type = getattr(reminder, 'event_type', 'medicine') if is_health_event else 'medicine'
                elder_id = getattr(reminder, 'elder_id', None) or getattr(reminder, 'subject_id', None)
                subject_id = getattr(reminder, 'subject_id', None) or getattr(reminder, 'elder_id', None)
                scheduled_time = getattr(reminder, 'reminder_time', None)
                
                msg_en = f"It's time for your {clean_name}." if clean_name else "It's time to take your medicine."
                msg_ml = f"ഇപ്പോൾ {clean_name} സമയം ആയി." if clean_name else "നിങ്ങളുടെ മരുന്ന് കഴിക്കാനുള്ള സമയമാണ്."

                pending_reminders.append({
                    "id": rem_id,
                    "event_type": event_type,
                    "title": clean_name,
                    "description": desc,
                    "medicine_name": clean_name, # Authoritative structured medicine name
                    "dosage": desc,
                    "scheduled_time": scheduled_time,
                    "elder_id": elder_id,
                    "subject_id": subject_id,
                    "message_en": msg_en,
                    "message_ml": msg_ml
                })
                
        # 3. Future Channel Placeholders
        if 'firebase' in channels:
            self._send_firebase_push(reminder)
        if 'sms' in channels:
            self._send_sms(reminder)
        if 'whatsapp' in channels:
            self._send_whatsapp(reminder)
        if 'email' in channels:
            self._send_email(reminder)

    async def escalate_missed_reminder(self, db: Optional[Session] = None, reminder: Any = None):
        """
        Escalation Engine: Triggered when a medicine is still pending after the configured delay.
        Notifies caregivers. Safely delegates session ownership to dispatch_notification if db is None.
        """
        rem_id = getattr(reminder, "id", None)
        self.log_reminder_event(db, rem_id, "Caregiver Notified")
        
        from services.notification_service import dispatch_notification
        elder_id = getattr(reminder, "elder_id", None) or getattr(reminder, "subject_id", None)
        rem_time = getattr(reminder, "reminder_time", "")
        med_name = getattr(reminder, "medicine_name", getattr(reminder, "title", "medicine"))

        # Use existing dispatch to send to caregiver websocket
        await dispatch_notification(
            db=db,
            elder_id=elder_id,
            title="Missed Medication",
            message=f"The patient has not confirmed today's {rem_time} {med_name} medicine.",
            priority="high"
        )
        
    def log_reminder_event(self, db: Optional[Session], reminder_id: int, event_type: str):
        """
        Reminder history logger for analytics.
        Types: Reminder Sent, Reminder Opened, Reminder Ignored, Taken, Skipped, Reminded Again, Caregiver Notified
        """
        # Note: In a production app this would insert into a ReminderHistory table.
        # For current architecture readiness, we log it and update the medicine record if applicable.
        logger.info(f"ReminderHistory - ID: {reminder_id} | Event: {event_type} | Time: {datetime.datetime.utcnow()}")
        
    # --- Future Integration Stubs ---
    
    def _send_firebase_push(self, reminder):
        pass
        
    def _send_sms(self, reminder):
        pass
        
    def _send_whatsapp(self, reminder):
        pass
        
    def _send_email(self, reminder):
        pass

notification_manager = NotificationManager()
