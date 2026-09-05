import os
import asyncio
import logging
import time
import uuid
import httpx
from typing import Dict, Any, Optional
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)

class GroqProvider(BaseAIProvider):
    """
    Groq API Provider - Fast, free-tier hosted LLMs (e.g. llama-3.3-70b-versatile or compound-mini).
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY", "")
        configured_model = model or os.environ.get("GROQ_MODEL") or os.environ.get("AI_MODEL", "qwen/qwen3.8-27b")
        if configured_model in ("llama-3.3-70b-versatile", "groq/compound-mini"):
            configured_model = "qwen/qwen3.8-27b"
        self.model = configured_model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        try:
            curr_loop = asyncio.get_running_loop()
        except RuntimeError:
            curr_loop = None
        if self._client is None or self._client.is_closed or getattr(self, "_client_loop", None) != curr_loop:
            self._client = httpx.AsyncClient(timeout=8.0)
            self._client_loop = curr_loop
        return self._client

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.3,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        req_id = request_id or str(uuid.uuid4())[:8]
        t_start = time.perf_counter()

        if not self.is_available:
            t_end = time.perf_counter()
            return {
                "text": "",
                "provider": self.provider_name,
                "model": self.model,
                "success": False,
                "error": "GROQ_API_KEY missing",
                "error_type": "API_KEY_MISSING",
                "status": "PROVIDER_UNAVAILABLE",
                "request_id": req_id,
                "start_time": t_start,
                "end_time": t_end,
                "latency_ms": (t_end - t_start) * 1000
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max(max_tokens, 250),
            "temperature": temperature
        }

        try:
            client = self._get_client()
            resp = await client.post(self.base_url, headers=headers, json=payload)
            t_end = time.perf_counter()
            lat_ms = (t_end - t_start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                    content = choices[0]["message"]["content"].strip()
                    return {
                        "text": content,
                        "provider": self.provider_name,
                        "model": self.model,
                        "success": True,
                        "error": None,
                        "error_type": None,
                        "status": "PASS",
                        "request_id": req_id,
                        "start_time": t_start,
                        "end_time": t_end,
                        "latency_ms": lat_ms
                    }
                return {
                    "text": "",
                    "provider": self.provider_name,
                    "model": self.model,
                    "success": False,
                    "error": "No content in choice",
                    "error_type": "NO_CONTENT",
                    "status": "FAILED",
                    "request_id": req_id,
                    "start_time": t_start,
                    "end_time": t_end,
                    "latency_ms": lat_ms
                }
            elif resp.status_code == 429:
                logger.warning(f"[AI_PROVIDER req_{req_id}] Groq rate limit hit (429)")
                return {
                    "text": "",
                    "provider": self.provider_name,
                    "model": self.model,
                    "success": False,
                    "error": "Rate limit exceeded (429)",
                    "error_type": "RATE_LIMIT_429",
                    "status": "PROVIDER_UNAVAILABLE",
                    "request_id": req_id,
                    "start_time": t_start,
                    "end_time": t_end,
                    "latency_ms": lat_ms
                }
            else:
                resp_text = resp.text[:200]
                err_type = "HIGH_TRAFFIC_503" if ("high traffic" in resp_text.lower() or resp.status_code == 503) else f"HTTP_{resp.status_code}"
                logger.warning(f"[AI_PROVIDER req_{req_id}] Groq HTTP {resp.status_code}: {resp_text}")
                return {
                    "text": "",
                    "provider": self.provider_name,
                    "model": self.model,
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp_text}",
                    "error_type": err_type,
                    "status": "PROVIDER_UNAVAILABLE",
                    "request_id": req_id,
                    "start_time": t_start,
                    "end_time": t_end,
                    "latency_ms": lat_ms
                }
        except httpx.TimeoutException as te:
            t_end = time.perf_counter()
            lat_ms = (t_end - t_start) * 1000
            logger.warning(f"[AI_PROVIDER req_{req_id}] Groq timeout exception: {te}")
            return {
                "text": "",
                "provider": self.provider_name,
                "model": self.model,
                "success": False,
                "error": f"Timeout: {str(te)}",
                "error_type": "TIMEOUT",
                "status": "PROVIDER_UNAVAILABLE",
                "request_id": req_id,
                "start_time": t_start,
                "end_time": t_end,
                "latency_ms": lat_ms
            }
        except Exception as e:
            t_end = time.perf_counter()
            lat_ms = (t_end - t_start) * 1000
            err_str = str(e)
            err_type = "NETWORK_ERROR" if ("getaddrinfo" in err_str or "connect" in err_str.lower()) else "EXCEPTION"
            logger.warning(f"[AI_PROVIDER req_{req_id}] Groq exception: {e}")
            return {
                "text": "",
                "provider": self.provider_name,
                "model": self.model,
                "success": False,
                "error": err_str,
                "error_type": err_type,
                "status": "PROVIDER_UNAVAILABLE",
                "request_id": req_id,
                "start_time": t_start,
                "end_time": t_end,
                "latency_ms": lat_ms
            }

