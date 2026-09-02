import os
import sys
import tempfile
import shutil
import time
import uuid
import pytest
from unittest.mock import patch, MagicMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from infrastructure.storage_service import (
    LocalStorageProvider,
    SupabaseStorageProvider,
    get_storage_provider,
    sanitize_object_key,
    build_document_object_key,
    MAX_SIGNED_URL_EXPIRY_SECONDS
)

# -----------------------------------------------------------------------------
# 1. Object Key & Path Traversal Security Tests
# -----------------------------------------------------------------------------

def test_sanitize_object_key_valid():
    key = "user-123/doc-456/lab_results.pdf"
    assert sanitize_object_key(key) == "user-123/doc-456/lab_results.pdf"

def test_sanitize_object_key_normalizes_slashes():
    key = "user-123//doc-456\\\\lab_results.pdf"
    assert sanitize_object_key(key) == "user-123/doc-456/lab_results.pdf"

def test_sanitize_object_key_rejects_parent_traversal():
    with pytest.raises(ValueError, match="Path traversal detected"):
        sanitize_object_key("../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal detected"):
        sanitize_object_key("user-123/../../secret/doc.pdf")

    with pytest.raises(ValueError, match="Path traversal detected"):
        sanitize_object_key("user-123/doc-456/../file.txt")

def test_sanitize_object_key_rejects_control_characters():
    with pytest.raises(ValueError, match="Invalid control characters"):
        sanitize_object_key("user-123/doc\0/file.pdf")

def test_build_document_object_key():
    key = build_document_object_key("user_abc", "doc_xyz", "blood_work.pdf")
    assert key == "user_abc/doc_xyz/blood_work.pdf"

def test_build_document_object_key_requires_all_fields():
    with pytest.raises(ValueError):
        build_document_object_key("", "doc_123", "test.pdf")
    with pytest.raises(ValueError):
        build_document_object_key("user_123", "", "test.pdf")
    with pytest.raises(ValueError):
        build_document_object_key("user_123", "doc_123", "")

# -----------------------------------------------------------------------------
# 2. LocalStorageProvider Lifecycle Tests
# -----------------------------------------------------------------------------

