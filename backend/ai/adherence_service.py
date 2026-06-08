import datetime
from sqlalchemy.orm import Session
from models.medicine import MedicineReminder

def calculate_confidence_score(db_reminder: MedicineReminder, confirmation_method: str) -> MedicineReminder:
    """
    Calculates the confidence score of a medicine confirmation.
    
    If confirmation happens unrealistically fast (e.g. < 5 seconds), lower the score.
    Updates the db_reminder in-place.
    """
    db_reminder.confirmation_method = confirmation_method
    now = datetime.datetime.utcnow()
    
    if db_reminder.reminder_triggered_at:
        time_diff = int((now - db_reminder.reminder_triggered_at).total_seconds())
        db_reminder.confirmation_time_difference = time_diff
    else:
        time_diff = None
        
    base_score = 100
    flags = []
    
    if confirmation_method == "manual":
        # Manual tap is generally trustworthy, but check speed
        if time_diff is not None and time_diff < 3:
            base_score -= 40
            flags.append("suspiciously_fast_manual")
        elif time_diff is not None and time_diff > 3600:
            flags.append("delayed_manual")
            
    elif confirmation_method == "voice":
        # Voice is good but could be a casual "yeah" without actually taking it
        if time_diff is not None and time_diff < 5:
            base_score -= 50
            flags.append("suspiciously_fast_voice")
            
    db_reminder.confidence_score = base_score
    db_reminder.adherence_pattern_flags = ",".join(flags) if flags else None
    
    return db_reminder

def get_behavioral_insights(db: Session, user_id: str = None):
    """
    Analyzes historical data to find adherence trends.
    Placeholder for future family monitoring dashboard.
    """
    # E.g., calculate weekly adherence percentage, frequency of low confidence
    pass
