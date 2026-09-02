"""
ORMA AI — Dual-Mode Secure Storage Abstraction
Provides secure object storage for persistent medical documents:
- LocalStorageProvider: Local filesystem storage for offline development & tests.
- SupabaseStorageProvider: Private Supabase Object Storage for cloud production.

Security Controls:
- Strict user-isolated object keys: {user_id}/{document_id}/{sanitized_filename}
- Private bucket assumption (medical-documents is never public)
- Short-lived signed download URLs (expiry <= 300 seconds)
- Path traversal defense and strict boundary enforcement
- Production fail-closed validation (no silent fallback to ephemeral disk)
- Zero credential logging
"""

import os
import re
import shutil
import logging
import hmac
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default base directory for local storage
DEFAULT_LOCAL_STORAGE_DIR = (
    os.getenv("RAG_UPLOAD_DIR")
    or os.getenv("UPLOAD_DIR")
    or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads",
        "documents"
    )
)

MAX_SIGNED_URL_EXPIRY_SECONDS = 300  # Strict 5-minute limit for medical data


def sanitize_object_key(key: str) -> str:
    """
    Validates and normalizes object key to eliminate directory traversal patterns.
    Ensures safe segment structure: user_id/document_id/filename.
    """
    cleaned = key.replace("\\", "/").strip()
    # Collapse duplicate slashes
    cleaned = re.sub(r"/+", "/", cleaned)
    segments = [s for s in cleaned.split("/") if s and s != "."]
    
    # Check for directory traversal
    if any(s == ".." for s in segments):
        raise ValueError(f"Path traversal detected in storage object key: '{key}'")
    
    # Disallow empty segments or control characters
    for s in segments:
        if re.search(r"[\0\r\n]", s):
            raise ValueError("Invalid control characters in storage object key")
            
    return "/".join(segments)


def build_document_object_key(user_id: str, document_id: str, safe_filename: str) -> str:
    """
    Constructs the canonical, strictly isolated object key for RAG documents:
    {user_id}/{document_id}/{sanitized_filename}
    """
    uid = str(user_id).strip()
    did = str(document_id).strip()
    fname = str(safe_filename).strip()

    if not uid or not did or not fname:
        raise ValueError("user_id, document_id, and safe_filename are required to build object key")

    raw_key = f"{uid}/{did}/{fname}"
    return sanitize_object_key(raw_key)


