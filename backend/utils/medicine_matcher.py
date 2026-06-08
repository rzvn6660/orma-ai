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
    "Glipizide"
]

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
