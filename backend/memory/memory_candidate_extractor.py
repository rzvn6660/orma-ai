import logging
import re
import json
from typing import List, Dict, Any, Optional
from memory.memory_classifier import memory_classifier
from memory.importance_engine import importance_engine
from memory.confidence_engine import confidence_engine

logger = logging.getLogger(__name__)

class MemoryCandidateExtractor:
    """
    Analyzes conversation transcripts to identify potential memory candidates.
    Resilient to provider timeouts, truncated tokens, and markdown fences.
    Features deterministic fallback for explicit, high-confidence memory commands.
    """
    def __init__(self):
        pass

    def _clean_and_parse_json(self, text_resp: str) -> List[Dict[str, Any]]:
        """
        Extracts and parses JSON lists or objects from LLM response text,
        handling code fences, trailing commas, and truncated model outputs.
        """
        if not text_resp:
            return []

        # 1. Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text_resp, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*", "", cleaned).strip()

        # 2. Try matching full JSON array [...]
        start_arr = cleaned.find('[')
        end_arr = cleaned.rfind(']')
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            json_str = cleaned[start_arr:end_arr + 1]
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str) # clean trailing commas
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                elif isinstance(data, dict):
                    return [data]
            except Exception:
                pass

        # 3. Try matching single JSON object {...}
        start_obj = cleaned.find('{')
        end_obj = cleaned.rfind('}')
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            json_str = cleaned[start_obj:end_obj + 1]
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            try:
                data = json.loads(json_str)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
            except Exception:
                pass

        # 4. Fallback: Regex extraction for truncated or malformed JSON objects
        extracted = []
        pattern = r'["\']title["\']\s*:\s*["\']([^"\']+)["\']\s*,\s*["\']value["\']\s*:\s*["\']([^"\']*)["\']?'
        for match in re.finditer(pattern, cleaned, flags=re.IGNORECASE):
            title = match.group(1).strip()
            value = match.group(2).strip()
            if title and value:
                extracted.append({"title": title, "value": value})

        if extracted:
            return extracted

        # Reversed order: value before title
        pattern_rev = r'["\']value["\']\s*:\s*["\']([^"\']+)["\']\s*,\s*["\']title["\']\s*:\s*["\']([^"\']*)["\']?'
        for match in re.finditer(pattern_rev, cleaned, flags=re.IGNORECASE):
            value = match.group(1).strip()
            title = match.group(2).strip()
            if title and value:
                extracted.append({"title": title, "value": value})

        return extracted

    def _extract_explicit_memory_candidate(self, user_text: str, context_intent: str) -> Optional[Dict[str, Any]]:
        """
        Deterministically extracts a candidate when the user explicitly commands
        the system to remember a preference or fact.
        Rejects questions, casual remarks, and past recollections.
        """
        text_clean = user_text.strip()
        if not text_clean:
            return None

        # Rejection Rule 1: Questions must never become memories
        if text_clean.endswith("?"):
            return None

        low = text_clean.lower()
        if any(low.startswith(q) for q in [
            "do you remember", "did you remember", "can you remember", "could you remember",
            "what do you remember", "what did you remember", "what is", "what was", "what are",
            "when is", "where is", "who is", "did i", "have i", "do i"
        ]):
            return None

        # Rejection Rule 2: Past personal recollections ("I remember taking my pill")
        if any(low.startswith(r) for r in ["i remember ", "i recalled ", "i was remembering ", "i remember when"]):
            return None

        # Recognition Rule: Imperative memory trigger
        trigger_pattern = (
            r"^\s*(?:please\s+)?(?:remember|keep\s+in\s+mind|note\s+down|note|save\s+(?:this\s+)?to\s+(?:my\s+)?memory)"
            r"(?:\s+that|\s*:|\s*,)?\s+(.+)$"
        )
        match = re.match(trigger_pattern, text_clean, flags=re.IGNORECASE)
        if not match:
            return None

        statement = match.group(1).strip()
        # Clean leading "that ", "to "
        statement = re.sub(r"^(?:that|to)\s+", "", statement, flags=re.IGNORECASE).strip()
        statement = statement.rstrip(".!,").strip()

        if len(statement) < 3:
            return None

        title = None
        value = None

        # Pattern A: Copula structure: "<subject> is/are/was <value>"
        copula_match = re.match(
            r"^(?:my\s+)?(.*?)\s+(?:is|are|was|should\s+be|must\s+be)\s+(.+)$",
            statement,
            flags=re.IGNORECASE
        )
        if copula_match:
            raw_sub = copula_match.group(1).strip()
            raw_val = copula_match.group(2).strip().rstrip(".!,")
            if raw_sub and raw_val:
                title = raw_sub.title()
                value = raw_val

        # Pattern B: Preference structure: "I prefer <val> for/in/as <key>" or "I prefer <val>"
        if not title:
            pref_match = re.match(
                r"^i\s+prefer\s+(.*?)(?:\s+(?:for|in|as)\s+(.+))?$",
                statement,
                flags=re.IGNORECASE
            )
            if pref_match:
                raw_val = pref_match.group(1).strip().rstrip(".!,")
                raw_key = (pref_match.group(2) or "").strip().rstrip(".!,")
                title = f"Preferred {raw_key.title()}" if raw_key else "Preferred Setting"
                value = raw_val

        # Pattern C: Allergy structure: "I am allergic to <val>"
        if not title:
            allergy_match = re.match(
                r"^(?:i\s+am\s+)?allergic\s+to\s+(.+)$",
                statement,
                flags=re.IGNORECASE
            )
            if allergy_match:
                title = "Allergy"
                value = allergy_match.group(1).strip().rstrip(".!,")

        # Pattern D: General explicit fact fallback
        if not title:
            has_pref = any(w in statement.lower() for w in ["like", "prefer", "love", "favorite", "hate"])
            title = "User Preference" if has_pref else "Important Note"
            value = statement

        # Enrich candidate
        category = memory_classifier.classify(value, context_intent, title)
        importance = importance_engine.calculate_importance(category, value)
        confidence, recommendation = confidence_engine.evaluate_confidence(value, 0.95)

        candidate = {
            "title": title,
            "value": value,
            "category": category,
            "importance": importance,
            "confidence": confidence,
            "recommendation": recommendation,
            "source": "conversation"
        }
        return candidate

    async def extract_candidates(self, user_text: str, ai_response: str, context_intent: str) -> List[Dict[str, Any]]:
        """
        Analyzes the turn and returns a list of candidate memory dictionaries.
        Resilient to AI provider timeouts, truncated responses, and format errors.
        """
        logger.info(f"[MemoryCandidateExtractor] Analyzing conversation turn for memories. Intent: {context_intent}")
        
        # 1. Pre-evaluate for explicit imperative memory commands
        explicit_candidate = self._extract_explicit_memory_candidate(user_text, context_intent)
        if explicit_candidate:
            logger.info(f"[MemoryCandidateExtractor] Detected explicit memory candidate: '{explicit_candidate['title']}' -> '{explicit_candidate['value']}'")

        candidates = []
        extracted = []

        # 2. Try LLM extraction
        prompt = (
            "Analyze the following conversation turn between an elderly user and an AI healthcare assistant. "
            "Identify if the user explicitly shared a persistent personal preference, important personal fact, "
            "family relationship, or explicitly asked the AI to remember something for the future. "
            "CRITICAL: Do NOT extract casual chit-chat, meals/what they ate, greetings, temporary remarks, or questions. "
            "Return valid JSON as a list of objects. Each object must have: "
            "'title' (short description of the fact) and 'value' (the actual fact/detail). "
            "If nothing should be remembered, return an empty list [].\n\n"
            f"User: \"{user_text}\"\nAI: \"{ai_response}\""
        )

        try:
            from llm.ai_manager import ai_manager
            res = await ai_manager.generate(prompt=prompt, max_tokens=350, temperature=0.0)
            text_resp = res.get("text", "")
            if text_resp:
                extracted = self._clean_and_parse_json(text_resp)
        except Exception as e:
            logger.warning(f"[MemoryCandidateExtractor] AI provider extraction failed/timed out: {e}")

        # 3. Enrich parsed candidates from LLM
        for item in extracted:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            value = item.get("value")
            if not title or not value:
                continue

            category = memory_classifier.classify(value, context_intent, title)
            # Filter out casual Conversation category - only persistent factual categories should be saved
            if category == "Conversation":
                logger.info(f"[MemoryCandidateExtractor] Skipping non-persistent conversation item: {title}")
                continue

            importance = importance_engine.calculate_importance(category, value)
            base_confidence = 0.9
            confidence, recommendation = confidence_engine.evaluate_confidence(value, base_confidence)

            candidate = {
                "title": title,
                "value": value,
                "category": category,
                "importance": importance,
                "confidence": confidence,
                "recommendation": recommendation,
                "source": "conversation"
            }
            candidates.append(candidate)
            logger.info(f"[MemoryCandidateExtractor] LLM extracted candidate: {candidate}")

        # 4. Fallback: If LLM returned no candidates (due to timeout, malformed output, or oversight)
        # but user gave an explicit, high-confidence memory instruction, persist it!
        if not candidates and explicit_candidate:
            logger.info(f"[MemoryCandidateExtractor] Applying deterministic fallback for explicit memory: '{explicit_candidate['title']}'")
            candidates.append(explicit_candidate)

        return candidates

memory_candidate_extractor = MemoryCandidateExtractor()
