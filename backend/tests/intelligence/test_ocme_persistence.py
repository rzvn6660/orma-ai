import sys
import os
import asyncio
import pytest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, Base, engine
from main import app
from models.user import User
from models.medicine import MedicineReminder
from memory.memory_models import OCMEMemory, OCMEMemoryCreate
from memory.memory_store import memory_store
from memory.memory_service import ocme_service
from memory.memory_candidate_extractor import memory_candidate_extractor
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager
from services.auth_service import create_access_token

client = TestClient(app)

TEST_USER_A_ID = "ocme_persist_user_a"
TEST_USER_B_ID = "ocme_persist_user_b"

@pytest.fixture(autouse=True)
def setup_clean_db():
    db = SessionLocal()
    try:
        # Clean existing test memories and users
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.query(User).filter(User.id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.commit()

        # Create test users with valid token_version
        user_a = User(
            id=TEST_USER_A_ID,
            email="usera_ocme@orma.test",
            name="Alice Test",
            role="elderly",
            token_version=1
        )
        user_b = User(
            id=TEST_USER_B_ID,
            email="userb_ocme@orma.test",
            name="Bob Test",
            role="elderly",
            token_version=1
        )
        db.add_all([user_a, user_b])
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.query(User).filter(User.id.in_([TEST_USER_A_ID, TEST_USER_B_ID])).delete()
        db.commit()
    finally:
        db.close()

def get_auth_headers(user_id: str, role: str = "elderly") -> dict:
    token = create_access_token(data={"sub": user_id, "role": role, "ver": 1})
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# TEST 1: Explicit Memory Instruction -> Candidate Generated
# =========================================================================
@pytest.mark.asyncio
async def test_explicit_memory_candidate_generation():
    test_phrases = [
        "Remember that my preferred reminder language is English.",
        "Please remember that my preferred reminder language is English."
    ]
    for phrase in test_phrases:
        candidates = await memory_candidate_extractor.extract_candidates(phrase, "I have noted that.", "Memory")
        assert len(candidates) >= 1, f"Failed to extract candidate for phrase: {phrase}"
        cand = candidates[0]
        title_lower = cand["title"].lower()
        assert "preferred reminder language" in title_lower or "language" in title_lower or "preference" in title_lower
        assert "English" in cand["value"]
        assert cand["category"] == "Preference"
        assert cand["confidence"] >= 0.9

# =========================================================================
# TEST 2: Candidate -> OCMEMemory Saved in Database
# =========================================================================
@pytest.mark.asyncio
async def test_candidate_saves_to_ocmememory():
    db = SessionLocal()
    try:
        candidates = await ocme_service.process_conversation_turn(
            db,
            user_id=TEST_USER_A_ID,
            user_text="Remember that my preferred reminder language is English.",
            ai_response="I will remember that your preferred reminder language is English.",
            context_intent="Memory"
        )
        assert len(candidates) >= 1
        
        saved_records = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(saved_records) == 1
        record = saved_records[0]
        assert record.category == "Preference"
        assert "English" in record.value
    finally:
        db.close()

# =========================================================================
# TEST 3: Memory Retrieval for Same Authenticated User via Canonical Route
# =========================================================================
def test_canonical_route_authenticated_retrieval():
    db = SessionLocal()
    try:
        mem_data = OCMEMemoryCreate(
            category="Preference",
            title="Preferred Reminder Language",
            value="English",
            importance=80,
            confidence=0.95,
            source="conversation"
        )
        saved = memory_store.save_memory(db, TEST_USER_A_ID, mem_data)
        saved_id = saved.id
    finally:
        db.close()

    headers_a = get_auth_headers(TEST_USER_A_ID)

    # 1. Canonical route with trailing slash
    resp = client.get("/api/ocme/", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == saved_id
    assert data[0]["value"] == "English"

    # 2. Canonical route without trailing slash
    resp_no_slash = client.get("/api/ocme", headers=headers_a)
    assert resp_no_slash.status_code == 200
    assert len(resp_no_slash.json()) == 1

    # 3. Single memory endpoint
    resp_single = client.get(f"/api/ocme/{saved_id}", headers=headers_a)
    assert resp_single.status_code == 200
    assert resp_single.json()["value"] == "English"

# =========================================================================
# TEST 4: Compatibility Route Alias (/api/ocme/ocme/)
# =========================================================================
def test_route_compatibility_alias():
    db = SessionLocal()
    try:
        mem_data = OCMEMemoryCreate(
            category="Preference",
            title="Preferred Reminder Language",
            value="English",
            importance=80,
            confidence=0.95,
            source="conversation"
        )
        saved = memory_store.save_memory(db, TEST_USER_A_ID, mem_data)
        saved_id = saved.id
    finally:
        db.close()

    headers_a = get_auth_headers(TEST_USER_A_ID)
    resp = client.get("/api/ocme/ocme/", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == saved_id

# =========================================================================
# TEST 5: Cross-User Isolation (User B cannot access User A's memory)
# =========================================================================
def test_cross_user_isolation():
    db = SessionLocal()
    try:
        mem_data = OCMEMemoryCreate(
            category="Preference",
            title="Preferred Reminder Language",
            value="English",
            importance=80,
            confidence=0.95,
            source="conversation"
        )
        saved_a = memory_store.save_memory(db, TEST_USER_A_ID, mem_data)
        saved_a_id = saved_a.id
    finally:
        db.close()

    headers_b = get_auth_headers(TEST_USER_B_ID)

    # User B list must NOT include User A's memory
    resp_b_list = client.get("/api/ocme/", headers=headers_b)
    assert resp_b_list.status_code == 200
    assert len(resp_b_list.json()) == 0

    # User B direct lookup of User A's memory ID must return 404
    resp_b_item = client.get(f"/api/ocme/{saved_a_id}", headers=headers_b)
    assert resp_b_item.status_code == 404

# =========================================================================
# TEST 6: Unauthenticated Memory Access -> 401
# =========================================================================
def test_unauthenticated_memory_access_401():
    resp_list = client.get("/api/ocme/")
    assert resp_list.status_code == 401

    resp_single = client.get("/api/ocme/1")
    assert resp_single.status_code == 401

# =========================================================================
# TEST 7: Truncated, Fenced, and Malformed JSON is Handled Safely
# =========================================================================
def test_truncated_fenced_json_handling():
    extractor = memory_candidate_extractor

    # 1. Truncated output
    truncated = '```json\n[{"title": "Preferred Reminder Language", "value": "English"'
    parsed_trunc = extractor._clean_and_parse_json(truncated)
    assert len(parsed_trunc) == 1
    assert parsed_trunc[0]["title"] == "Preferred Reminder Language"
    assert parsed_trunc[0]["value"] == "English"

    # 2. Fenced output with trailing comma
    fenced = '```json\n[{"title": "Language", "value": "English",},]\n```'
    parsed_fenced = extractor._clean_and_parse_json(fenced)
    assert len(parsed_fenced) == 1
    assert parsed_fenced[0]["title"] == "Language"
    assert parsed_fenced[0]["value"] == "English"

    # 3. Single object output
    obj_str = '{"title": "Allergy", "value": "Penicillin"}'
    parsed_obj = extractor._clean_and_parse_json(obj_str)
    assert len(parsed_obj) == 1
    assert parsed_obj[0]["title"] == "Allergy"
    assert parsed_obj[0]["value"] == "Penicillin"

# =========================================================================
# TEST 8: Provider Timeout Handled Safely
# =========================================================================
@pytest.mark.asyncio
async def test_provider_timeout_handled_safely():
    with patch("llm.ai_manager.ai_manager.generate", side_effect=httpx.ReadTimeout("Model read timed out")):
        candidates = await memory_candidate_extractor.extract_candidates(
            user_text="Remember that my preferred reminder language is English.",
            ai_response="I will remember that.",
            context_intent="Memory"
        )
        assert len(candidates) == 1
        assert "English" in candidates[0]["value"]
        assert candidates[0]["category"] == "Preference"

# =========================================================================
# TEST 9: Ambiguous / Non-Memory Statements Do NOT Create Memories
# =========================================================================
@pytest.mark.asyncio
async def test_ambiguous_statements_no_memory():
    db = SessionLocal()
    try:
        ambiguous_statements = [
            "What medicine is that?",
            "What time?",
            "What about tomorrow?",
            "I had some toast this morning.",
            "Do you remember my language?"
        ]
        for stmt in ambiguous_statements:
            candidates = await ocme_service.process_conversation_turn(
                db,
                user_id=TEST_USER_A_ID,
                user_text=stmt,
                ai_response="Sure, I can help you with that.",
                context_intent="GENERAL_CONVERSATION"
            )
            assert len(candidates) == 0, f"Ambiguous statement created unwanted candidate: {stmt}"

        # Ensure database has zero memories
        mems = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(mems) == 0
    finally:
        db.close()

# =========================================================================
# TEST 10: End-to-End Chat Save -> Fresh Session Retrieval
# =========================================================================
@pytest.mark.asyncio
async def test_end_to_end_chat_persistence_and_retrieval():
    db = SessionLocal()
    try:
        # Turn 1: Save explicit memory via orchestrator
        t1_reply = await orchestrator.process_request(
            text="Remember that my preferred reminder language is English.",
            user_id=TEST_USER_A_ID,
            db=db,
            language="en"
        )
        assert t1_reply is not None

        # Verify memory saved to DB
        saved_mems = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(saved_mems) == 1
        assert "English" in saved_mems[0].value

        # Fresh Session Simulation: Clear conversation session history
        conversation_manager.clear_session(TEST_USER_A_ID)
        assert len(conversation_manager.get_history(TEST_USER_A_ID)) == 0

        # Turn 2: Retrieve in fresh conversation
        t2_reply = await orchestrator.process_request(
            text="What is my preferred reminder language?",
            user_id=TEST_USER_A_ID,
            db=db,
            language="en"
        )
        # Response must reference English
        assert "english" in t2_reply.lower() or "noted" in t2_reply.lower(), f"Unexpected retrieval reply: {t2_reply}"
    finally:
        db.close()

# =========================================================================
# TEST 11: Explicit Memory In Offline Fallback Mode (No LLM Providers)
# =========================================================================
@pytest.mark.asyncio
async def test_explicit_memory_in_offline_fallback_mode():
    """
    Proves that even when cloud/local LLM providers are unavailable (e.g. CI without API keys),
    explicit user memory instructions are reliably parsed and persisted via the deterministic path,
    retrieval answers are grounded in the saved memory, and ordinary casual conversation does NOT persist.
    """
    from llm.ai_manager import ai_manager
    original_providers = ai_manager.providers if hasattr(ai_manager, 'providers') else None

    db = SessionLocal()
    try:
        # Simulate completely offline environment
        ai_manager.providers = {}

        # 1. Explicit memory save
        t1_reply = await orchestrator.process_request(
            text="Remember that my preferred reminder language is English.",
            user_id=TEST_USER_A_ID,
            db=db,
            language="en"
        )
        assert t1_reply is not None

        # Verify exactly one memory record was persisted
        saved_mems = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(saved_mems) == 1
        assert "English" in saved_mems[0].value
        assert "Language" in saved_mems[0].title or "Preference" in saved_mems[0].category

        # 2. Fresh session simulation
        conversation_manager.clear_session(TEST_USER_A_ID)
        assert len(conversation_manager.get_history(TEST_USER_A_ID)) == 0

        # 3. Retrieval in offline fallback mode
        t2_reply = await orchestrator.process_request(
            text="What language do I prefer for reminders?",
            user_id=TEST_USER_A_ID,
            db=db,
            language="en"
        )
        assert "english" in t2_reply.lower(), f"Expected 'English' in retrieval reply, got: '{t2_reply}'"

        # Verify retrieval did not create a duplicate memory
        mems_after_query = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(mems_after_query) == 1

        # 4. Ordinary casual conversation must NOT persist memory
        t3_reply = await orchestrator.process_request(
            text="I had some toast this morning.",
            user_id=TEST_USER_A_ID,
            db=db,
            language="en"
        )
        assert t3_reply is not None
        mems_after_casual = db.query(OCMEMemory).filter(OCMEMemory.user_id == TEST_USER_A_ID).all()
        assert len(mems_after_casual) == 1
    finally:
        if original_providers is not None:
            ai_manager.providers = original_providers
        db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

