import sys
import os
import asyncio
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
from intelligence.orchestrator import orchestrator
from intelligence.intent_detector import intent_detector

def setup_test_db():
    db = SessionLocal()
    try:
        # Create test user
        user = db.query(User).filter(User.id == "test_intent_user_99").first()
        if not user:
            user = User(
                id="test_intent_user_99",
                email="intenttest@orma.ai",
                name="Intent Test Elder",
                role="elderly"
            )
            db.add(user)
            db.commit()

        # Clean existing medicines for test user
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == "test_intent_user_99") | 
            (MedicineReminder.subject_id == "test_intent_user_99")
        ).delete()
        db.commit()

        # Create realistic morning and night medicine records
        med1 = MedicineReminder(
            id=1001,
            elder_id="test_intent_user_99",
            subject_id="test_intent_user_99",
            medicine_name="TEST2",
            dosage="10mg",
            reminder_time="08:00 AM",
            taken_status=True, # Morning medicine 1 taken
            adherence_pattern_flags="normal"
        )
        med2 = MedicineReminder(
            id=1002,
            elder_id="test_intent_user_99",
            subject_id="test_intent_user_99",
            medicine_name="TEST3",
            dosage="20mg",
            reminder_time="08:00 AM",
            taken_status=False, # Morning medicine 2 pending
            adherence_pattern_flags="normal"
        )
        med3 = MedicineReminder(
            id=1003,
            elder_id="test_intent_user_99",
            subject_id="test_intent_user_99",
            medicine_name="TEST_LIVE",
            dosage="50mg",
            reminder_time="21:00", # 09:00 PM Night medicine pending
            taken_status=False,
            adherence_pattern_flags="normal"
        )

        db.add_all([med1, med2, med3])
        db.commit()
        print("[SETUP] Created 3 test medicines (1 morning taken, 1 morning pending, 1 night pending)")
    finally:
        db.close()