class BaseStorageProvider(ABC):
    """Abstract base class defining the authoritative storage provider interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider identifier (e.g. 'local' or 'supabase')."""
        pass

    @abstractmethod
    def upload_file(
        self,
        bucket: str,
        object_path: str,
        file_bytes: bytes,
        content_type: Optional[str] = None
    ) -> str:
        """Uploads file bytes and returns the stored object key."""
        pass

    @abstractmethod
    def delete_file(self, bucket: str, object_path: str) -> bool:
        """Deletes a specific object key from the storage bucket."""
        pass

    @abstractmethod
    def delete_folder(self, bucket: str, folder_prefix: str) -> bool:
        """Deletes all objects matching the given folder prefix."""
        pass

    @abstractmethod
    def create_signed_download_url(
        self,
        bucket: str,
        object_path: str,
        expires_in: int = MAX_SIGNED_URL_EXPIRY_SECONDS
    ) -> str:
        """Generates a temporary, time-limited signed URL for authenticated download."""
        pass

    @abstractmethod
    def get_file_bytes(self, bucket: str, object_path: str) -> bytes:
        """Retrieves raw object bytes (used for internal streaming or processing)."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local filesystem storage provider for offline development, local runs, and automated testing.
    Keeps files organized within a dedicated storage root with strict traversal defense.
    """

    def __init__(self, base_dir: Optional[str] = None, default_bucket: str = "medical-documents"):
        self.base_dir = os.path.abspath(base_dir or DEFAULT_LOCAL_STORAGE_DIR)
        self.default_bucket = default_bucket
        self._signing_secret = os.getenv("JWT_SECRET_KEY", "local_storage_development_signing_secret").encode()
        os.makedirs(self.base_dir, exist_ok=True)

    @property
    def provider_name(self) -> str:
        return "local"

    def _resolve_safe_path(self, bucket: str, object_path: str) -> str:
        clean_key = sanitize_object_key(object_path)
        # Store under base_dir/bucket/object_path or base_dir/object_path
        target_path = os.path.abspath(os.path.join(self.base_dir, clean_key))
        if not target_path.startswith(self.base_dir):
            raise ValueError(f"Directory traversal boundary violation: '{object_path}'")
        return target_path

    def upload_file(
        self,
        bucket: str,
        object_path: str,
        file_bytes: bytes,
        content_type: Optional[str] = None
    ) -> str:
        target_path = self._resolve_safe_path(bucket, object_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return sanitize_object_key(object_path)

    def delete_file(self, bucket: str, object_path: str) -> bool:
        try:
            target_path = self._resolve_safe_path(bucket, object_path)
            if os.path.exists(target_path) and os.path.isfile(target_path):
                os.remove(target_path)
                return True
            return False
        except Exception as e:
            logger.warning(f"[LocalStorage] Failed to delete file {object_path}: {e}")
            return False

    def delete_folder(self, bucket: str, folder_prefix: str) -> bool:
        try:
            clean_prefix = sanitize_object_key(folder_prefix)
            target_dir = os.path.abspath(os.path.join(self.base_dir, clean_prefix))
            if not target_dir.startswith(self.base_dir):
                raise ValueError("Traversal boundary violation in folder delete")
            if os.path.exists(target_dir) and os.path.isdir(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
                return True
            return False
        except Exception as e:
            logger.warning(f"[LocalStorage] Failed to delete folder {folder_prefix}: {e}")
            return False

    def create_signed_download_url(
        self,
        bucket: str,
        object_path: str,
        expires_in: int = MAX_SIGNED_URL_EXPIRY_SECONDS
    ) -> str:
        # Enforce maximum expiry
        expiry = min(int(expires_in), MAX_SIGNED_URL_EXPIRY_SECONDS)
        expiry_ts = int(time.time()) + expiry
        clean_key = sanitize_object_key(object_path)

        # Generate HMAC signature to verify authenticity and timestamp
        sig_payload = f"{bucket}:{clean_key}:{expiry_ts}".encode()
        signature = hmac.new(self._signing_secret, sig_payload, hashlib.sha256).hexdigest()

        # Local download endpoint
        return f"/api/documents/local-download?bucket={bucket}&key={clean_key}&expires={expiry_ts}&sig={signature}"

    def verify_local_signed_url(self, bucket: str, object_path: str, expires_ts: int, signature: str) -> bool:
        """Validates the HMAC signature and expiration timestamp of a local signed URL."""
        if time.time() > expires_ts:
            return False
        sig_payload = f"{bucket}:{sanitize_object_key(object_path)}:{expires_ts}".encode()
        expected = hmac.new(self._signing_secret, sig_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_file_bytes(self, bucket: str, object_path: str) -> bytes:
        target_path = self._resolve_safe_path(bucket, object_path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Storage object not found: {object_path}")
        with open(target_path, "rb") as f:
            return f.read()


class SupabaseStorageProvider(BaseStorageProvider):
    """
    Cloud production storage provider utilizing Supabase Object Storage (S3-compatible REST API).
    Always treats target buckets as private. Never generates public URLs.
    """

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
        default_bucket: str = "medical-documents"
    ):
        if not supabase_url or not service_role_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for SupabaseStorageProvider")

        self.supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self.default_bucket = default_bucket

    @property
    def provider_name(self) -> str:
        return "supabase"

    def _get_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._service_role_key}",
            "apikey": self._service_role_key
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def upload_file(
        self,
        bucket: str,
        object_path: str,
        file_bytes: bytes,
        content_type: Optional[str] = None
    ) -> str:
        import httpx

        clean_key = sanitize_object_key(object_path)
        target_bucket = bucket or self.default_bucket
        url = f"{self.supabase_url}/storage/v1/object/{target_bucket}/{clean_key}"
        headers = self._get_headers(content_type or "application/octet-stream")
        headers["x-upsert"] = "true"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, content=file_bytes, headers=headers)
            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"Supabase Storage upload failed with status {response.status_code}: {response.text}"
                )

        return clean_key

    def delete_file(self, bucket: str, object_path: str) -> bool:
        import httpx

        clean_key = sanitize_object_key(object_path)
        target_bucket = bucket or self.default_bucket
        url = f"{self.supabase_url}/storage/v1/object/{target_bucket}"
        headers = self._get_headers("application/json")
        payload = {"prefixes": [clean_key]}

        with httpx.Client(timeout=15.0) as client:
            response = client.request("DELETE", url, json=payload, headers=headers)
            if response.status_code in (200, 204):
                return True
            logger.warning(f"Supabase Storage delete failed ({response.status_code}): {response.text}")
            return False

    def delete_folder(self, bucket: str, folder_prefix: str) -> bool:
        import httpx

        clean_prefix = sanitize_object_key(folder_prefix).rstrip("/")
        target_bucket = bucket or self.default_bucket
        url = f"{self.supabase_url}/storage/v1/object/{target_bucket}"
        headers = self._get_headers("application/json")
        payload = {"prefixes": [clean_prefix]}

        with httpx.Client(timeout=15.0) as client:
            response = client.request("DELETE", url, json=payload, headers=headers)
            if response.status_code in (200, 204):
                return True
            logger.warning(f"Supabase Storage delete_folder failed ({response.status_code}): {response.text}")
            return False

    def create_signed_download_url(
        self,
        bucket: str,
        object_path: str,
        expires_in: int = MAX_SIGNED_URL_EXPIRY_SECONDS
    ) -> str:
        import httpx

        expiry = min(int(expires_in), MAX_SIGNED_URL_EXPIRY_SECONDS)
        clean_key = sanitize_object_key(object_path)
        target_bucket = bucket or self.default_bucket
        url = f"{self.supabase_url}/storage/v1/object/sign/{target_bucket}/{clean_key}"
        headers = self._get_headers("application/json")
        payload = {"expiresIn": expiry}

        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to generate Supabase signed URL (status {response.status_code}): {response.text}"
                )
            data = response.json()

        signed_path = data.get("signedURL") or data.get("signedUrl")
        if not signed_path:
            raise RuntimeError(f"Unexpected Supabase sign response payload: {data}")

        if signed_path.startswith("http://") or signed_path.startswith("https://"):
            return signed_path
        
        # Ensure proper /storage/v1 prefix for relative Supabase Storage paths
        clean_rel_path = "/" + signed_path.lstrip("/")
        if not clean_rel_path.startswith("/storage/v1"):
            return f"{self.supabase_url}/storage/v1{clean_rel_path}"

        return f"{self.supabase_url}{clean_rel_path}"

    def get_file_bytes(self, bucket: str, object_path: str) -> bytes:
        import httpx

        clean_key = sanitize_object_key(object_path)
        target_bucket = bucket or self.default_bucket
        url = f"{self.supabase_url}/storage/v1/object/authenticated/{target_bucket}/{clean_key}"
        headers = self._get_headers()

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code != 200:
                raise FileNotFoundError(
                    f"Failed to fetch object {clean_key} (status {response.status_code})"
                )
            return response.content


