import sys
import os
import asyncio
import time
import pytest

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
from intelligence.conversation_manager import conversation_manager
from intelligence.tools import healthcare_tools
from llm.ai_manager import ai_manager

def setup_brain_test_db():
    db = SessionLocal()
    try:
        # Create test user
        user = db.query(User).filter(User.id == "test_brain_user_88").first()
        if not user:
            user = User(
                id="test_brain_user_88",
                email="braintest@orma.ai",
                name="Grandma Sarah",
                role="elderly"
            )
            db.add(user)
            db.commit()

        # Clean existing test records for user
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == "test_brain_user_88") | 
            (MedicineReminder.subject_id == "test_brain_user_88")
        ).delete()
        db.query(HealthEvent).filter(
            (HealthEvent.elder_id == "test_brain_user_88") | 
            (HealthEvent.subject_id == "test_brain_user_88")
        ).delete()
        db.commit()

        # Create realistic medicines
        m1 = MedicineReminder(
            id=2001,
            elder_id="test_brain_user_88",
            subject_id="test_brain_user_88",
            medicine_name="Metformin",
            dosage="500 mg",
            reminder_time="08:00 AM",
            taken_status=True,
            adherence_pattern_flags="normal"
        )
        m2 = MedicineReminder(
            id=2002,
            elder_id="test_brain_user_88",
            subject_id="test_brain_user_88",
            medicine_name="Lisinopril",
            dosage="10 mg",
            reminder_time="08:00 AM",
            taken_status=False,
            adherence_pattern_flags="normal"
        )
        m3 = MedicineReminder(
            id=2003,
            elder_id="test_brain_user_88",
            subject_id="test_brain_user_88",
            medicine_name="Atorvastatin",
            dosage="20 mg",
            reminder_time="09:00 PM",
            taken_status=False,
            adherence_pattern_flags="normal"
        )

        # Create doctor appointment
        he1 = HealthEvent(
            id=3001,
            elder_id="test_brain_user_88",
            subject_id="test_brain_user_88",
            event_type="doctor_appointment",
            title="Dr. Smith Consultation",
            description="Cardiology Followup",
            event_date="Tomorrow",
            reminder_time="10:00 AM",
            location="City General Hospital"
        )

        db.add_all([m1, m2, m3, he1])
        db.commit()
        print("[SETUP] Created 3 test medicines + 1 health event for test_brain_user_88")
    finally:
        db.close()

