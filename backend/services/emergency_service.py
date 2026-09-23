import logging
from typing import List

# Setup logger for emergency alerts
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = {
    # High severity acute clinical & distress events (English)
    "chest pain": "high",
    "severe chest pain": "high",
    "cannot breathe": "high",
    "can't breathe": "high",
    "cant breathe": "high",
    "breathing difficulty": "high",
    "severe breathing difficulty": "high",
    "bleeding heavily": "high",
    "heavy bleeding": "high",
    "unconscious": "high",
    "fell down": "high",
    "fell and hit": "high",
    "can't get up": "high",
    "cant get up": "high",
    "cannot get up": "high",
    "call an ambulance": "high",
    "call ambulance": "high",
    "ambulance": "high",
    "heart is beating irregularly": "high",
    "heart beating irregularly": "high",
    "emergency": "high",

    # High severity acute distress events (Malayalam)
    "രക്ഷിക്കൂ": "high",                      # Save me / help me
    "നിലത്ത് വീണു": "high",                 # Fell on the floor
    "ഞാൻ വീണു": "high",                     # I fell
    "നെഞ്ചുവേദന": "high",                   # Chest pain
    "കടുത്ത നെഞ്ചുവേദന": "high",            # Severe chest pain
    "ആപത്ത്": "high",                         # Emergency / disaster
    "ആംബുലൻസ് വിളിക്കൂ": "high",             # Call ambulance
    "ആംബുലൻസ്": "high",                     # Ambulance
    "എഴുന്നേൽക്കാൻ കഴിയുന്നില്ല": "high",       # Cannot get up
    "ശ്വാസമെടുക്കാൻ കഴിയുന്നില്ല": "high",      # Cannot breathe
    "ശ്വാസം മുട്ടുന്നു": "high",              # Suffocating
    "സഹായം വേണം": "high",                    # Need help (acute)

    # Medium severity distress signals
    "help me": "high",
    "save me": "high",
    "help": "medium",
    "dizziness": "medium"
}

INFORMATIONAL_OR_META_PATTERNS = [
    "how does emergency", "how emergency support works", "how emergency works",
    "what is emergency", "emergency support", "emergency feature", "emergency features",
    "about emergency", "emergency setup", "emergency contact phone", "emergency contact number",
    "emergency contact info", "tell me about emergency", "information about emergency",
    "how to use emergency", "emergency button",
    "എമർജൻസി ഫീച്ചറിനെക്കുറിച്ച്", "എമർജൻസി ഫീച്ചർ", "എമർജൻസി സപ്പോർട്ട്"
]

HISTORICAL_OR_THIRD_PARTY_MARKERS = [
    "last year", "last month", "last week", "yesterday", "years ago", "a year ago",
    "when i was young", "earlier this week", "a few days ago", "past week",
    "my grandson", "my granddaughter", "my friend", "my neighbor", "someone else",
    "football last week", "playing football", "playing outside",
    "ഇന്നലെ", "കഴിഞ്ഞ ആഴ്ച", "കഴിഞ്ഞ മാസം", "കഴിഞ്ഞ വർഷം"
]

def analyze_text_for_emergency(text: str) -> dict:
    """
    Analyzes transcribed text for acute emergency keywords with context filtering.
    Avoids false positives on informational queries and historical/third-party anecdotes.
    """
    if not text:
        return {"is_emergency": False, "triggered_keywords": [], "severity": "low", "message": ""}
        
    text_lower = text.lower().strip()

    # 1. Informational / Meta-inquiry check (e.g. "how does emergency feature work?")
    is_meta = any(pat in text_lower for pat in INFORMATIONAL_OR_META_PATTERNS)
    if is_meta:
        return {
            "is_emergency": False,
            "triggered_keywords": [],
            "severity": "low",
            "message": "",
            "filtered_reason": "informational_or_meta_query"
        }

    # 2. Acute keywords search
    triggered_keywords = [kw for kw in EMERGENCY_KEYWORDS.keys() if kw in text_lower]

    # Special handling for single word 'help': only trigger if text is very short/urgent
    if triggered_keywords == ["help"]:
        words = text_lower.split()
        if len(words) > 6 and not any(w in text_lower for w in ["hurts", "pain", "now", "please", "urgent"]):
            # Casual conversation e.g. "Can you help me find my recipe?"
            triggered_keywords = []

    if not triggered_keywords:
        return {"is_emergency": False, "triggered_keywords": [], "severity": "low", "message": ""}

    # 3. Check for historical or third-party narratives
    is_historical = any(marker in text_lower for marker in HISTORICAL_OR_THIRD_PARTY_MARKERS)
    # Check if there is an overriding immediate acute distress token
    ongoing_acute_override = any(tok in text_lower for tok in [
        "cannot get up", "can't get up", "cant get up", "bleeding heavily",
        "save me", "help me now", "right away", "immediately", "urgent",
        "എഴുന്നേൽക്കാൻ കഴിയുന്നില്ല", "രക്ഷിക്കൂ"
    ])

    if is_historical and not ongoing_acute_override:
        return {
            "is_emergency": False,
            "triggered_keywords": [],
            "severity": "low",
            "message": "",
            "filtered_reason": "historical_or_third_party_incident"
        }
    
    is_emergency = len(triggered_keywords) > 0
    
    severity = "low"
    if is_emergency:
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