async def run_intent_audit():
    setup_test_db()
    db = SessionLocal()

    test_user_id = "test_intent_user_99"

    print("\n========================================")
    print("ORMA AI CONVERSATIONAL INTENT AUDIT")
    print("========================================")

    # ---------------------------------------------------------
    # TEST 1: Morning Medication Schedule
    # ---------------------------------------------------------
    q1 = "What time are my morning medicines?"
    intent1, conf1, meta1 = await intent_detector.detect_intent_with_metadata(q1)
    res1 = await orchestrator.process_request(q1, test_user_id, db)
    
    print(f"\n[TEST 1] Query: '{q1}'")
    print(f"Detected Intent: {intent1} | TimePeriod: {meta1.get('time_period')}")
    print(f"Response: {res1}")
    
    assert intent1 == "MEDICATION_SCHEDULE", f"Expected MEDICATION_SCHEDULE, got {intent1}"
    assert meta1.get("time_period") == "morning", f"Expected morning, got {meta1.get('time_period')}"
    print("[PASS] Morning medication schedule test PASSED")

    # ---------------------------------------------------------
    # TEST 2: Night Medication Status
    # ---------------------------------------------------------
    q2 = "Are all my night medicines taken?"
    intent2, conf2, meta2 = await intent_detector.detect_intent_with_metadata(q2)
    res2 = await orchestrator.process_request(q2, test_user_id, db)
    
    print(f"\n[TEST 2] Query: '{q2}'")
    print(f"Detected Intent: {intent2} | TimePeriod: {meta2.get('time_period')}")
    print(f"Response: {res2}")
    
    assert intent2 == "MEDICATION_STATUS", f"Expected MEDICATION_STATUS, got {intent2}"
    assert meta2.get("time_period") == "night", f"Expected night, got {meta2.get('time_period')}"
    print("[PASS] Night medication status test PASSED")

    # ---------------------------------------------------------
    # TEST 3: Daily Adherence Summary
    # ---------------------------------------------------------
    q3 = "How did I do today?"
    intent3, conf3, meta3 = await intent_detector.detect_intent_with_metadata(q3)
    res3 = await orchestrator.process_request(q3, test_user_id, db)
    
    print(f"\n[TEST 3] Query: '{q3}'")
    print(f"Detected Intent: {intent3} | TimePeriod: {meta3.get('time_period')}")
    print(f"Response: {res3}")
    
    assert intent3 == "MEDICATION_SUMMARY", f"Expected MEDICATION_SUMMARY, got {intent3}"
    print("[PASS] Daily adherence summary test PASSED")

    # ---------------------------------------------------------
    # TEST 4: General Greeting / Conversation
    # ---------------------------------------------------------
    q4 = "Hi. How do we do?"
    intent4, conf4, meta4 = await intent_detector.detect_intent_with_metadata(q4)
    res4 = await orchestrator.process_request(q4, test_user_id, db)
    
    print(f"\n[TEST 4] Query: '{q4}'")
    print(f"Detected Intent: {intent4}")
    print(f"Response: {res4}")
    
    assert intent4 in ["GREETING", "GENERAL_CONVERSATION"], f"Expected GREETING or GENERAL_CONVERSATION, got {intent4}"
    assert "TEST2" not in res4 and "TEST3" not in res4 and "TEST_LIVE" not in res4, "Greeting MUST NOT list medication details"
    print("[PASS] General greeting test PASSED")

    # ---------------------------------------------------------
    # TEST 5: Multilingual Intent Detection
    # ---------------------------------------------------------
    # Malayalam
    q_ml = "എന്റെ രാവിലെ കഴിക്കേണ്ട മരുന്നുകൾ ഏതാണ്?"
    intent_ml, _, meta_ml = await intent_detector.detect_intent_with_metadata(q_ml)
    print(f"\n[TEST 5a] Malayalam Query: '{q_ml}' -> Intent: {intent_ml}, Time: {meta_ml.get('time_period')}")
    assert intent_ml == "MEDICATION_SCHEDULE" and meta_ml.get("time_period") == "morning"

    # Hindi
    q_hi = "मेरी रात की दवाइयाँ ले ली हैं क्या?"
    intent_hi, _, meta_hi = await intent_detector.detect_intent_with_metadata(q_hi)
    print(f"[TEST 5b] Hindi Query: '{q_hi}' -> Intent: {intent_hi}, Time: {meta_hi.get('time_period')}")
    assert intent_hi == "MEDICATION_STATUS" and meta_hi.get("time_period") == "night"

    # Arabic
    q_ar = "هل تناولت جميع أدوية الليل؟"
    intent_ar, _, meta_ar = await intent_detector.detect_intent_with_metadata(q_ar)
    print(f"[TEST 5c] Arabic Query: '{q_ar}' -> Intent: {intent_ar}, Time: {meta_ar.get('time_period')}")
    assert intent_ar == "MEDICATION_STATUS" and meta_ar.get("time_period") == "night"

    print("[PASS] Multilingual intent classification tests PASSED")

    # ---------------------------------------------------------
    # TEST 6: Medication Safety Verification
    # ---------------------------------------------------------
    meds_after = db.query(MedicineReminder).filter(
        (MedicineReminder.elder_id == test_user_id) | 
        (MedicineReminder.subject_id == test_user_id)
    ).all()
    status_map: dict[int, bool] = {int(m.id): bool(m.taken_status) for m in meds_after}
    assert status_map[1001] is True, "med 1001 must remain taken"
    assert status_map[1002] is False, "med 1002 must remain pending"
    assert status_map[1003] is False, "med 1003 must remain pending"
    print("[PASS] Medication safety state preservation test PASSED (No database mutation caused by conversational queries)")

    # ---------------------------------------------------------
    # TEST 7: Emergency System Regression Isolation
    # ---------------------------------------------------------
    q_em = "Help! I fell and I am in pain"
    intent_em, _, _ = await intent_detector.detect_intent_with_metadata(q_em)
    print(f"\n[TEST 7] Emergency Query: '{q_em}' -> Intent: {intent_em}")
    assert intent_em == "Emergency", f"Expected Emergency, got {intent_em}"
    print("[PASS] Emergency system regression test PASSED")

    db.close()
    print("\n========================================")
    print("ALL CONVERSATIONAL INTENT AUDIT TESTS PASSED SUCCESSFULLY!")
    print("========================================\n")

if __name__ == "__main__":
    asyncio.run(run_intent_audit())