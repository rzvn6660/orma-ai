import os
import logging
import httpx
from typing import Dict, Any, Optional
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseAIProvider):
    """
    Ollama Provider - Open source local execution (llama3, qwen2.5, mistral, etc.). No API keys required.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.environ.get("AI_MODEL", "llama3")

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        # Only mark available if explicitly enabled via environment variable
        return os.environ.get("OLLAMA_ENABLED", "false").lower() in ("true", "1")

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        url = f"{self.base_url.rstrip('/')}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=8.0)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("response", "").strip()
                    return {"text": content, "provider": self.provider_name, "model": self.model, "success": True, "error": None}
                else:
                    return {"text": "", "provider": self.provider_name, "model": self.model, "success": False, "error": f"Ollama HTTP {resp.status_code}"}
        except Exception as e:
            logger.debug(f"[AI_PROVIDER] Ollama not accessible at {self.base_url}: {e}")
            return {"text": "", "provider": self.provider_name, "model": self.model, "success": False, "error": "Ollama service unavailable"}
