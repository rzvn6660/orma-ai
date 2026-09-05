import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Authoritative backend/.env environment loader
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .providers.base_provider import BaseAIProvider
from .providers.groq_provider import GroqProvider
from .providers.gemini_provider import GeminiProvider
from .providers.ollama_provider import OllamaProvider
from .providers.fallback_provider import FallbackProvider

logger = logging.getLogger(__name__)

class AIManager:
    """
    Central Manager for ORMA AI LLM providers with Groq primary,
    Gemini secondary failover, health checks, latency measurement, and safety enforcement.
    """
    def __init__(self):
        self.primary_name = os.environ.get("PRIMARY_LLM_PROVIDER", os.environ.get("AI_PROVIDER", "groq")).lower()
        self.groq = GroqProvider()
        self.gemini = GeminiProvider()
        self.ollama = OllamaProvider()
        self.fallback = FallbackProvider()

    def _get_provider_chain(self) -> List[BaseAIProvider]:
        chain = []
        
        if self.primary_name == "gemini":
            chain = [self.gemini, self.groq, self.ollama, self.fallback]
        elif self.primary_name == "ollama":
            chain = [self.ollama, self.groq, self.gemini, self.fallback]
        else: # Default ("groq" or "auto") - Groq primary, Gemini secondary fallback
            chain = [self.groq, self.gemini, self.ollama, self.fallback]

        result = []
        seen = set()
        for p in chain:
            if p.provider_name not in seen:
                seen.add(p.provider_name)
                result.append(p)
        return result

    async def check_health(self) -> Dict[str, Any]:
        """
        Fast, non-blocking LLM provider health check.
        Returns provider availability, primary/secondary names, model name, and latency in ms.
        """
        start_time = time.time()
        providers = self._get_provider_chain()
        
        active_llms = [p for p in providers if p.provider_name != "fallback" and p.is_available]
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if active_llms:
            primary = active_llms[0]
            secondary = active_llms[1].provider_name if len(active_llms) > 1 else "fallback"
            return {
                "available": True,
                "provider": primary.provider_name,
                "secondary_provider": secondary,
                "model": getattr(primary, "model_name", primary.provider_name),
                "latency_ms": latency_ms,
                "reason": f"Primary provider '{primary.provider_name}' active and reachable."
            }
            
        return {
            "available": False,
            "provider": "fallback",
            "secondary_provider": "none",
            "model": "rule-fallback-1.0",
            "latency_ms": latency_ms,
            "reason": "No cloud or local LLM provider configured/reachable. Fallback active."
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Executes request through Gemini primary -> Groq secondary failover chain.
        Returns generation result with latency and failover metadata.
        """
        start_t = time.time()
        providers = self._get_provider_chain()
        
        safety_notice = (
            "\n\nMEDICAL SAFETY RULE:\n"
            "Never claim that a user has taken a medicine unless the database context explicitly states it is confirmed/taken.\n"
            "Keep answers concise, direct, clear, warm, and reassuring."
        )
        full_system = f"{system_prompt}{safety_notice}" if system_prompt else safety_notice

        first_tried = None

        for provider in providers:
            if not provider.is_available and provider.provider_name != "fallback":
                continue
                
            if first_tried is None and provider.provider_name != "fallback":
                first_tried = provider.provider_name

            logger.info(f"[AI_MANAGER] Attempting generation with provider '{provider.provider_name}'")
            p_start = time.time()
            try:
                res = await provider.generate_response(
                    prompt=prompt,
                    system_prompt=full_system,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            except Exception as e:
                logger.warning(f"[AI_MANAGER] Provider '{provider.provider_name}' raised exception: {e}. Trying next provider...")
                continue
            p_latency = int((time.time() - p_start) * 1000)
            
            if res.get("success") and res.get("text"):
                logger.info(f"[AI_MANAGER] Generation successful via '{provider.provider_name}' (model={res.get('model')}, latency={p_latency}ms)")
                res["latency_ms"] = p_latency
                res["llm_called"] = True if provider.provider_name != "fallback" else False
                if first_tried and first_tried != provider.provider_name:
                    res["fallback_from"] = first_tried
                return res
            else:
                logger.warning(f"[AI_MANAGER] Provider '{provider.provider_name}' failed: {res.get('error')}. Trying next provider...")

        # Ultimate fallback guarantee
        fb_res = await self.fallback.generate_response(prompt=prompt, system_prompt=system_prompt)
        fb_res["latency_ms"] = int((time.time() - start_t) * 1000)
        fb_res["llm_called"] = False
        fb_res["fallback_used"] = True
        return fb_res

ai_manager = AIManager()
