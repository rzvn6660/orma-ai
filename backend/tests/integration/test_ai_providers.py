import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
import pytest
import os
from llm.ai_manager import ai_manager
from llm.providers.groq_provider import GroqProvider
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.ollama_provider import OllamaProvider
from llm.providers.fallback_provider import FallbackProvider

@pytest.mark.asyncio
async def test_fallback_provider():
    provider = FallbackProvider()
    res = await provider.generate_response("Hello Orma")
    assert res["success"] is True
    assert "Hello" in res["text"] or "Orma" in res["text"] or "assist" in res["text"]

@pytest.mark.asyncio
async def test_ai_manager_fallback():
    # Force auto mode without keys
    res = await ai_manager.generate("Are my medicines due?")
    assert res["success"] is True
    assert res["text"] != ""
    assert res["provider"] in ["groq", "gemini", "ollama", "fallback"]

def test_provider_availability():
    groq = GroqProvider(api_key="")
    assert groq.is_available is False
    
    gemini = GeminiProvider(api_key="")
    assert gemini.is_available is False
    
    fallback = FallbackProvider()
    assert fallback.is_available is True
