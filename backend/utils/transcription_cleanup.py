import re

def normalize_transcription(text: str) -> str:
    """
    Cleans up common Whisper misheard variations of 'Orma AI' 
    and normalizes them to 'Orma AI'.
    """
    if not text:
        return text
        
    # List of common misheard variations
    variations = [
        r'\baroma ai\b',
        r'\borma\b',
        r'\bnormal ai\b',
        r'\bor my ai\b',
        r'\balma ai\b'
    ]
    
    # Combine them into a single case-insensitive regex pattern
    pattern = re.compile('|'.join(variations), re.IGNORECASE)
    
    # Replace any matched variation with 'Orma AI'
    normalized_text = pattern.sub('Orma AI', text)
    
    return normalized_text
