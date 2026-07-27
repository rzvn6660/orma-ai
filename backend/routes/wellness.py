from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.wellness import WellnessLog
from dependencies import get_current_context

router = APIRouter()

@router.get("/summary")
def get_wellness_summary(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Provides wellness indicators, confusion trends, and emotional state analytics
    for the Caregiver Dashboard.
    """
    subject = ctx['resolved_subject']
    logs = db.query(WellnessLog).filter(WellnessLog.user_id == subject["id"]).order_by(WellnessLog.timestamp.desc()).limit(100).all()
    
    emotion_counts = {"sadness": 0, "stress": 0, "anxiety": 0, "loneliness": 0, "calmness": 0}
    confusion_events = 0
    repeated_questions = 0
    
    for log in logs:
        if log.emotion in emotion_counts:
            emotion_counts[log.emotion] += 1
        if log.confusion_flag:
            confusion_events += 1
        if log.repeated_question:
            repeated_questions += 1
            
    # Calculate simple trends
    status = "Stable"
    if confusion_events > 3 or emotion_counts["anxiety"] > 2:
        status = "Needs Attention"
    if confusion_events > 5:
        status = "High Cognitive Concern"
        
    return {
        "emotions": emotion_counts,
        "confusion_events_recent": confusion_events,
        "repeated_questions": repeated_questions,
        "status": status,
        "total_interactions": len(logs),
        "recent_logs": [
            {
                "time": log.timestamp.strftime("%I:%M %p"),
                "text": log.text,
                "emotion": log.emotion,
                "confusion": log.confusion_flag
            } for log in logs[:5]
        ]
    }
