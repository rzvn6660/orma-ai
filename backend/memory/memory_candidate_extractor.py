import logging
import httpx
import json
from typing import List, Dict, Any
from memory.memory_classifier import memory_classifier
from memory.importance_engine import importance_engine
from memory.confidence_engine import confidence_engine

logger = logging.getLogger(__name__)

class MemoryCandidateExtractor:
    """
    Analyzes conversation transcripts to identify potential memory candidates.
    Does NOT store anything. Just prepares the structured candidates.
    """
    def __init__(self):
        pass

    async def extract_candidates(self, user_text: str, ai_response: str, context_intent: str) -> List[Dict[str, Any]]:
        """
        Analyzes the turn and returns a list of candidate memory dictionaries.
        """
        logger.info("[MemoryCandidateExtractor] Analyzing conversation turn for potential memories.")
        
        prompt = (
            "Analyze the following conversation turn between a user and an AI assistant. "
            "Identify if the user shared any factual personal information, preferences, health data, "
            "relationships, or events that the AI should remember for the future. "
            "Return valid JSON as a list of objects. Each object must have: "
            "'title' (short description of the fact) and 'value' (the actual fact/detail). "
            "If nothing should be remembered, return an empty list [].\n\n"
            f"User: \"{user_text}\"\nAI: \"{ai_response}\""
        )

        candidates = []
        try:
            from llm.ai_manager import ai_manager
            res = await ai_manager.generate(prompt=prompt, max_tokens=200)
            text_resp = res.get("text", "")
            extracted = []
            if text_resp:
                start = text_resp.find('[')
                end = text_resp.rfind(']')
                if start != -1 and end != -1:
                    json_str = text_resp[start:end+1]
                    try:
                        extracted = json.loads(json_str)
                        if isinstance(extracted, dict):
                            extracted = [extracted]
                    except Exception:
                        extracted = []
                        
            for item in extracted:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                value = item.get("value")
                if not title or not value:
                    continue
                    
                # Enrich the candidate using the engines
                category = memory_classifier.classify(value, context_intent)
                importance = importance_engine.calculate_importance(category, value)
                
                # Base extraction confidence can be assumed high if LLM extracted it clearly
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
                logger.info(f"[MemoryCandidateExtractor] Extracted candidate: {candidate}")
                        
        except Exception as e:
            logger.error(f"[MemoryCandidateExtractor] Extraction failed: {e}")
            
        return candidates

memory_candidate_extractor = MemoryCandidateExtractor()
