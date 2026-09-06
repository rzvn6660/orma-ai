import logging
import json
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Extracts structured entities based on the detected intent.
    """
    def __init__(self):
        pass

    async def extract(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Extract entities tailored to the specific intent using dedicated extractors.
        """
        logger.info(f"[EntityExtractor] Extracting entities for intent '{intent}' from text: '{text}'")
        
        if intent == "Appointment":
            return await self._extract_appointment(text)
        elif intent == "Medicine":
            return await self._extract_medicine(text)
        elif intent == "Reminder":
            return await self._extract_reminder(text)
        elif intent == "HealthRecord":
            return await self._extract_health_record(text)
        elif intent == "Memory":
            return await self._extract_memory(text)
        elif intent == "Caregiver":
            return await self._extract_caregiver(text)
        elif intent == "Emergency":
            return await self._extract_emergency(text)
        else:
            return {}

    async def _extract_appointment(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract appointment details. Return valid JSON with keys: "
            "'doctor_name', 'specialty', 'date', 'time', 'location', 'reason'.\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _extract_medicine(self, text: str) -> Dict[str, Any]:
        import re
        low = text.lower().strip()
        extracted = {}

        # 1. Action detection
        creation_keywords = [
            "my medicine is at", "my medicine at", "medicine is at", "add", "create",
            "schedule", "remind me to", "set reminder", "new medicine", "ചേർക്കുക", "ചേർക്കൂ",
            "എന്റെ മരുന്ന്", "മണിക്കാണ്", "മണിക്ക്"
        ]
        if any(w in low for w in creation_keywords) and not any(q in low for q in ["what", "when", "did i", "have i", "ഏതാണ്", "എപ്പോഴാണ്"]):
            extracted["action"] = "create"

        # 2. Time extraction
        time_match = re.search(r'\b(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b', low, re.I)
        if time_match:
            time_raw = time_match.group(1).strip()
            tm = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_raw, re.I)
            if tm:
                hr = int(tm.group(1))
                mn = int(tm.group(2)) if tm.group(2) else 0
                ampm = (tm.group(3) or "").upper()
                if not ampm:
                    if "രാത്രി" in low or "വൈകുന്നേരം" in low:
                        ampm = "PM"
                    elif "രാവിലെ" in low:
                        ampm = "AM"
                    else:
                        ampm = "PM" if hr >= 12 or hr in [7, 8, 9, 10, 11] else "AM"
                    if hr > 12:
                        hr -= 12
                extracted["time"] = f"{hr:02d}:{mn:02d} {ampm}"

        # 3. Dosage extraction (strict: only if explicit number + unit is present)
        dose_match = re.search(r'\b(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|tablets?|pills?|capsules?|drops?))\b', low, re.I)
        if dose_match:
            extracted["dosage"] = dose_match.group(1).strip()
        else:
            extracted["dosage"] = ""

        # 4. Frequency extraction
        freq_match = re.search(r'\b(once daily|twice daily|three times daily|thrice daily|every \d+ hours|daily|once a day|twice a day)\b', low, re.I)
        if freq_match:
            extracted["frequency"] = freq_match.group(1).strip()

        # 5. Medicine name extraction from text
        name_match = re.search(r'\b(?:add|create|schedule|take)\s+(?:a\s+)?(?:new\s+)?([A-Za-z0-9\s]+?)\s+(?:at\s+\d|daily|every|\d+\s*mg)', text, re.I)
        if name_match:
            extracted["medicine_name"] = name_match.group(1).strip()
        elif re.search(r'\bmy medicine\s+([A-Za-z0-9]+)\s+is at\b', text, re.I):
            m_name = re.search(r'\bmy medicine\s+([A-Za-z0-9]+)\s+is at\b', text, re.I).group(1).strip()
            if m_name.lower() not in ["is", "at", "time"]:
                extracted["medicine_name"] = m_name

        # If medicine_name is still not found and text is a short name answer
        if "medicine_name" not in extracted:
            clean_test = re.sub(r"[^\w\s]", "", text).strip()
            if len(clean_test.split()) <= 4 and not any(w in low for w in ["medicine", "is at", "remind", "schedule", "add", "take", "what", "when", "did i"]):
                extracted["medicine_name"] = text.strip().rstrip(".").strip()

        # If fields are missing and text is complex, use LLM fallback
        if not extracted.get("time") or not extracted.get("action"):
            prompt = (
                "Extract medicine details. Return valid JSON with keys: "
                "'medicine_name', 'dosage', 'frequency', 'time', 'purpose', 'action' (e.g. 'take', 'schedule', 'status').\n"
                f"Text: \"{text}\""
            )
            llm_res = await self._call_llm_json(prompt)
            if llm_res:
                for k, v in llm_res.items():
                    if v and (k not in extracted or not extracted[k]):
                        extracted[k] = v

        return extracted

    async def _extract_reminder(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract reminder details. Return valid JSON with keys: "
            "'title', 'time', 'date', 'frequency'.\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _extract_health_record(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract health record details. Return valid JSON with keys: "
            "'test_name', 'date', 'result_value', 'hospital_name'.\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _extract_memory(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract memory/context details. Return valid JSON with keys: "
            "'query_subject', 'timeframe', 'action' (e.g. 'recall', 'store').\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _extract_caregiver(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract caregiver details. Return valid JSON with keys: "
            "'relation', 'name', 'message_content', 'urgency'.\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _extract_emergency(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract emergency details. Return valid JSON with keys: "
            "'symptom', 'location', 'severity' (high/medium/low).\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

    async def _call_llm_json(self, prompt: str) -> Dict[str, Any]:
        try:
            from llm.ai_manager import ai_manager
            res = await ai_manager.generate(prompt=prompt, max_tokens=150)
            text_resp = res.get("text", "")
            if text_resp:
                start = text_resp.find('{')
                end = text_resp.rfind('}')
                if start != -1 and end != -1:
                    json_str = text_resp[start:end+1]
                    parsed = json.loads(json_str)
                    logger.info(f"[EntityExtractor] Extracted: {parsed}")
                    return parsed
        except Exception as e:
            logger.warning(f"[EntityExtractor] Extraction warning: {e}")
        
        return {}

entity_extractor = EntityExtractor()
