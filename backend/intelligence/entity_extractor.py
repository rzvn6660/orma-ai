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
        prompt = (
            "Extract medicine details. Return valid JSON with keys: "
            "'medicine_name', 'dosage', 'frequency', 'time', 'purpose', 'action' (e.g. 'take', 'schedule', 'status').\n"
            f"Text: \"{text}\""
        )
        return await self._call_llm_json(prompt)

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
