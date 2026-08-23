import sys
import os
import time
import asyncio
import statistics
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

from database import SessionLocal, engine
from models.user import User
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
from intelligence.tools import healthcare_tools
from intelligence.orchestrator import orchestrator
from context.context_resolver import ContextResolver
from memory.memory_service import ocme_service

def setup_db():
    db = SessionLocal()
    test_uid = "step4_voice_user_101"
    try:
        user = db.query(User).filter(User.id == test_uid).first()
        if not user:
            user = User(id=test_uid, email="voiceuser@orma.ai", name="Grandma Sarah", role="elderly")
            db.add(user)
            db.commit()

        db.query(MedicineReminder).filter(
            (MedicineReminder.id == 20001) | (MedicineReminder.elder_id == test_uid)
        ).delete(synchronize_session=False)
        db.commit()

        m1 = MedicineReminder(
            id=20001,
            elder_id=test_uid,
            subject_id=test_uid,
            medicine_name="Atorvastatin",
            dosage="20 mg",
            reminder_time="09:00 PM",
            taken_status=False,
            adherence_pattern_flags="normal"
        )
        db.add(m1)
        db.commit()
    finally:
        db.close()

def profile_tool_direct():
    print("========================================")
    print("DIRECT TOOL & DATABASE PROFILING")
    print("========================================\n")

    # 1. DB Session Creation Time
    t_sess_0 = time.perf_counter()
    db = SessionLocal()
    t_sess_1 = time.perf_counter()
    db_session_time_ms = (t_sess_1 - t_sess_0) * 1000
    print(f"1. DB Session Creation Time: {db_session_time_ms:.3f} ms")

    # 2. Raw SQL Execution Time vs ORM Conversion Time
    from sqlalchemy import text
    t_q_0 = time.perf_counter()
    raw_res = db.execute(text("SELECT id, elder_id, medicine_name, dosage, reminder_time, taken_status FROM medicine_reminders WHERE elder_id = 'step4_voice_user_101'")).fetchall()
    t_q_1 = time.perf_counter()
    sql_exec_time_ms = (t_q_1 - t_q_0) * 1000
    print(f"2. Raw SQL Execution Time:    {sql_exec_time_ms:.3f} ms")

    # 3. SQLAlchemy ORM Model Query & Conversion
    t_orm_0 = time.perf_counter()
    orm_medicines = db.query(MedicineReminder).filter(
        (MedicineReminder.elder_id == "step4_voice_user_101") | (MedicineReminder.subject_id == "step4_voice_user_101")
    ).all()
    t_orm_1 = time.perf_counter()
    orm_time_ms = (t_orm_1 - t_orm_0) * 1000
    print(f"3. ORM Query & Object Conversion: {orm_time_ms:.3f} ms (Retrieved {len(orm_medicines)} records)")

    # 4. Direct HealthcareTools.get_medication_status Execution Time
    t_ht_0 = time.perf_counter()
    ht_status = healthcare_tools.get_medication_status(db, "step4_voice_user_101", "tonight")
    t_ht_1 = time.perf_counter()
    ht_time_ms = (t_ht_1 - t_ht_0) * 1000
    print(f"4. HealthcareTools.get_medication_status: {ht_time_ms:.3f} ms")

    # 5. Direct HealthcareTools.get_medication_schedule Execution Time
    t_hs_0 = time.perf_counter()
    ht_sched = healthcare_tools.get_medication_schedule(db, "step4_voice_user_101", "today")
    t_hs_1 = time.perf_counter()
    hs_time_ms = (t_hs_1 - t_hs_0) * 1000
    print(f"5. HealthcareTools.get_medication_schedule: {hs_time_ms:.3f} ms")

    # 6. ContextResolver Execution Time
    test_user = db.query(User).filter(User.id == "step4_voice_user_101").first()
    t_cr_0 = time.perf_counter()
    ctx = ContextResolver.resolve(test_user, "What is my next medicine?", db)
    t_cr_1 = time.perf_counter()
    cr_time_ms = (t_cr_1 - t_cr_0) * 1000
    print(f"6. ContextResolver.resolve:   {cr_time_ms:.3f} ms")

    db.close()

async def profile_orchestrator_substages():
    setup_db()
    db = SessionLocal()
    test_uid = "step4_voice_user_101"

    print("\n----------------------------------------")
    print("ORCHESTRATOR SUB-STAGE LATENCY PROFILING")
    print("----------------------------------------")

    # Measure OCME Turn Processing (Candidate Extractor)
    t_ocme_0 = time.perf_counter()
    try:
        mem_cand = await ocme_service.process_conversation_turn(db, test_uid, "What is my next medicine?", "", "MEDICATION_SCHEDULE")
    except Exception as e:
        print(f"OCME Error: {e}")
    t_ocme_1 = time.perf_counter()
    ocme_time_ms = (t_ocme_1 - t_ocme_0) * 1000
    print(f"OCME process_conversation_turn latency: {ocme_time_ms:.3f} ms")

    # Full orchestrator process_request_detailed for TOOL_ONLY query
    t_orch_0 = time.perf_counter()
    res = await orchestrator.process_request_detailed("What is my next medicine?", test_uid, db, language="en-IN")
    t_orch_1 = time.perf_counter()
    orch_time_ms = (t_orch_1 - t_orch_0) * 1000
    print(f"Orchestrator TOOL_ONLY request latency: {orch_time_ms:.3f} ms")

    ts = res["timestamps"]
    print("\nStage Breakdown for TOOL_ONLY:")
    print(f"  T0->T1 (STT init):        {(ts['T1'] - ts['T0'])*1000:.3f} ms")
    print(f"  T1->T3 (NLU Intent):       {(ts['T3'] - ts['T1'])*1000:.3f} ms")
    print(f"  T3->T4 (Brain Routing):    {(ts['T4'] - ts['T3'])*1000:.3f} ms")
    print(f"  T4->T5 (Tool & Memory DB): {(ts['T5'] - ts['T4'])*1000:.3f} ms")
    print(f"  T5->T8 (Synthesis):        {(ts['T8'] - ts['T5'])*1000:.3f} ms")
    print(f"  Total Backend Latency:     {(ts['T9'] - ts['T0'])*1000:.3f} ms")

    db.close()

if __name__ == "__main__":
    profile_tool_direct()
    asyncio.run(profile_orchestrator_substages())