def get_storage_provider() -> BaseStorageProvider:
    """
    Factory function selecting the appropriate storage provider:
    - Production: Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY; fails closed if missing.
    - Local: Uses LocalStorageProvider if Supabase Storage config is absent.
    """
    supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
    service_role_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    bucket = (os.getenv("SUPABASE_STORAGE_BUCKET") or "medical-documents").strip()
    environment = (os.getenv("ENVIRONMENT") or "development").strip().lower()

    # If Supabase Storage credentials are fully configured, use cloud provider
    if supabase_url and service_role_key:
        return SupabaseStorageProvider(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            default_bucket=bucket
        )

    # In production, disallow silent fallback to ephemeral disk
    if environment == "production":
        raise RuntimeError(
            "[STORAGE CONFIGURATION ERROR] In production environment, SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY must be configured for persistent document storage. "
            "Silent fallback to ephemeral local container filesystem is disallowed."
        )

    # Partial configuration in development should fail clearly
    if supabase_url and not service_role_key:
        raise RuntimeError(
            "[STORAGE CONFIGURATION ERROR] SUPABASE_URL is configured but SUPABASE_SERVICE_ROLE_KEY is missing."
        )

    # Local development default
    return LocalStorageProvider(default_bucket=bucket)


# Global storage service instance
storage_service = get_storage_provider()
