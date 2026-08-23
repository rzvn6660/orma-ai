import sys
import os
import asyncio
import time
import pytest
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

from database import SessionLocal, Base, engine
from models.user import User
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
from intelligence.orchestrator import orchestrator
from intelligence.intent_detector import intent_detector
from intelligence.mode_resolver import mode_resolver, ExecutionMode
from llm.ai_manager import ai_manager
from llm.providers.gemini_provider import GeminiProvider

def setup_routing_test_db():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == "routing_user_55").first()
        if not user:
            user = User(
                id="routing_user_55",
                email="routing@orma.ai",
                name="Grandma Sarah",
                role="elderly"
            )
            db.add(user)
            db.commit()

        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == "routing_user_55") | 
            (MedicineReminder.subject_id == "routing_user_55")
        ).delete()
        db.commit()

        m1 = MedicineReminder(
            id=5001,
            elder_id="routing_user_55",
            subject_id="routing_user_55",
            medicine_name="Metformin",
            dosage="500 mg",
            reminder_time="08:00 AM",
            taken_status=True,
            adherence_pattern_flags="normal"
        )
        m2 = MedicineReminder(
            id=5002,
            elder_id="routing_user_55",
            subject_id="routing_user_55",
            medicine_name="Atorvastatin",
            dosage="20 mg",
            reminder_time="09:00 PM",
            taken_status=False,
            adherence_pattern_flags="normal"
        )

        db.add_all([m1, m2])
        db.commit()
    finally:
        db.close()

async def run_llm_routing_test():
    setup_routing_test_db()
    db = SessionLocal()
    test_uid = "routing_user_55"

    print("\n==================================================")
    print("ORMA AI — INTENT-BASED LLM ROUTING TEST MATRIX")
    print("==================================================")

    matrix = [
        ("What time is my next medicine?", "MEDICATION_SCHEDULE", ExecutionMode.TOOL_ONLY, False, "medication_schedule"),
        ("Am I done with my medicines today?", "MEDICATION_STATUS", ExecutionMode.LLM_WITH_TOOL, True, "medication_status"),
        ("I've had a difficult day.", "GENERAL_CONVERSATION", ExecutionMode.CONVERSATIONAL, True, "none"),
        ("I need emergency help.", "Emergency", ExecutionMode.SAFETY_DETERMINISTIC, False, "emergency_service")
    ]

    with patch.object(GeminiProvider, 'is_available', new_callable=PropertyMock, return_value=True), \
         patch.object(ai_manager.gemini, 'generate_response', new_callable=AsyncMock) as mock_gemini:
        
        mock_gemini.return_value = {
            "text": "Gemini synthetic natural response OK",
            "provider": "gemini",
            "model": "gemini-1.5-flash",
            "success": True,
            "error": None
        }

        llm_health = await ai_manager.check_health()

        for q, exp_intent, exp_mode, exp_llm_req, exp_tool in matrix:
            intent, _, _ = await intent_detector.detect_intent_with_metadata(q)
            is_next_med = "next medicine" in q.lower() or "next scheduled medicine" in q.lower()
            mode_data = mode_resolver.resolve_execution_mode(intent, q, llm_health["available"], has_next_med_query=is_next_med)

            res = await orchestrator.process_request(q, test_uid, db)

            print(f"\nQuery: \"{q}\"")
            print(f"  • Expected Mode: {exp_mode} | Actual Mode: {mode_data['mode']}")
            print(f"  • LLM Required: {mode_data['llm_required']} (Expected: {exp_llm_req})")
            print(f"  • Tool Selected: {mode_data['tool']} (Expected: {exp_tool})")
            print(f"  • Response: {res}")

            assert mode_data["mode"] == exp_mode, f"Expected {exp_mode}, got {mode_data['mode']}"
            assert mode_data["llm_required"] == exp_llm_req, f"Expected LLM required={exp_llm_req}"
            assert mode_data["tool"] == exp_tool, f"Expected tool={exp_tool}"

    print("\n==================================================")
    print("ALL INTENT-BASED LLM ROUTING TESTS PASSED SUCCESSFULLY!")
    print("==================================================\n")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_llm_routing_test())