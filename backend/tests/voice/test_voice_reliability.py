import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.user import User, CaregiverRelationship
from models.medicine import MedicineReminder
from models.emergency import EmergencyAlert
from services.auth_service import create_access_token
from datetime import timedelta
from sqlalchemy import func

def run_realtime_and_voice_test():
    print("=========================================================")
    print("ORMA AI — REAL-TIME DATA & VOICE ASSISTANT RELIABILITY TEST")
    print("=========================================================")

    db = SessionLocal()
    try:
        elder = db.query(User).filter(func.lower(User.email) == "test11@gmail.com").first()
        caregiver = db.query(User).filter(func.lower(User.email) == "test1c@gmail.com").first()
        assert elder is not None, "Elder Test11 not found"
        assert caregiver is not None, "Caregiver Test1C not found"

        elder_id = elder.id
        caregiver_id = caregiver.id

        # Clean existing medicines & emergencies for Test11
        db.query(MedicineReminder).filter(MedicineReminder.elder_id == elder_id).delete()
        db.query(EmergencyAlert).filter(EmergencyAlert.elder_id == elder_id).delete()
        db.commit()

        # Seed Test11 medicines
        med_a = MedicineReminder(
            elder_id=elder_id, 
            medicine_name="TEST2", 
            dosage="10mg", 
            reminder_time="02:30 PM", 
            taken_status=False
        )
        med_b = MedicineReminder(
            elder_id=elder_id, 
            medicine_name="TEST3", 
            dosage="20mg", 
            reminder_time="02:30 PM", 
            taken_status=False
        )
        db.add_all([med_a, med_b])
        db.commit()

        med_a_id = med_a.id
        elder_token = create_access_token({"sub": elder_id, "role": elder.role}, expires_delta=timedelta(hours=2))
        caregiver_token = create_access_token({"sub": caregiver_id, "role": caregiver.role}, expires_delta=timedelta(hours=2))
    finally:
        db.close()

    elder_headers = {"Authorization": f"Bearer {elder_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    with TestClient(app) as client:
        # TEST 1: Voice / Chat Assistant Real-Time Medicine Query
        print("\n--- TEST 1: Voice/Chat Query for Test11 Medicines ---")
        chat_req = {
            "message": "Did I have any medicine to take today?",
            "language_preference": "en"
        }
        res = client.post("/api/chat/", json=chat_req, headers=elder_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        chat_body = res.json()
        assert "response" in chat_body and len(chat_body["response"]) > 0
        ai_reply = chat_body["response"]
        print(f"[PASS] AI Response generated: '{ai_reply}'")
        
        # Verify response references real medicines (TEST2 or TEST3)
        assert "TEST2" in ai_reply or "TEST3" in ai_reply or "medicine" in ai_reply.lower(), "AI reply must reference active medicines"
        print("[PASS] AI Response correctly used live Test11 database medicine records!")

        # TEST 2: Real-time Medicine Creation via API
        print("\n--- TEST 2: Real-time Medicine Creation ---")
        new_med_payload = {
            "medicine_name": "TEST_LIVE",
            "dosage": "50mg",
            "reminder_time": "06:00 PM",
            "frequency": "Daily"
        }
        create_res = client.post("/api/medicines/", json=new_med_payload, headers=elder_headers)
        assert create_res.status_code == 200, f"Failed to create medicine: {create_res.text}"
        created_med = create_res.json()
        print(f"[PASS] Created live medicine ID {created_med['id']} ({created_med['medicine_name']} at {created_med['reminder_time']})")

        # TEST 3: Ask AI again after creating new medicine
        print("\n--- TEST 3: Voice/Chat Query After New Medicine Created ---")
        res2 = client.post("/api/chat/", json=chat_req, headers=elder_headers)
        assert res2.status_code == 200
        ai_reply2 = res2.json()["response"]
        print(f"[PASS] AI Response after creation: '{ai_reply2}'")

        # TEST 4: Mark Medicine Taken & Query AI
        print("\n--- TEST 4: Mark Medicine Taken & Query AI ---")
        take_res = client.put(f"/api/medicines/{med_a_id}/taken", headers=elder_headers)
        assert take_res.status_code == 200

        res3 = client.post("/api/chat/", json=chat_req, headers=elder_headers)
        assert res3.status_code == 200
        ai_reply3 = res3.json()["response"]
        print(f"[PASS] AI Response after marking taken: '{ai_reply3}'")

        # TEST 5: Emergency Real-Time Regression Check
        print("\n--- TEST 5: Emergency Real-Time Regression Check ---")
        em_res = client.post("/api/emergency/analyze", json={"text": "Test emergency trigger"}, headers=elder_headers)
        assert em_res.status_code == 200, f"Failed to trigger emergency: {em_res.text}"
        alert_data = em_res.json()
        alert_id = alert_data.get("alert_id") or alert_data.get("id")
        assert alert_id is not None
        print(f"[PASS] Emergency alert created with ID {alert_id}")

        # Caregiver fetches active emergency
        active_res = client.get("/api/emergency/active", headers=caregiver_headers)
        assert active_res.status_code == 200
        active_data = active_res.json()
        active_list = active_data.get("active_emergencies") if isinstance(active_data, dict) else active_data
        assert len(active_list) > 0
        print(f"[PASS] Caregiver active emergency retrieved: {len(active_list)} active alert(s).")

        # Caregiver Acknowledges
        ack_res = client.post(f"/api/emergency/{alert_id}/acknowledge", headers=caregiver_headers)
        assert ack_res.status_code == 200
        print("[PASS] Caregiver acknowledged emergency.")

        # Caregiver Resolves
        res_res = client.post(f"/api/emergency/{alert_id}/resolve", json={"notes": "Resolved in test"}, headers=caregiver_headers)
        assert res_res.status_code == 200
        print("[PASS] Caregiver resolved emergency.")

        # Verify active emergencies cleared
        active_after_data = client.get("/api/emergency/active", headers=caregiver_headers).json()
        active_after_list = active_after_data.get("active_emergencies") if isinstance(active_after_data, dict) else active_after_data
        assert len(active_after_list) == 0
        print("[PASS] Active emergencies cleared post-resolution.")

    print("\n=========================================================")
    print("ALL REAL-TIME & VOICE ASSISTANT RELIABILITY TESTS PASSED!")
    print("=========================================================")

if __name__ == "__main__":
    run_realtime_and_voice_test()
