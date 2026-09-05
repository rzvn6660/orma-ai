from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
import datetime
from typing import Dict, Any

from services.medicine_service import resolve_medication_daily_status

def get_summary(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    today = datetime.datetime.utcnow().date()
    query = db.query(MedicineReminder)
    if elder_ids is not None:
        query = query.filter(MedicineReminder.elder_id.in_(elder_ids))
    all_meds = query.all()
    
    total = len(all_meds)
    taken = sum(1 for m in all_meds if resolve_medication_daily_status(m))
    missed = sum(1 for m in all_meds if not resolve_medication_daily_status(m) and m.adherence_pattern_flags == 'missed')
    pending = sum(1 for m in all_meds if not resolve_medication_daily_status(m) and m.adherence_pattern_flags != 'missed')
    
    completion_rate = round((taken / total * 100) if total > 0 else 0)
    
    return {
        "medicines_taken": taken,
        "missed_medicines": missed,
        "pending_medicines": pending,
        "completion_percentage": completion_rate
    }

def get_adherence(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    # Mocking historical adherence data for startup-level dashboard visuals
    weekly_trends = [
        {"day": "Mon", "adherence": 85},
        {"day": "Tue", "adherence": 92},
        {"day": "Wed", "adherence": 88},
        {"day": "Thu", "adherence": 95},
        {"day": "Fri", "adherence": 90},
        {"day": "Sat", "adherence": 97},
        {"day": "Sun", "adherence": 94},
    ]
    
    query = db.query(MedicineReminder)
    if elder_ids is not None:
        query = query.filter(MedicineReminder.elder_id.in_(elder_ids))
    all_meds = query.all()
    avg_confidence = 0
    if all_meds:
        confidences = [m.confidence_score for m in all_meds if m.confidence_score]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            
    return {
        "weekly_trends": weekly_trends,
        "consistency_score": 92,
        "confidence_average": round(avg_confidence or 88),
        "missed_reminders_this_week": 3
    }

def get_behavior(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    # Analyzing confirmation methods
    query = db.query(MedicineReminder)
    if elder_ids is not None:
        query = query.filter(MedicineReminder.elder_id.in_(elder_ids))
    all_meds = query.all()
    voice_confirmed = sum(1 for m in all_meds if m.confirmation_method == "voice")
    manual_confirmed = sum(1 for m in all_meds if m.confirmation_method == "manual")
    unverified = len(all_meds) - voice_confirmed - manual_confirmed
    
    return {
        "confirmation_stats": {
            "voice": voice_confirmed,
            "manual": manual_confirmed,
            "suspicious": 1, # Mock
            "unverified": unverified
        },
        "insights": [
            "Consistent morning routine established.",
            "Voice confirmation used for 80% of evening meds.",
            "1 suspicious fast confirmation detected yesterday."
        ]
    }

def get_emergencies(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    # Mocking emergency alerts for the dashboard
    return {
        "recent_triggers": [
            {"id": 1, "type": "Fall Detected", "time": "2 days ago", "severity": "high", "resolved": True},
            {"id": 2, "type": "Missed multiple meds", "time": "1 week ago", "severity": "medium", "resolved": True}
        ],
        "total_history": 5
    }
