def detect_medicine_confirmation(text: str) -> bool:
    """
    Detects if the user is confirming they have taken their medicine.
    Supports English and Malayalam intent matching.
    """
    text_lower = text.lower()
    
    confirmation_phrases = [
        "i took it", "medicine taken", "yes i had it", "took medicine", "i took my medicine",
        "i had it", "already took it", "have taken it", "കഴിച്ചു", "മരുന്ന് കഴിച്ചു", "എടുത്തു", "മരുന്ന് എടുത്തു",
        "i took", "yes i took", "already had", "finished taking", "i have taken"
    ]
    
    return any(phrase in text_lower for phrase in confirmation_phrases)

def detect_medicine_status_inquiry(text: str) -> bool:
    """
    Detects if user is asking about their medicine status.
    """
    text_lower = text.lower()
    inquiry_phrases = [
        "did i take", "have i taken", "is my medicine pending",
        "മരുന്ന് കഴിച്ചോ", "മരുന്ന് എടുത്തോ", "did i have"
    ]
    return any(phrase in text_lower for phrase in inquiry_phrases)
