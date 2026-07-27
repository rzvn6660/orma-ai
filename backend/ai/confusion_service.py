from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.wellness import WellnessLog
from ai.emotion_service import analyze_emotion

def get_intent_category(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["medicine", "pill", "took", "മരുന്ന്", "ഗുളിക"]):
        return "medicine_query"
    if any(w in text_lower for w in ["appointment", "doctor", "hospital", "ഡോക്ടർ", "ആശുപത്രി"]):
        return "appointment_query"
    if any(w in text_lower for w in ["where", "who", "what time", "എവിടെ", "ആര്", "എപ്പോൾ"]):
        return "memory_query"
    return "general"

def detect_and_log_confusion(db: Session, text: str, user_id: str) -> bool:
    """
    Detects repeated questions and cognitive irregularities.
    Generates confusion flag and behavioral insights.
    """
    category = get_intent_category(text)
    emotion = analyze_emotion(text)
    
    now = datetime.utcnow()
    fifteen_mins_ago = now - timedelta(minutes=15)
    
    # Check for repeated questions in the short time window
    recent_logs = db.query(WellnessLog).filter(
        WellnessLog.user_id == user_id,
        WellnessLog.timestamp >= fifteen_mins_ago,
        WellnessLog.intent_category == category
    ).all()
    
    # If the user asked the same category of question recently, flag as repeated
    # category must not be 'general' to count as specific confusion
    repeated = len(recent_logs) >= 1 and category != "general"
    
    # Confusion is flagged if repeating memory/medicine questions or showing anxiety
    confusion_flag = repeated or emotion in ["anxiety", "stress"]
    
    log = WellnessLog(
        user_id=user_id,
        text=text,
        emotion=emotion,
        confusion_flag=confusion_flag,
        repeated_question=repeated,
        intent_category=category
    )
    db.add(log)
    db.commit()
    
    return confusion_flag
