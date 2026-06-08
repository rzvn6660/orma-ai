import json
import httpx
from utils.medicine_matcher import fuzzy_match_medicine

async def parse_medicine_text(raw_text: str) -> dict:
    """
    Uses the local LLM to parse raw OCR or Voice text into a structured medicine dictionary.
    Returns a dictionary with extracted fields and correction suggestions.
    """
    prompt = (
        "You are an AI medical assistant extracting prescription data. "
        "Extract the medicine name, dosage, timing, purpose, frequency, and notes from the following raw text. "
        "Return strictly valid JSON with the following keys: "
        "'medicine_name', 'dosage', 'timing', 'purpose', 'frequency', 'notes'. If a field is missing, set it to an empty string. "
        "Do NOT include markdown formatting or extra text.\n\n"
        f"Raw Text: {raw_text}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_json = data.get("response", "{}")
                parsed = json.loads(raw_json)
                
                # Apply fuzzy matching to the extracted name
                original_name = parsed.get("medicine_name", "")
                corrected_name = fuzzy_match_medicine(original_name)
                
                return {
                    "medicine_name": corrected_name,
                    "original_ocr_name": original_name,
                    "dosage": parsed.get("dosage", ""),
                    "timing": parsed.get("timing", "08:00 AM"),
                    "purpose": parsed.get("purpose", ""),
                    "frequency": parsed.get("frequency", ""),
                    "notes": parsed.get("notes", ""),
                    "confidence": 85 if original_name == corrected_name else 60,
                    "suggestion": f"Did you mean {corrected_name}?" if original_name != corrected_name else None
                }
            else:
                raise ValueError("Failed to get response from Ollama")
    except Exception as e:
        print(f"Error parsing medicine: {e}")
        # Fallback mechanism
        return {
            "medicine_name": "Unknown",
            "original_ocr_name": "Unknown",
            "dosage": "",
            "timing": "08:00 AM",
            "purpose": "",
            "frequency": "",
            "notes": "",
            "confidence": 0,
            "suggestion": "Could not parse correctly. Please verify."
        }
