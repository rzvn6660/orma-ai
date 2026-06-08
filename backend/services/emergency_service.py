import logging
from typing import List

# Setup logger for emergency alerts
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = {
    "chest pain": "high",
    "cannot breathe": "high",
    "emergency": "high",
    "fell down": "high",
    "help": "medium",
    "dizziness": "medium"
}

def analyze_text_for_emergency(text: str) -> dict:
    """
    Analyzes transcribed text for emergency keywords.
    """
    if not text:
        return {"is_emergency": False, "triggered_keywords": []}
        
    text_lower = text.lower()
    triggered_keywords = [kw for kw in EMERGENCY_KEYWORDS.keys() if kw in text_lower]
    
    is_emergency = len(triggered_keywords) > 0
    
    severity = "low"
    if is_emergency:
        # Determine highest severity
        severities = [EMERGENCY_KEYWORDS[kw] for kw in triggered_keywords]
        if "high" in severities:
            severity = "high"
        elif "medium" in severities:
            severity = "medium"
            
    message = "It sounds like you may need help. Alerting emergency contacts." if is_emergency else ""
            
    return {
        "is_emergency": is_emergency,
        "triggered_keywords": triggered_keywords,
        "severity": severity,
        "message": message
    }

def trigger_alert(user_id: str, text: str, triggered_keywords: List[str]):
    """
    Triggers an emergency alert.
    
    TODO: Prepare for future SMS/Email integration (e.g., Twilio, SendGrid).
    For now, this logs a high-priority warning to the console.
    """
    logger.warning(
        f"\n{'='*50}\n"
        f"🚨 EMERGENCY ALERT TRIGGERED for user '{user_id}' 🚨\n"
        f"Keywords detected: {triggered_keywords}\n"
        f"Context: {text}\n"
        f"{'='*50}\n"
    )
    # Future integration:
    # send_sms_alert(user_id, text)
    # send_email_alert(user_id, text)
