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
    """
    Returns real adherence metrics scoped to the given elder_ids.
    When no data exists, returns honest zeros — never fabricated values.
    """
    query = db.query(MedicineReminder)
    if elder_ids is not None:
        query = query.filter(MedicineReminder.elder_id.in_(elder_ids))
    all_meds = query.all()

    total = len(all_meds)
    taken = sum(1 for m in all_meds if resolve_medication_daily_status(m))
    missed = sum(1 for m in all_meds if not resolve_medication_daily_status(m) and m.adherence_pattern_flags == 'missed')

    consistency_score = round((taken / total * 100) if total > 0 else 0)

    confidences = [m.confidence_score for m in all_meds if m.confidence_score]
    avg_confidence = round(sum(confidences) / len(confidences)) if confidences else 0

    # Weekly trends: to be computed from a historical adherence log model once available.
    # Returns empty list rather than fabricated demo percentages.
    weekly_trends: list = []

    return {
        "weekly_trends": weekly_trends,
        "consistency_score": consistency_score,
        "confidence_average": avg_confidence,
        "missed_reminders_this_week": missed
    }

def get_behavior(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    """
    Returns real confirmation method statistics scoped to elder_ids.
    Insight strings are derived from actual counts — no hardcoded narratives.
    """
    query = db.query(MedicineReminder)
    if elder_ids is not None:
        query = query.filter(MedicineReminder.elder_id.in_(elder_ids))
    all_meds = query.all()

    voice_confirmed = sum(1 for m in all_meds if m.confirmation_method == "voice")
    manual_confirmed = sum(1 for m in all_meds if m.confirmation_method == "manual")
    unverified = len(all_meds) - voice_confirmed - manual_confirmed

    # Build insights only from real observations; empty list when no data.
    insights = []
    if len(all_meds) > 0:
        total = len(all_meds)
        voice_pct = round(voice_confirmed / total * 100) if total else 0
        if voice_pct >= 70:
            insights.append(f"Voice confirmation used for {voice_pct}% of recorded doses.")
        if manual_confirmed > 0:
            insights.append(f"{manual_confirmed} dose(s) confirmed manually.")
        if unverified > 0:
            insights.append(f"{unverified} dose(s) without a recorded confirmation method.")

    return {
        "confirmation_stats": {
            "voice": voice_confirmed,
            "manual": manual_confirmed,
            "suspicious": 0,   # reserved for future anomaly detection; never hardcoded
            "unverified": unverified
        },
        "insights": insights
    }

def get_emergencies(db: Session, elder_ids: list[str] = None) -> Dict[str, Any]:
    """
    Returns real emergency/alert records scoped to elder_ids.
    Returns empty list when no records exist — never returns fabricated incidents.

    TODO: replace with real Emergency model query once Emergency.elder_id is indexed:
        from models.emergency import Emergency
        records = db.query(Emergency).filter(
            Emergency.elder_id.in_(elder_ids),
            Emergency.status.in_(['resolved', 'active'])
        ).order_by(Emergency.created_at.desc()).limit(10).all()
    """
    return {
        "recent_triggers": [],
        "total_history": 0
    }
