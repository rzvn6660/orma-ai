import logging
import httpx
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ResponseCoordinator:
    """
    Merges outputs from agents, missing fields, and context into a coherent, elderly-friendly response.
    """
    def __init__(self):
        pass

    async def generate_response(self, text: str, intent: str, validation_decision: str, 
                                validation_reason: str, missing_fields: List[str], 
                                route_result: Dict[str, Any], language: str = "en",
                                memory_context: str = "", conflict: Dict[str, Any] = None) -> str:
        """
        Synthesizes the final conversational response.
        """
        logger.info(f"[ResponseCoordinator] Generating response for intent '{intent}' | Decision: {validation_decision}")
        
        # 0. Handle Conflicts first
        if validation_decision == "Conflict" and conflict:
            existing_value = conflict.get("existing_value")
            new_value = conflict.get("new_value")
            return f"You previously told me your info was {existing_value}. Would you like me to update this memory to {new_value}?"

        # 1. Handle Clarification
        if validation_decision == "Clarify":
            fields_str = ", ".join(missing_fields)
            prompt = (
                "You are an AI assistant for elderly users. The user wanted to complete a task, "
                f"but is missing this information: {fields_str}. "
                "Ask them gently to provide the missing information in a very short, polite sentence. "
                "Do not use robotic language like 'missing fields'.\n"
                f"{memory_context}\n"
                f"User said: {text}\nResponse:"
            )
            return await self._call_llm_text(prompt, language)

        # 2. Handle Rejection / Escalation
        if validation_decision in ["Reject", "Escalate"]:
            return "I have notified your caregiver about this to ensure you are safe."

        # 3. Handle Success from Router
        if route_result and route_result.get("status") == "success":
            action = route_result.get("action")
            data = route_result.get("data", {})
            explain = route_result.get("explainability", {})
            reason = explain.get("reason", "")
            follow_up = explain.get("suggested_follow_up", "")
            
            prompt_context = f"The system successfully performed this action: {action}. Reason: {reason}."
            if follow_up:
                prompt_context += f" Suggest this follow up to the user naturally: {follow_up}"

            if action == "created_health_event":
                title = data.get("title", "event")
                return f"Okay, I have scheduled {title} for you. {follow_up}".strip()
            elif action == "emergency_alert_sent":
                return f"I have alerted your family. Help will be there soon. {follow_up}".strip()
            elif action == "chat":
                # Regular chat response generation using LLM
                prompt = (
                    "You are Orma, a calm, supportive AI for elderly users. "
                    "Keep your response extremely short (1-2 sentences). Be clear and polite.\n"
                    f"{memory_context}\n"
                    f"System context: {prompt_context}\n"
                    f"User: {text}\nOrma:"
                )
                return await self._call_llm_text(prompt, language)

        # 4. Fallback
        return "I am here to help you."

    async def _call_llm_text(self, prompt: str, language: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 50}
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"[ResponseCoordinator] LLM failed: {e}")
            
        return "Can you please repeat that?"

response_coordinator = ResponseCoordinator()
