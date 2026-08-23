import sys
import os
import asyncio
import time
import uuid
import json
from unittest.mock import AsyncMock, patch, PropertyMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure UTF-8 output formatting for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from llm.ai_manager import ai_manager
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.groq_provider import GroqProvider

def log_diagnostic_block(
    req_id: str,
    llm_required: bool,
    llm_available: bool,
    llm_called: bool,
    primary_provider: str,
    primary_model: str,
    fallback_used: bool,
    fallback_from: str,
    final_provider: str,
    final_model: str,
    latency_ms: int,
    response_received: bool,
    test_result: str
):
    print("========================================")
    print("ORMA LLM RUNTIME TEST")
    print("========================================")
    print(f"request_id: {req_id}")
    print(f"llm_required: {llm_required}")
    print(f"llm_available: {llm_available}")
    print(f"llm_called: {llm_called}")
    print(f"primary_provider: {primary_provider}")
    print(f"primary_model: {primary_model}")
    print(f"fallback_used: {fallback_used}")
    print(f"fallback_from: {fallback_from}")
    print(f"final_provider: {final_provider}")
    print(f"final_model: {final_model}")
    print(f"latency_ms: {latency_ms}")
    print(f"response_received: {response_received}")
    print(f"test_result: {test_result}")
    print("========================================\n")

