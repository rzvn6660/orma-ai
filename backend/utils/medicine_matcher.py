from thefuzz import process

# A small mock database of common elderly medicines.
# In production, this would be an actual API or large database.
COMMON_MEDICINES = [
    "Amlodipine",
    "Metformin",
    "Atorvastatin",
    "Lisinopril",
    "Losartan",
    "Levothyroxine",
    "Omeprazole",
    "Pantoprazole",
    "Gabapentin",
    "Aspirin",
    "Clopidogrel",
    "Rosuvastatin",
    "Furosemide",
    "Glipizide",
    "Paracetamol"
]

import re

def normalize_dosage(dosage: str) -> str:
    if not dosage:
        return dosage
    dosage = dosage.lower().strip()
    dosage = re.sub(r'\bgrams?\b', 'mg', dosage)  # Grams mistakenly transcribed often mean mg for these meds
    dosage = re.sub(r'\bmilligrams?\b', 'mg', dosage)
    dosage = re.sub(r'\bml\b', 'ml', dosage) # ensure lowercase
    # normalize spaces like "500 mg" to "500 mg"
    dosage = re.sub(r'(\d+)\s*(mg|ml)', r'\1 \2', dosage)
    return dosage

def normalize_timing(timing: str) -> str:
    if not timing:
        return "08:00 AM"
        
    timing_lower = timing.lower().strip()
    
    mapping = {
        "morning": "08:00 AM",
        "before breakfast": "07:30 AM",
        "after breakfast": "09:00 AM",
        "afternoon": "01:00 PM",
        "before lunch": "12:30 PM",
        "after lunch": "01:30 PM",
        "evening": "06:00 PM",
        "before dinner": "07:30 PM",
        "after dinner": "08:30 PM",
        "night": "09:00 PM",
        "bedtime": "09:30 PM",
        "at bedtime": "09:30 PM",
        "everyday after lunch": "01:30 PM",
        "sos": ""
    }
    
    for key, value in mapping.items():
        if key in timing_lower:
            return value
            
    # Try to extract time like "8 PM"
    time_match = re.search(r'(\d{1,2})(?::\d{2})?\s*(am|pm)', timing_lower)
    if time_match:
        return time_match.group(0).upper()
        
    return timing

def fuzzy_match_medicine(extracted_name: str, threshold: int = 70) -> str:
    """
    Attempts to match an OCR-extracted medicine name against known common medicines.
    Returns the corrected name if a match > threshold is found, otherwise the original.
    """
    if not extracted_name:
        return extracted_name
        
    match, score = process.extractOne(extracted_name, COMMON_MEDICINES)
    if score >= threshold:
        return match
    return extracted_name