@pytest.fixture
def temp_local_storage():
    tmp_dir = tempfile.mkdtemp(prefix="orma_test_storage_")
    provider = LocalStorageProvider(base_dir=tmp_dir, default_bucket="test-bucket")
    yield provider, tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_local_storage_upload_and_read(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    obj_key = "user_1/doc_1/prescription.pdf"
    data = b"%PDF-1.4 synthetic pdf content for testing"

    stored_key = provider.upload_file("test-bucket", obj_key, data, "application/pdf")
    assert stored_key == obj_key

    read_bytes = provider.get_file_bytes("test-bucket", obj_key)
    assert read_bytes == data

def test_local_storage_delete_file(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    obj_key = "user_1/doc_2/scan.png"
    data = b"image bytes"

    provider.upload_file("test-bucket", obj_key, data, "image/png")
    assert provider.delete_file("test-bucket", obj_key) is True

    # Subsequent read fails
    with pytest.raises(FileNotFoundError):
        provider.get_file_bytes("test-bucket", obj_key)

    # Deleting non-existent file returns False cleanly
    assert provider.delete_file("test-bucket", "non_existent.pdf") is False

def test_local_storage_delete_folder(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    user_prefix = "user_delete_test"
    provider.upload_file("test-bucket", f"{user_prefix}/doc_1/a.txt", b"a")
    provider.upload_file("test-bucket", f"{user_prefix}/doc_2/b.txt", b"b")

    assert provider.delete_folder("test-bucket", user_prefix) is True

    with pytest.raises(FileNotFoundError):
        provider.get_file_bytes("test-bucket", f"{user_prefix}/doc_1/a.txt")

def test_local_storage_traversal_boundary_enforcement(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    with pytest.raises(ValueError, match="Path traversal detected"):
        provider.upload_file("test-bucket", "../outside.txt", b"escape")

def test_local_storage_signed_url_generation_and_verification(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    obj_key = "user_1/doc_1/sample.pdf"

    # Generate URL with 120s expiry
    signed_url = provider.create_signed_download_url("test-bucket", obj_key, expires_in=120)
    assert "/api/documents/local-download?" in signed_url
    assert "bucket=test-bucket" in signed_url
    assert "expires=" in signed_url
    assert "sig=" in signed_url

    # Parse query params
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(signed_url)
    qs = parse_qs(parsed.query)
    expires_ts = int(qs["expires"][0])
    sig = qs["sig"][0]

    # Legitimate signature passes
    assert provider.verify_local_signed_url("test-bucket", obj_key, expires_ts, sig) is True

    # Tampered key fails
    assert provider.verify_local_signed_url("test-bucket", "tampered_key.pdf", expires_ts, sig) is False

    # Tampered signature fails
    assert provider.verify_local_signed_url("test-bucket", obj_key, expires_ts, "invalid_signature") is False

    # Expired timestamp fails
    past_ts = int(time.time()) - 10
    assert provider.verify_local_signed_url("test-bucket", obj_key, past_ts, sig) is False

def test_local_storage_signed_url_enforces_max_300s(temp_local_storage):
    provider, tmp_dir = temp_local_storage
    obj_key = "user_1/doc_1/sample.pdf"

    # Request 99999 seconds - must be clamped to <= 300
    signed_url = provider.create_signed_download_url("test-bucket", obj_key, expires_in=99999)
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(signed_url).query)
    expires_ts = int(qs["expires"][0])
    assert expires_ts <= int(time.time()) + MAX_SIGNED_URL_EXPIRY_SECONDS + 2

# -----------------------------------------------------------------------------
# 3. SupabaseStorageProvider Configuration & Security Tests
# -----------------------------------------------------------------------------

def test_supabase_storage_missing_credentials_raises():
    with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"):
        SupabaseStorageProvider(supabase_url="", service_role_key="")

    with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"):
        SupabaseStorageProvider(supabase_url="https://test.supabase.co", service_role_key="")

def test_supabase_storage_signed_url_clamps_expiry():
    provider = SupabaseStorageProvider(
        supabase_url="https://test.supabase.co",
        service_role_key="mock_secret_key_never_logged",
        default_bucket="medical-documents"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    # Supabase returns relative path beginning with /object/sign/
    mock_resp.json.return_value = {
        "signedURL": "/object/sign/medical-documents/user/doc/f.pdf?token=abc"
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MockClient.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_resp

        # Request 3600 seconds - must be clamped to <= 300
        url = provider.create_signed_download_url("medical-documents", "user/doc/f.pdf", expires_in=3600)
        # Verifies /object/sign/... correctly receives /storage/v1 prefix
        assert url == "https://test.supabase.co/storage/v1/object/sign/medical-documents/user/doc/f.pdf?token=abc"

        # Verify payload sent to Supabase Storage API has expiresIn: 300
        mock_client_instance.post.assert_called_once()
        _, kwargs = mock_client_instance.post.call_args
        assert kwargs["json"]["expiresIn"] == 300

def test_supabase_storage_signed_url_absolute_url_preserved():
    provider = SupabaseStorageProvider(
        supabase_url="https://test.supabase.co",
        service_role_key="mock_secret_key_never_logged",
        default_bucket="medical-documents"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    # Supabase returns an already-absolute URL (e.g. from CDN or custom domain)
    mock_resp.json.return_value = {
        "signedURL": "https://cdn.supabase.co/storage/v1/object/sign/medical-documents/user/doc/f.pdf?token=abc"
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MockClient.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_resp

        url = provider.create_signed_download_url("medical-documents", "user/doc/f.pdf", expires_in=120)
        # Verifies absolute URL is preserved unchanged
        assert url == "https://cdn.supabase.co/storage/v1/object/sign/medical-documents/user/doc/f.pdf?token=abc"

def test_supabase_storage_signed_url_existing_storage_v1_prefix_not_duplicated():
    provider = SupabaseStorageProvider(
        supabase_url="https://test.supabase.co",
        service_role_key="mock_secret_key_never_logged",
        default_bucket="medical-documents"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    # Relative path already containing /storage/v1
    mock_resp.json.return_value = {
        "signedURL": "/storage/v1/object/sign/medical-documents/user/doc/f.pdf?token=abc"
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MockClient.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_resp

        url = provider.create_signed_download_url("medical-documents", "user/doc/f.pdf", expires_in=120)
        # Verifies /storage/v1 is not duplicated
        assert url == "https://test.supabase.co/storage/v1/object/sign/medical-documents/user/doc/f.pdf?token=abc"


def test_supabase_storage_upload_headers():
    provider = SupabaseStorageProvider(
        supabase_url="https://test.supabase.co",
        service_role_key="mock_secret_key_never_logged",
        default_bucket="medical-documents"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MockClient.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_resp

        key = provider.upload_file("medical-documents", "u1/d1/doc.pdf", b"bytes", "application/pdf")
        assert key == "u1/d1/doc.pdf"

        mock_client_instance.post.assert_called_once()
        _, kwargs = mock_client_instance.post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer mock_secret_key_never_logged"
        assert kwargs["headers"]["apikey"] == "mock_secret_key_never_logged"
        assert kwargs["headers"]["x-upsert"] == "true"

# -----------------------------------------------------------------------------
# 4. Storage Provider Selection & Fail-Closed Logic Tests
# -----------------------------------------------------------------------------

def test_get_storage_provider_local_default():
    with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "", "ENVIRONMENT": "development"}, clear=False):
        provider = get_storage_provider()
        assert provider.provider_name == "local"

def test_get_storage_provider_production_fails_closed():
    # In production, missing Supabase credentials MUST raise RuntimeError rather than falling back to local disk
    with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "", "ENVIRONMENT": "production"}, clear=False):
        with pytest.raises(RuntimeError, match="In production environment, SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured"):
            get_storage_provider()

def test_get_storage_provider_partial_config_raises():
    with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "", "ENVIRONMENT": "development"}, clear=False):
        with pytest.raises(RuntimeError, match="SUPABASE_URL is configured but SUPABASE_SERVICE_ROLE_KEY is missing"):
            get_storage_provider()

def test_get_storage_provider_supabase_when_configured():
    with patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "mock_key",
        "ENVIRONMENT": "production"
    }, clear=False):
        provider = get_storage_provider()
        assert provider.provider_name == "supabase"

# -----------------------------------------------------------------------------
# 5. Route-Level Document Download & Authorization Tests
# -----------------------------------------------------------------------------

from main import app
from fastapi.testclient import TestClient
from database import SessionLocal
from models.user import User, CaregiverRelationship
from rag.rag_models import RAGDocument, RAGDocumentChunk
from services.auth_service import create_access_token
from infrastructure.storage_service import storage_service

client = TestClient(app)

@pytest.fixture
def auth_storage_users():
    db = SessionLocal()
    tag = uuid.uuid4().hex[:6]
    uid_a = f"u_st_a_{tag}"
    uid_b = f"u_st_b_{tag}"
    cg_appr = f"cg_st_appr_{tag}"
    cg_rev = f"cg_st_rev_{tag}"

    user_a = User(id=uid_a, email=f"{uid_a}@test.com", role="elderly", name="Elder A", email_verified=True)
    user_b = User(id=uid_b, email=f"{uid_b}@test.com", role="elderly", name="Elder B", email_verified=True)
    caregiver_appr = User(id=cg_appr, email=f"{cg_appr}@test.com", role="caregiver", name="Caregiver Appr", email_verified=True)
    caregiver_rev = User(id=cg_rev, email=f"{cg_rev}@test.com", role="caregiver", name="Caregiver Rev", email_verified=True)

    db.add_all([user_a, user_b, caregiver_appr, caregiver_rev])
    db.commit()

    rel_appr = CaregiverRelationship(elder_id=uid_a, caregiver_id=cg_appr, status="approved")
    rel_rev = CaregiverRelationship(elder_id=uid_a, caregiver_id=cg_rev, status="revoked")

    db.add_all([rel_appr, rel_rev])
    db.commit()

    tokens = {
        "user_a": create_access_token(data={"sub": uid_a, "role": "elderly", "ver": 1}),
        "user_b": create_access_token(data={"sub": uid_b, "role": "elderly", "ver": 1}),
        "cg_appr": create_access_token(data={"sub": cg_appr, "role": "caregiver", "ver": 1}),
        "cg_rev": create_access_token(data={"sub": cg_rev, "role": "caregiver", "ver": 1}),
        "uids": {"a": uid_a, "b": uid_b, "cg_appr": cg_appr, "cg_rev": cg_rev}
    }

    yield tokens

    # Teardown
    db.query(RAGDocumentChunk).filter(RAGDocumentChunk.user_id.in_([uid_a, uid_b])).delete(synchronize_session=False)
    db.query(RAGDocument).filter(RAGDocument.user_id.in_([uid_a, uid_b])).delete(synchronize_session=False)
    db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id.in_([uid_a, uid_b])).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_([uid_a, uid_b, cg_appr, cg_rev])).delete(synchronize_session=False)
    db.commit()
    db.close()

def test_document_signed_url_and_download_lifecycle(auth_storage_users):
    tokens = auth_storage_users
    uid_a = tokens["uids"]["a"]
    uid_b = tokens["uids"]["b"]
    cg_appr = tokens["uids"]["cg_appr"]
    cg_rev = tokens["uids"]["cg_rev"]

    db = SessionLocal()
    doc_id = f"doc_test_{uuid.uuid4().hex[:6]}"
    raw_content = b"%PDF-1.4 Clinical Discharge Summary for Elder A"
    
    # Ingest document via storage abstraction
    bucket = getattr(storage_service, "default_bucket", "medical-documents")
    obj_key = build_document_object_key(uid_a, doc_id, "summary.pdf")
    stored_path = storage_service.upload_file(bucket, obj_key, raw_content, "application/pdf")

    doc = RAGDocument(
        id=doc_id,
        user_id=uid_a,
        title="Summary.pdf",
        file_path=stored_path,
        file_size=len(raw_content),
        processing_status="READY"
    )
    db.add(doc)
    db.commit()
    db.close()

    # 1. Elder A (Owner) can request signed download URL
    res_url = client.get(f"/api/documents/{doc_id}/url", headers={"Authorization": f"Bearer {tokens['user_a']}"})
    assert res_url.status_code == 200
    data_url = res_url.json()
    assert data_url["document_id"] == doc_id
    assert data_url["expires_in"] <= 300
    assert "download_url" in data_url

    # 2. Elder A can download directly (200 stream on Local, 307 redirect on Supabase)
    res_dl = client.get(
        f"/api/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {tokens['user_a']}"},
        follow_redirects=False
    )
    assert res_dl.status_code in (200, 307)
    if res_dl.status_code == 200:
        assert res_dl.content == raw_content
    elif res_dl.status_code == 307:
        assert "/storage/v1/object/sign/" in res_dl.headers["location"]

    # 3. Approved Caregiver can access on behalf of Elder A
    res_cg_url = client.get(
        f"/api/documents/{doc_id}/url",
        headers={"Authorization": f"Bearer {tokens['cg_appr']}", "X-Subject-Id": uid_a}
    )
    assert res_cg_url.status_code == 200

    # 4. User B (unrelated tenant) CANNOT access Elder A's document (Cross-tenant 404)
    res_b_url = client.get(f"/api/documents/{doc_id}/url", headers={"Authorization": f"Bearer {tokens['user_b']}"})
    assert res_b_url.status_code == 404

    res_b_dl = client.get(f"/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tokens['user_b']}"})
    assert res_b_dl.status_code == 404

    # 5. Revoked Caregiver CANNOT access Elder A's document (403)
    res_rev = client.get(
        f"/api/documents/{doc_id}/url",
        headers={"Authorization": f"Bearer {tokens['cg_rev']}", "X-Subject-Id": uid_a}
    )
    assert res_rev.status_code == 403

    # 6. Unauthenticated request rejected (401)
    res_unauth = client.get(f"/api/documents/{doc_id}/url")
    assert res_unauth.status_code == 401

    # 7. Authorized deletion removes document and storage object
    res_del = client.delete(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {tokens['user_a']}"})
    assert res_del.status_code == 200

    # Verify deleted from storage
    with pytest.raises(FileNotFoundError):
        storage_service.get_file_bytes(bucket, stored_path)

