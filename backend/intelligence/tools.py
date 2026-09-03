import datetime
import pytz
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
from models.user import User

logger = logging.getLogger(__name__)

def parse_time_to_minutes(time_str: str) -> Optional[int]:
    """Parses a time string (e.g. '08:00 AM', '2:04 PM', '14:30', '8:00pm') to minutes from midnight (0..1439)."""
    if not time_str:
        return None
    s = time_str.strip().upper()
    is_pm = "PM" in s
    is_am = "AM" in s
    clean = s.replace("AM", "").replace("PM", "").strip()
    parts = clean.split(":")
    if len(parts) >= 2:
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            return hour * 60 + minute
        except (ValueError, IndexError):
            return None
    elif len(parts) == 1:
        try:
            hour = int(parts[0])
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            return hour * 60
        except ValueError:
            return None
    return None

def get_med_times(med: MedicineReminder) -> List[str]:
    raw = med.reminder_time or ""
    return [t.strip() for t in raw.split(",") if t.strip()]

def med_applies_on_date(med: MedicineReminder, target_date: datetime.date) -> bool:
    freq = (med.frequency or "").strip().lower()
    if not freq or any(f in freq for f in ["daily", "once daily", "twice daily", "three times daily", "thrice daily"]):
        return True
    if freq.startswith("weekly"):
        day_name = target_date.strftime("%A").lower()
        return day_name in freq
    if freq.startswith("monthly"):
        try:
            target_day = int(freq.split("-")[1].strip())
            return target_date.day == target_day
        except:
            return False
    if "alternate" in freq:
        ref_date = med.created_at.date() if med.created_at else target_date
        return (target_date.toordinal() - ref_date.toordinal()) % 2 == 0
    if "sos" in freq or "as needed" in freq:
        return False
    return True

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
        taken = [m for m in filtered if m.taken_status]
        pending = [m for m in filtered if not m.taken_status]
        
        return {
            "tool": "medication_schedule",
            "time_period": time_period,
            "count": len(filtered),
            "taken_count": len(taken),
            "pending_count": len(pending),
            "all_taken": len(pending) == 0 and len(filtered) > 0,
            "medications": [
                {
                    "id": m.id,
                    "name": m.medicine_name,
                    "dosage": m.dosage or "standard dose",
                    "scheduled_time": m.reminder_time,
                    "taken": m.taken_status,
                    "status": "TAKEN" if m.taken_status else "PENDING"
                } for m in filtered
            ]
        }

    @staticmethod
    def get_next_medication(db: Session, user_id: str, query_text: str = "", language: str = "en") -> Dict[str, Any]:
        user_str = str(user_id)
        # 1. Resolve User Timezone
        user_obj = db.query(User).filter(User.id == user_str).first()
        tz_name = (user_obj.timezone if user_obj and user_obj.timezone else "UTC").strip()
        try:
            user_tz = pytz.timezone(tz_name)
        except Exception:
            user_tz = pytz.utc

        now_local = datetime.datetime.now(user_tz)
        local_today = now_local.date()
        now_minutes = now_local.hour * 60 + now_local.minute

        # 2. Retrieve all medicines for this specific subject/user
        medicines = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()

        if not medicines:
            return {
                "status": "no_medicines",
                "medication": None,
                "response_text": HealthcareTools._format_next_med_response(
                    status="no_medicines", med_name="", dosage="", scheduled_time="", day="", language=language
                )
            }

        # 3. Determine today's scheduled doses
        today_meds = [m for m in medicines if med_applies_on_date(m, local_today)]
        
        today_pending_doses = []
        today_taken_doses = []

        for m in today_meds:
            times = get_med_times(m) or ["Standard time"]
            is_taken = bool(m.taken_status)
            if is_taken and m.taken_at:
                try:
                    taken_local = m.taken_at.replace(tzinfo=pytz.utc).astimezone(user_tz).date() if m.taken_at.tzinfo is None else m.taken_at.astimezone(user_tz).date()
                    if taken_local != local_today:
                        is_taken = False
                except Exception:
                    pass

            for t_str in times:
                mins = parse_time_to_minutes(t_str)
                mins_val = mins if mins is not None else 9999
                dose_info = {
                    "id": m.id,
                    "name": m.medicine_name,
                    "dosage": m.dosage or "standard dose",
                    "scheduled_time": t_str,
                    "minutes": mins_val,
                    "is_taken": is_taken,
                    "medicine": m
                }
                if is_taken:
                    today_taken_doses.append(dose_info)
                else:
                    today_pending_doses.append(dose_info)

        # 4. If there are pending doses today:
        if today_pending_doses:
            today_pending_doses.sort(key=lambda d: d["minutes"])
            # Prefer doses upcoming today (at or after current time), else earliest pending
            upcoming = [d for d in today_pending_doses if d["minutes"] >= now_minutes]
            chosen_dose = upcoming[0] if upcoming else today_pending_doses[0]

            return {
                "status": "found_today",
                "medication": chosen_dose,
                "pending_count": len(today_pending_doses),
                "taken_count": len(today_taken_doses),
                "response_text": HealthcareTools._format_next_med_response(
                    status="found_today",
                    med_name=chosen_dose["name"],
                    dosage=chosen_dose["dosage"],
                    scheduled_time=chosen_dose["scheduled_time"],
                    day="today",
                    language=language
                )
            }

        # 5. No pending doses remain today
        had_doses_today = len(today_taken_doses) > 0

        # Look for next future recurring occurrence in the next 14 days
        next_future_dose = None
        next_future_day_label = ""

        for day_offset in range(1, 15):
            future_date = local_today + datetime.timedelta(days=day_offset)
            matching_future_meds = [m for m in medicines if med_applies_on_date(m, future_date)]
            if matching_future_meds:
                future_doses = []
                for fm in matching_future_meds:
                    for ft in get_med_times(fm) or ["Standard time"]:
                        fm_mins = parse_time_to_minutes(ft)
                        future_doses.append({
                            "id": fm.id,
                            "name": fm.medicine_name,
                            "dosage": fm.dosage or "standard dose",
                            "scheduled_time": ft,
                            "minutes": fm_mins if fm_mins is not None else 9999
                        })
                if future_doses:
                    future_doses.sort(key=lambda d: d["minutes"])
                    next_future_dose = future_doses[0]
                    next_future_day_label = "tomorrow" if day_offset == 1 else future_date.strftime("%A")
                    break

        if had_doses_today:
            if next_future_dose:
                return {
                    "status": "all_taken_today_next_future",
                    "medication": next_future_dose,
                    "day_label": next_future_day_label,
                    "response_text": HealthcareTools._format_next_med_response(
                        status="all_taken_today_next_future",
                        med_name=next_future_dose["name"],
                        dosage=next_future_dose["dosage"],
                        scheduled_time=next_future_dose["scheduled_time"],
                        day=next_future_day_label,
                        language=language
                    )
                }
            else:
                return {
                    "status": "all_taken_today_no_future",
                    "medication": None,
                    "response_text": HealthcareTools._format_next_med_response(
                        status="all_taken_today_no_future",
                        med_name="", dosage="", scheduled_time="", day="", language=language
                    )
                }
        else:
            if next_future_dose:
                return {
                    "status": "none_today_next_future",
                    "medication": next_future_dose,
                    "day_label": next_future_day_label,
                    "response_text": HealthcareTools._format_next_med_response(
                        status="none_today_next_future",
                        med_name=next_future_dose["name"],
                        dosage=next_future_dose["dosage"],
                        scheduled_time=next_future_dose["scheduled_time"],
                        day=next_future_day_label,
                        language=language
                    )
                }
            else:
                return {
                    "status": "no_medicines",
                    "medication": None,
                    "response_text": HealthcareTools._format_next_med_response(
                        status="no_medicines",
                        med_name="", dosage="", scheduled_time="", day="", language=language
                    )
                }

    @staticmethod
    def _format_next_med_response(status: str, med_name: str, dosage: str, scheduled_time: str, day: str, language: str = "en") -> str:
        lang = (language or "en").lower()

        # Malayalam
        if lang.startswith("ml"):
            if status == "found_today":
                return f"നിങ്ങളുടെ അടുത്ത മരുന്ന് {med_name} ({dosage}), സമയം {scheduled_time}."
            if status == "all_taken_today_next_future":
                day_ml = "നാളെ" if day == "tomorrow" else day
                return f"ഇന്നത്തെ മരുന്നുകളെല്ലാം കഴിച്ചു കഴിഞ്ഞു. അടുത്ത മരുന്ന് {day_ml} {scheduled_time}-ന് {med_name} ({dosage}) ആണ്."
            if status == "all_taken_today_no_future":
                return "ഇന്നത്തെ മരുന്നുകളെല്ലാം കഴിച്ചു കഴിഞ്ഞു. ഇനി ഇന്ന് മരുന്നുകൾ ഒന്നുമില്ല."
            if status == "none_today_next_future":
                day_ml = "നാളെ" if day == "tomorrow" else day
                return f"ഇന്ന് മരുന്നുകൾ ഒന്നുമില്ല. അടുത്ത മരുന്ന് {day_ml} {scheduled_time}-ന് {med_name} ({dosage}) ആണ്."
            return "നിങ്ങളുടെ റെക്കോർഡുകളിൽ മരുന്നുകളൊന്നും ഷെഡ്യൂൾ ചെയ്തിട്ടില്ല."

        # Hindi
        if lang.startswith("hi"):
            if status == "found_today":
                return f"आपकी अगली दवा {med_name} ({dosage}) है जो {scheduled_time} के लिए निर्धारित है।"
            if status == "all_taken_today_next_future":
                day_hi = "कल" if day == "tomorrow" else day
                return f"आज की सभी दवाएं पूरी हो चुकी हैं। आपकी अगली दवा {day_hi} {scheduled_time} बजे {med_name} ({dosage}) है।"
            if status == "all_taken_today_no_future":
                return "आज के लिए कोई और दवा निर्धारित नहीं है। आज की सभी दवाएं ली जा चुकी हैं।"
            if status == "none_today_next_future":
                day_hi = "कल" if day == "tomorrow" else day
                return f"आज के लिए कोई दवा निर्धारित नहीं है। आपकी अगली दवा {day_hi} {scheduled_time} बजे {med_name} ({dosage}) है।"
            return "आपके रिकॉर्ड में वर्तमान में कोई दवा निर्धारित नहीं है।"

        # Arabic
        if lang.startswith("ar"):
            if status == "found_today":
                return f"دواؤك التالي هو {med_name} ({dosage}) المجدول في {scheduled_time}."
            if status == "all_taken_today_next_future":
                day_ar = "غداً" if day == "tomorrow" else day
                return f"لقد تناولت جميع أدوية اليوم. دواؤك التالي {day_ar} في {scheduled_time} هو {med_name} ({dosage})."
            if status == "all_taken_today_no_future":
                return "ليس لديك أي أدوية أخرى مجدولة لهذا اليوم. لقد تناولت جميع أدويتك."
            if status == "none_today_next_future":
                day_ar = "غداً" if day == "tomorrow" else day
                return f"ليس لديك أدوية مجدولة اليوم. دواؤك التالي {day_ar} في {scheduled_time} هو {med_name} ({dosage})."
            return "ليس لديك أي أدوية مجدولة حالياً في سجلاتك."

        # Default: English
        if status == "found_today":
            return f"Your next medicine is {med_name} ({dosage}) scheduled for {scheduled_time}."
        if status == "all_taken_today_next_future":
            if day == "tomorrow":
                return f"You have no more medicines scheduled for today. Your next medicine is {med_name} ({dosage}) scheduled for tomorrow at {scheduled_time}."
            return f"You have no more medicines scheduled for today. Your next medicine is {med_name} ({dosage}) scheduled for {day} at {scheduled_time}."
        if status == "all_taken_today_no_future":
            return "You have no more medicines scheduled for today. All scheduled medicines have been taken."
        if status == "none_today_next_future":
            if day == "tomorrow":
                return f"You have no medicines scheduled for today. Your next medicine is {med_name} ({dosage}) scheduled for tomorrow at {scheduled_time}."
            return f"You have no medicines scheduled for today. Your next medicine is {med_name} ({dosage}) scheduled for {day} at {scheduled_time}."
        return "You have no medicines currently scheduled in your records."

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