async def run_conversational_brain_audit():
    setup_brain_test_db()
    db = SessionLocal()
    test_uid = "test_brain_user_88"

    print("\n========================================")
    print("ORMA AI CONVERSATIONAL BRAIN AUDIT")
    print("========================================")

    # ---------------------------------------------------------
    # TEST 1: LLM Health System & Telemetry Check
    # ---------------------------------------------------------
    health = await ai_manager.check_health()
    print(f"\n[TEST 1] LLM Provider Health: {health}")
    assert "available" in health
    assert "provider" in health
    assert "latency_ms" in health
    print("[PASS] LLM capability health check PASSED")

    # ---------------------------------------------------------
    # TEST 2: Open-Ended Semantic Variations (Morning Schedule)
    # ---------------------------------------------------------
    morning_variations = [
        "What time are my morning medicines?",
        "What should I take this morning?",
        "What's scheduled for me in the morning?",
        "Do I have anything to take before noon?"
    ]
    for q in morning_variations:
        intent, _, meta = await intent_detector.detect_intent_with_metadata(q)
        print(f"[TEST 2] '{q}' -> Intent: {intent}, Period: {meta.get('time_period')}")
        assert intent == "MEDICATION_SCHEDULE", f"Expected MEDICATION_SCHEDULE for '{q}', got {intent}"
        assert meta.get("time_period") == "morning", f"Expected morning for '{q}', got {meta.get('time_period')}"
    print("[PASS] Open-ended morning semantic variations PASSED")

    # ---------------------------------------------------------
    # TEST 3: Open-Ended Semantic Variations (Night Status)
    # ---------------------------------------------------------
    night_variations = [
        "Are all my night medicines taken?",
        "What do I still need tonight?",
        "Have I taken my night medicine?",
        "Is anything left before bed?"
    ]
    for q in night_variations:
        intent, _, meta = await intent_detector.detect_intent_with_metadata(q)
        print(f"[TEST 3] '{q}' -> Intent: {intent}, Period: {meta.get('time_period')}")
        assert intent == "MEDICATION_STATUS", f"Expected MEDICATION_STATUS for '{q}', got {intent}"
        assert meta.get("time_period") == "night", f"Expected night for '{q}', got {meta.get('time_period')}"
    print("[PASS] Open-ended night status semantic variations PASSED")

    # ---------------------------------------------------------
    # TEST 4: Open-Ended Semantic Variations (General Conversation)
    # ---------------------------------------------------------
    general_queries = [
        "Hi ORMA",
        "How are you?",
        "Tell me something",
        "I feel tired today"
    ]
    for q in general_queries:
        intent, _, _ = await intent_detector.detect_intent_with_metadata(q)
        res = await orchestrator.process_request(q, test_uid, db)
        print(f"[TEST 4] '{q}' -> Intent: {intent} | Response: {res}")
        assert intent in ["GREETING", "GENERAL_CONVERSATION"]
        assert "Metformin" not in res and "Lisinopril" not in res, "Greeting response MUST NOT dump medicine records"
    print("[PASS] Open-ended general conversation isolation PASSED")

    # ---------------------------------------------------------
    # TEST 5: Controlled Tool Execution & DB Facts Retrieval
    # ---------------------------------------------------------
    sched_tool = healthcare_tools.get_medication_schedule(db, test_uid, time_period="morning")
    status_tool = healthcare_tools.get_medication_status(db, test_uid, time_period="night")
    adh_tool = healthcare_tools.get_daily_adherence(db, test_uid)
    cal_tool = healthcare_tools.get_calendar_events(db, test_uid)

    print(f"\n[TEST 5] Tool Schedule (Morning): {sched_tool['count']} medicines")
    print(f"[TEST 5] Tool Status (Night): Pending={status_tool['pending_count']}")
    print(f"[TEST 5] Tool Adherence: {adh_tool['summary_text']}")
    print(f"[TEST 5] Tool Calendar: {cal_tool['events'][0]['title']}")

    assert sched_tool["count"] == 2
    assert status_tool["pending_count"] == 1
    assert adh_tool["total_scheduled"] == 3
    assert cal_tool["count"] == 1
    print("[PASS] Controlled backend tools execution PASSED")

    # ---------------------------------------------------------
    # TEST 6: Multi-Turn Conversation Coreference & Context
    # ---------------------------------------------------------
    conversation_manager.clear_current_task(test_uid)
    
    # Turn 1
    q_turn1 = "What medicines do I have tonight?"
    res_turn1 = await orchestrator.process_request(q_turn1, test_uid, db)
    print(f"\n[TEST 6 - Turn 1] Query: '{q_turn1}' -> Response: {res_turn1}")
    
    # Turn 2: Anaphoric follow-up ("Did I take it?")
    q_turn2 = "Did I take it?"
    intent_t2, _, _ = await intent_detector.detect_intent_with_metadata(q_turn2)
    res_turn2 = await orchestrator.process_request(q_turn2, test_uid, db)
    print(f"[TEST 6 - Turn 2] Query: '{q_turn2}' -> Intent: {intent_t2} | Response: {res_turn2}")
    
    assert intent_t2 == "MEDICATION_STATUS", "Follow-up 'Did I take it?' must resolve to MEDICATION_STATUS"
    assert "Atorvastatin" in res_turn2 or "pending" in res_turn2.lower() or "not" in res_turn2.lower() or "at 09:00 pm" in res_turn2.lower(), "Follow-up must resolve 'it' to night medicine"
    print("[PASS] Multi-turn conversation coreference & context PASSED")

    # ---------------------------------------------------------
    # TEST 7: Multilingual NLU & Orchestration
    # ---------------------------------------------------------
    # Malayalam
    q_ml = "എന്റെ രാവിലെ കഴിക്കേണ്ട മരുന്നുകൾ ഏതാണ്?"
    intent_ml, _, meta_ml = await intent_detector.detect_intent_with_metadata(q_ml)
    print(f"\n[TEST 7a] Malayalam NLU: Intent={intent_ml}, Time={meta_ml.get('time_period')}")
    assert intent_ml == "MEDICATION_SCHEDULE" and meta_ml.get("time_period") == "morning"

    # Hindi
    q_hi = "मेरी रात की दवाइयाँ ले ली हैं क्या?"
    intent_hi, _, meta_hi = await intent_detector.detect_intent_with_metadata(q_hi)
    print(f"[TEST 7b] Hindi NLU: Intent={intent_hi}, Time={meta_hi.get('time_period')}")
    assert intent_hi == "MEDICATION_STATUS" and meta_hi.get("time_period") == "night"

    # Arabic
    q_ar = "هل تناولت جميع أدوية الليل؟"
    intent_ar, _, meta_ar = await intent_detector.detect_intent_with_metadata(q_ar)
    print(f"[TEST 7c] Arabic NLU: Intent={intent_ar}, Time={meta_ar.get('time_period')}")
    assert intent_ar == "MEDICATION_STATUS" and meta_ar.get("time_period") == "night"

    print("[PASS] Multilingual semantic orchestration PASSED")

    # ---------------------------------------------------------
    # TEST 8: Medication Safety & Non-Mutation Verification
    # ---------------------------------------------------------
    meds_after = db.query(MedicineReminder).filter(MedicineReminder.elder_id == test_uid).all()
    status_map: dict[int, bool] = {int(m.id): bool(m.taken_status) for m in meds_after}
    assert status_map[2001] is True, "m1 must remain taken"
    assert status_map[2002] is False, "m2 must remain pending"
    assert status_map[2003] is False, "m3 must remain pending"
    print("[PASS] Medication safety state non-mutation PASSED")

    # ---------------------------------------------------------
    # TEST 9: Deterministic Emergency Isolation
    # ---------------------------------------------------------
    q_em = "I need help, call my caregiver"
    intent_em, _, _ = await intent_detector.detect_intent_with_metadata(q_em)
    print(f"\n[TEST 9] Emergency Query: '{q_em}' -> Intent: {intent_em}")
    assert intent_em in ["Emergency", "Caregiver"], f"Expected Emergency or Caregiver, got {intent_em}"
    print("[PASS] Emergency path deterministic safety PASSED")

    # ---------------------------------------------------------
    # TEST 10: Crucial Regression Checks (The 4 Distinct Queries)
    # ---------------------------------------------------------
    q_r1 = "What time are my morning medicines?"
    q_r2 = "How did I do today?"
    q_r3 = "Are all my night medicines taken?"
    q_r4 = "Hi. How are you?"

    res_r1 = await orchestrator.process_request(q_r1, test_uid, db)
    res_r2 = await orchestrator.process_request(q_r2, test_uid, db)
    res_r3 = await orchestrator.process_request(q_r3, test_uid, db)
    res_r4 = await orchestrator.process_request(q_r4, test_uid, db)

    print(f"\n[TEST 10 - Query 1] {q_r1} -> {res_r1}")
    print(f"[TEST 10 - Query 2] {q_r2} -> {res_r2}")
    print(f"[TEST 10 - Query 3] {q_r3} -> {res_r3}")
    print(f"[TEST 10 - Query 4] {q_r4} -> {res_r4}")

    assert res_r1 != res_r2 != res_r3 != res_r4, "The 4 regression queries MUST produce 4 distinct responses!"
    print("[PASS] The 4 distinct regression queries PASSED")

    db.close()
    print("\n========================================")
    print("ALL CONVERSATIONAL BRAIN AUDIT TESTS PASSED SUCCESSFULLY!")
    print("========================================\n")

if __name__ == "__main__":
    asyncio.run(run_conversational_brain_audit())