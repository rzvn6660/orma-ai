import json
import httpx
from utils.medicine_matcher import fuzzy_match_medicine, normalize_dosage, normalize_timing

async def parse_medicine_text(raw_text: str) -> dict:
    """
    Uses the local LLM to parse raw OCR or Voice text into a structured medicine dictionary.
    Returns a dictionary with extracted fields and correction suggestions.
    """
    prompt = (
        "You are an AI medical assistant extracting prescription data. "
        "Extract EVERY medicine mentioned in the text. Continue parsing until the prescription ends to ensure no medicine is missed. "
        "Return strictly valid JSON as an ARRAY of objects. Each object must have these keys: "
        "'event_type' (e.g. medicine, doctor_appointment, blood_test, exercise, water_reminder, etc), "
        "'title' (e.g. medicine name, doctor name), 'description' (e.g. dosage, specialty), "
        "'timing' (e.g. 08:00 AM), 'event_date' (YYYY-MM-DD), 'purpose', 'frequency', 'notes', 'location', 'contact_number'. "
        "IMPORTANT RULES:\n"
        "- Never hallucinate medicine strengths or modify numbers. Validate extracted dosage directly from the text. If missing or uncertain, leave 'dosage' blank (\"\").\n"
        "- If time/frequency is not explicitly stated (e.g. SOS, or none), do NOT invent default times. Leave 'timing' and 'frequency' blank (\"\").\n"
        "- Preserve the original order of the medicines.\n"
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
                
                # If LLM returned a single dict instead of a list, wrap it
                if isinstance(parsed, dict):
                    parsed = [parsed]
                
                results = []
                for med in parsed:
                    event_type = med.get("event_type", "medicine")
                    title = med.get("title") or med.get("medicine_name", "")
                    description = med.get("description") or med.get("dosage", "")
                    
                    if not title:
                        continue
                        
                    # Fuzzy match only if it's a medicine
                    corrected_name = fuzzy_match_medicine(title) if event_type == 'medicine' else title
                    corrected_dosage = normalize_dosage(description) if event_type == 'medicine' else description
                    
                    raw_timing = med.get("timing", "")
                    corrected_timing = normalize_timing(raw_timing) if raw_timing else ""
                    
                    results.append({
                        "id": f"new_{len(results)}",
                        "event_type": event_type,
                        "title": corrected_name,
                        "description": corrected_dosage,
                        "medicine_name": corrected_name, # backward compatibility
                        "dosage": corrected_dosage, # backward compatibility
                        "original_ocr_name": title,
                        "timing": corrected_timing,
                        "event_date": med.get("event_date", ""),
                        "location": med.get("location", ""),
                        "contact_number": med.get("contact_number", ""),
                        "purpose": med.get("purpose", ""),
                        "frequency": med.get("frequency", ""),
                        "notes": med.get("notes", ""),
                        "confidence": 85 if title == corrected_name else 60,
                        "suggestion": f"Did you mean {corrected_name}?" if title != corrected_name else None
                    })
                
                return results
            else:
                raise ValueError("Failed to get response from Ollama")
    except Exception as e:
        print(f"Error parsing medicine: {e}")
        # Fallback mechanism
        return [{
            "event_type": "medicine",
            "title": "Unknown",
            "description": "",
            "medicine_name": "Unknown",
            "original_ocr_name": "Unknown",
            "dosage": "",
            "timing": "",
            "purpose": "",
            "frequency": "",
            "notes": "",
            "confidence": 0,
            "suggestion": "Could not parse correctly. Please verify."
        }]
