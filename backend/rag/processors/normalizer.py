import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Deterministic, safety-preserving text normalization for extracted medical documents.
    
    Guarantees:
    - Normalizes unicode forms (NFC).
    - Preserves all multilingual scripts (Malayalam, Hindi, Arabic, Tamil, Telugu, Kannada, English).
    - Removes non-printable control characters without deleting valid unicode.
    - Fixes hyphenated word wrapping across line breaks (e.g., 'Metfor-\nmin' -> 'Metformin').
    - Collapses excessive blank lines and whitespace.
    - NEVER alters medical numbers, dosages, or drug names.
    - NEVER invokes an LLM.
    """
    if not text:
        return ""

    # 1. Unicode normalization (Canonical Composition)
    normalized = unicodedata.normalize("NFC", text)

    # 2. Replace null bytes and non-printable control characters (keep \n, \r, \t)
    normalized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', normalized)

    # 3. Replace non-breaking spaces and exotic spaces with standard space
    normalized = re.sub(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]', ' ', normalized)

    # 4. Normalize CRLF to LF
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')

    # 5. Fix hyphenation at line breaks: word- \n word -> wordword
    # e.g., "Car- \ndiovascular" -> "Cardiovascular", "Metfor-\nmin" -> "Metformin"
    normalized = re.sub(r'([a-zA-Z\u0900-\u0D7F])-\s*\n\s*([a-zA-Z\u0900-\u0D7F])', r'\1\2', normalized)

    # 6. Collapse excessive horizontal whitespace within lines
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in normalized.split('\n')]

    # 7. Collapse excessive consecutive empty lines (>2 to 2)
    cleaned_lines = []
    consecutive_empty = 0
    for line in lines:
        if not line:
            consecutive_empty += 1
            if consecutive_empty <= 2:
                cleaned_lines.append("")
        else:
            consecutive_empty = 0
            cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return result
