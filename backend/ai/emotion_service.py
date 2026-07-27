def analyze_emotion(text: str) -> str:
    """
    Analyzes user text to detect emotions.
    Uses rule-based logic for fast transcription sentiment analysis.
    Prepared for future voice-tone analysis integration.
    """
    text_lower = text.lower()
    if any(w in text_lower for w in ["sad", "crying", "depressed", "unhappy", "സങ്കടം", "കരച്ചിൽ"]):
        return "sadness"
    if any(w in text_lower for w in ["stressed", "overwhelmed", "hard", "difficult", "പ്രയാസം", "ബുദ്ധിമുട്ട്"]):
        return "stress"
    if any(w in text_lower for w in ["worried", "scared", "anxious", "fear", "പേടി", "ഭയം", "ആശങ്ക"]):
        return "anxiety"
    if any(w in text_lower for w in ["lonely", "alone", "miss", "nobody", "ഒറ്റക്ക്", "തനിച്ചു"]):
        return "loneliness"
    return "calmness"
