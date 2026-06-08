def detect_medicine_confirmation(text: str) -> bool:
    """
    Detects if the user is confirming they have taken their medicine.
    Supports English and Malayalam intent matching.
    """
    text_lower = text.lower()
    
    confirmation_phrases = [
        "i took it", "medicine taken", "yes i had it", "took medicine",
        "i had it", "already taken", "കഴിച്ചു", "മരുന്ന് കഴിച്ചു", "എടുത്തു", "മരുന്ന് എടുത്തു"
    ]
    
    return any(phrase in text_lower for phrase in confirmation_phrases)
