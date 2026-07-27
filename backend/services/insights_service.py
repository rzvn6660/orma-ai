from sqlalchemy.orm import Session
from datetime import datetime
from services.medicine_service import get_reminders_for_users
from services.health_planner_service import get_events_for_users
from memory.memory_models import OCMEMemory
import logging

logger = logging.getLogger(__name__)

def generate_insights_summary(db: Session, subject_id: str):
    """
    Aggregates data to generate evidence-based AI insights for the given subject.
    """
    today_date_str = datetime.now().date().isoformat()
    
    # Fetch Data - wrap in try-except to ensure we never crash
    medicines = []
    events = []
    memories = []
    try:
        medicines = get_reminders_for_users(db, [subject_id])
        events = get_events_for_users(db, [subject_id])
        memories = db.query(OCMEMemory).filter(OCMEMemory.user_id == subject_id).all()
    except Exception as e:
        logger.error(f"Error fetching insights data: {e}")

    # --- 1. Today's Activity ---
    # MedicineReminder uses taken_status (bool)
    # HealthEvent uses status (bool)
    completed_meds_today = [m for m in medicines if getattr(m, 'taken_status', False)]
    pending_meds_today = [m for m in medicines if not getattr(m, 'taken_status', False)]
    completed_events_today = [e for e in events if getattr(e, 'status', False)]

    activity_text = "No activity recorded today."
    activity_source = "Health System"
    activity_link = "/my-health"

    if completed_meds_today and not pending_meds_today:
        activity_text = "Completed all scheduled medicines today."
        activity_source = "Medication Engine"
        activity_link = "/my-health?tab=medicines"
    elif completed_events_today:
        activity_text = "Doctor appointment or health event completed."
        activity_source = "Health Planner"
        activity_link = "/my-health?tab=planner"
    elif completed_meds_today:
        activity_text = f"{len(completed_meds_today)} medicine(s) recorded today."
        activity_source = "Medication Engine"
        activity_link = "/my-health?tab=medicines"

    activity = {
        "text": activity_text,
        "source": activity_source,
        "updated": "Just now",
        "confidence": 100,
        "link": activity_link
    }

    # --- 2. Important Memory ---
    mem_to_display = None
    try:
        # Prefer pinned or important, fallback to any
        for m in sorted(memories, key=lambda x: (getattr(x, 'pinned', False), getattr(x, 'importance', 0)), reverse=True):
            mem_to_display = m
            break
    except Exception as e:
        logger.error(f"Error sorting memories: {e}")

    if mem_to_display:
        memory = {
            "text": getattr(mem_to_display, 'value', getattr(mem_to_display, 'content', getattr(mem_to_display, 'title', "Saved memory available."))),
            "source": "Memory System",
            "updated": mem_to_display.created_at.strftime("%Y-%m-%d") if getattr(mem_to_display, 'created_at', None) else "Recently",
            "confidence": int(getattr(mem_to_display, 'confidence', 1.0) * 100),
            "link": "/orma?tab=memory"
        }
    else:
        memory = {
            "text": "No important memories available.",
            "source": "Memory System",
            "updated": "Just now",
            "confidence": 100,
            "link": "/orma?tab=memory"
        }

    # --- 3. Next Recommendation ---
    rec_text = "No recommendations at this time."
    rec_source = "Health System"
    rec_link = "/my-health"

    upcoming_events = [e for e in events if not getattr(e, 'status', False)]

    if pending_meds_today:
        rec_text = f"{len(pending_meds_today)} medicine(s) remaining today."
        rec_source = "Medication Engine"
        rec_link = "/my-health?tab=medicines"
    elif upcoming_events:
        title = getattr(upcoming_events[0], 'title', None) or 'Health Event'
        rec_text = f"Upcoming appointment: {title}."
        rec_source = "Health Planner"
        rec_link = "/my-health?tab=planner"

    recommendation = {
        "text": rec_text,
        "source": rec_source,
        "updated": "Just now",
        "confidence": 100,
        "link": rec_link
    }

    return {
        "activity": activity,
        "memory": memory,
        "recommendation": recommendation
    }