async def run_step1_verification():
    print("\n--------------------------------------------------")
    print("PART 1 — INSPECT CURRENT CONFIGURATION")
    print("--------------------------------------------------")
    gemini_key_set = bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")).strip())
    groq_key_set = bool(os.environ.get("GROQ_API_KEY", "").strip())

    print(f"GEMINI_API_KEY configured: {'YES' if gemini_key_set else 'NO'}")
    print(f"GROQ_API_KEY configured: {'YES' if groq_key_set else 'NO'}")
    
    gemini_model_name = os.environ.get("AI_MODEL", "gemini-1.5-flash")
    groq_model_name = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")

    # --------------------------------------------------
    # PART 2 — REAL GEMINI GENERATION TEST
    # --------------------------------------------------
    print("\n--------------------------------------------------")
    print("PART 2 — REAL GEMINI GENERATION TEST")
    print("--------------------------------------------------")
    req_id_2 = str(uuid.uuid4())[:8]
    gemini = GeminiProvider()
    
    if gemini.is_available:
        start_t = time.time()
        res_g = await gemini.generate_response("Reply with exactly: ORMA GEMINI TEST PASSED")
        lat_g = int((time.time() - start_t) * 1000)
        gemini_success = res_g.get("success", False) and bool(res_g.get("text"))
        resp_text_g = res_g.get("text", "")
        actual_g_model = res_g.get("model", gemini_model_name)
    else:
        gemini_success = False
        lat_g = 0
        resp_text_g = ""
        actual_g_model = gemini_model_name

    log_diagnostic_block(
        req_id=req_id_2,
        llm_required=True,
        llm_available=gemini.is_available,
        llm_called=gemini.is_available,
        primary_provider="gemini",
        primary_model=actual_g_model,
        fallback_used=not gemini_success,
        fallback_from="none",
        final_provider="gemini" if gemini_success else "none",
        final_model=actual_g_model if gemini_success else "none",
        latency_ms=lat_g,
        response_received=bool(resp_text_g),
        test_result="PASS" if gemini_success else "FAIL (API Key Missing / Quota)"
    )

    # --------------------------------------------------
    # PART 3 — REAL GROQ GENERATION TEST
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("PART 3 — REAL GROQ GENERATION TEST")
    print("--------------------------------------------------")
    req_id_3 = str(uuid.uuid4())[:8]
    groq = GroqProvider()
    
    if groq.is_available:
        start_t = time.time()
        res_q = await groq.generate_response("Reply with exactly: ORMA GROQ TEST PASSED")
        lat_q = int((time.time() - start_t) * 1000)
        groq_success = res_q.get("success", False) and bool(res_q.get("text"))
        resp_text_q = res_q.get("text", "")
        actual_q_model = res_q.get("model", groq_model_name)
    else:
        groq_success = False
        lat_q = 0
        resp_text_q = ""
        actual_q_model = groq_model_name

    log_diagnostic_block(
        req_id=req_id_3,
        llm_required=True,
        llm_available=groq.is_available,
        llm_called=groq.is_available,
        primary_provider="groq",
        primary_model=actual_q_model,
        fallback_used=not groq_success,
        fallback_from="none",
        final_provider="groq" if groq_success else "none",
        final_model=actual_q_model if groq_success else "none",
        latency_ms=lat_q,
        response_received=bool(resp_text_q),
        test_result="PASS" if groq_success else "FAIL (API Key Missing / Quota)"
    )

    # --------------------------------------------------
    # PART 4 — GEMINI → GROQ FAILOVER TEST
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("PART 4 — GEMINI -> GROQ FAILOVER TEST")
    print("--------------------------------------------------")
    req_id_4 = str(uuid.uuid4())[:8]

    # Inject failure on Gemini boundary, test failover to Groq
    with patch.object(GeminiProvider, 'is_available', new_callable=PropertyMock, return_value=True), \
         patch.object(GroqProvider, 'is_available', new_callable=PropertyMock, return_value=True), \
         patch.object(ai_manager.gemini, 'generate_response', new_callable=AsyncMock) as mock_gemini, \
         patch.object(ai_manager.groq, 'generate_response', new_callable=AsyncMock) as mock_groq:
        
        mock_gemini.return_value = {"text": "", "provider": "gemini", "model": actual_g_model, "success": False, "error": "HTTP 429 Rate Limit"}
        mock_groq.return_value = {"text": "ORMA GROQ FAILOVER TEST PASSED", "provider": "groq", "model": actual_q_model, "success": True, "error": None}

        start_t = time.time()
        res_fo = await ai_manager.generate("Reply with test")
        lat_fo = int((time.time() - start_t) * 1000)
        fo_success = res_fo.get("provider") == "groq" and res_fo.get("success") is True

        log_diagnostic_block(
            req_id=req_id_4,
            llm_required=True,
            llm_available=True,
            llm_called=True,
            primary_provider="gemini",
            primary_model=actual_g_model,
            fallback_used=True,
            fallback_from="gemini",
            final_provider=res_fo.get("provider", "groq"),
            final_model=res_fo.get("model", actual_q_model),
            latency_ms=lat_fo,
            response_received=bool(res_fo.get("text")),
            test_result="PASS" if fo_success else "FAIL"
        )

    # --------------------------------------------------
    # PART 5 — BOTH PROVIDERS FAILED TEST
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("PART 5 — BOTH PROVIDERS FAILED TEST")
    print("--------------------------------------------------")
    req_id_5 = str(uuid.uuid4())[:8]

    with patch.object(GeminiProvider, 'is_available', new_callable=PropertyMock, return_value=True), \
         patch.object(GroqProvider, 'is_available', new_callable=PropertyMock, return_value=True), \
         patch.object(ai_manager.gemini, 'generate_response', new_callable=AsyncMock) as mock_gemini, \
         patch.object(ai_manager.groq, 'generate_response', new_callable=AsyncMock) as mock_groq:
        
        mock_gemini.return_value = {"text": "", "provider": "gemini", "model": actual_g_model, "success": False, "error": "Quota Exceeded"}
        mock_groq.return_value = {"text": "", "provider": "groq", "model": actual_q_model, "success": False, "error": "Service Unavailable"}

        start_t = time.time()
        res_fb = await ai_manager.generate("User query about schedule")
        lat_fb = int((time.time() - start_t) * 1000)
        fb_success = res_fb.get("provider") == "fallback" and res_fb.get("success") is True

        log_diagnostic_block(
            req_id=req_id_5,
            llm_required=True,
            llm_available=False,
            llm_called=False,
            primary_provider="gemini",
            primary_model=actual_g_model,
            fallback_used=True,
            fallback_from="groq",
            final_provider="fallback",
            final_model="rule-fallback-1.0",
            latency_ms=lat_fb,
            response_received=bool(res_fb.get("text")),
            test_result="PASS" if fb_success else "FAIL"
        )

    # Return summary diagnostic details
    return {
        "gemini_key_set": gemini_key_set,
        "groq_key_set": groq_key_set,
        "gemini_success": gemini_success,
        "groq_success": groq_success,
        "failover_success": fo_success,
        "both_fallback_success": fb_success,
        "gemini_model": actual_g_model,
        "groq_model": actual_q_model,
        "gemini_latency": lat_g,
        "groq_latency": lat_q
    }

if __name__ == "__main__":
    asyncio.run(run_step1_verification())