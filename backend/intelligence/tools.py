import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
from models.user import User

logger = logging.getLogger(__name__)

def is_med_in_time_period(med: MedicineReminder, period: str) -> bool:
    """Helper to check if a medicine reminder falls within a given time period."""
    if not period or period in ["today", "all"]:
        return True
        
    rem_time = (med.reminder_time or "").upper().strip()
    hour = None
    if "AM" in rem_time:
        try: hour = int(rem_time.split(":")[0]) % 12
        except: pass
    elif "PM" in rem_time:
        try: hour = (int(rem_time.split(":")[0]) % 12) + 12
        except: pass
    elif ":" in rem_time:
        try: hour = int(rem_time.split(":")[0])
        except: pass

    if hour is not None:
        if period == "morning" and 5 <= hour < 12: return True
        if period == "afternoon" and 12 <= hour < 17: return True
        if period == "evening" and 17 <= hour < 21: return True
        if period == "night" and (hour >= 21 or hour < 5): return True
        return False

    low_t = rem_time.lower()
    if period == "morning" and ("am" in low_t or "morning" in low_t or "8" in low_t or "9" in low_t or "10" in low_t): return True
    if period == "afternoon" and ("lunch" in low_t or "12" in low_t or "13" in low_t or "14" in low_t): return True
    if period == "night" and ("pm" in low_t or "night" in low_t or "21" in low_t or "22" in low_t or "20" in low_t): return True
    return True

class HealthcareTools:
    """
    Controlled backend tools for database context retrieval (Requirement #4 & #5).
    Provides authoritative database facts without exposing raw DB structures directly to LLMs.
    """
    
    @staticmethod
    def get_medication_schedule(db: Session, user_id: str, time_period: str = "today") -> Dict[str, Any]:
        user_str = str(user_id)
        medicines = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()
        
        filtered = [m for m in medicines if is_med_in_time_period(m, time_period)]
        
        return {
            "tool": "medication_schedule",
            "time_period": time_period,
            "count": len(filtered),
            "medications": [
                {
                    "id": m.id,
                    "name": m.medicine_name,
                    "dosage": m.dosage or "standard dose",
                    "scheduled_time": m.reminder_time,
                    "taken": m.taken_status
                } for m in filtered
            ]
        }

    @staticmethod
    def get_medication_status(db: Session, user_id: str, time_period: str = "today") -> Dict[str, Any]:
        user_str = str(user_id)
        medicines = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()
        
        filtered = [m for m in medicines if is_med_in_time_period(m, time_period)]
        taken = [m for m in filtered if m.taken_status]
        pending = [m for m in filtered if not m.taken_status]
        
        return {
            "tool": "medication_status",
            "time_period": time_period,
            "total_count": len(filtered),
            "taken_count": len(taken),
            "pending_count": len(pending),
            "all_taken": len(pending) == 0 and len(filtered) > 0,
            "medications": [
                {
                    "id": m.id,
                    "name": m.medicine_name,
                    "dosage": m.dosage or "standard dose",
                    "scheduled_time": m.reminder_time,
                    "status": "TAKEN" if m.taken_status else ("SNOOZED" if m.adherence_pattern_flags == "snoozed" else "PENDING")
                } for m in filtered
            ]
        }

    @staticmethod
    def get_daily_adherence(db: Session, user_id: str) -> Dict[str, Any]:
        user_str = str(user_id)
        medicines = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()
        
        total = len(medicines)
        taken = sum(1 for m in medicines if m.taken_status)
        pending = total - taken
        pct = int((taken / total) * 100) if total > 0 else 100
        
        return {
            "tool": "daily_adherence",
            "total_scheduled": total,
            "taken_count": taken,
            "pending_count": pending,
            "adherence_percentage": pct,
            "summary_text": f"Taken {taken} of {total} scheduled medicines ({pct}% adherence)."
        }

    @staticmethod
    def get_calendar_events(db: Session, user_id: str) -> Dict[str, Any]:
        user_str = str(user_id)
        events = db.query(HealthEvent).filter(
            (HealthEvent.elder_id == user_str) | (HealthEvent.subject_id == user_str)
        ).all()
        
        return {
            "tool": "calendar_events",
            "count": len(events),
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "type": e.event_type,
                    "date": e.event_date,
                    "time": e.reminder_time,
                    "location": e.location
                } for e in events
            ]
        }

    @staticmethod
    def get_user_profile(db: Session, user_id: str) -> Dict[str, Any]:
        user_str = str(user_id)
        u = db.query(User).filter(User.id == user_str).first()
        if not u and user_str.isdigit():
            u = db.query(User).filter(User.id == int(user_str)).first()
            
        name = u.name if u else "User"
        role = u.role if u else "elderly"
        timezone = u.timezone if u else "UTC"
        
        return {
            "tool": "user_profile",
            "name": name,
            "role": role,
            "timezone": timezone
        }

healthcare_tools = HealthcareTools()
