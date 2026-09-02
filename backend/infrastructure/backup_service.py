"""
ORMA AI — Production Database Backup & Disaster Recovery Service
Implements point-in-time, WAL-consistent online SQLite backups, integrity verification,
automated retention lifecycle management, off-site replication adapter, and verified disaster recovery restoration.
"""

import os
import sys
import time
import json
import uuid
import shutil
import hashlib
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default persistent backup storage location (isolated outside public web root)
DEFAULT_BACKUP_DIR = os.getenv("BACKUP_DIR") or os.getenv("SQLITE_BACKUP_DIR")

def get_db_path() -> str:
    from database import DB_PATH
    return DB_PATH

def get_backup_dir(db_path: Optional[str] = None) -> str:
    if DEFAULT_BACKUP_DIR:
        backup_dir = os.path.abspath(DEFAULT_BACKUP_DIR)
    else:
        target_db = db_path or get_db_path()
        db_parent = os.path.dirname(os.path.abspath(target_db))
        backup_dir = os.path.join(db_parent, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def compute_sha256(filepath: str) -> str:
    """Calculates SHA-256 hash of a file for cryptographic integrity verification."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_sqlite_integrity(filepath: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes deep SQLite consistency & structural verification on a database file.
    Returns: (is_valid, status_message, table_counts)
    """
    if not os.path.exists(filepath):
        return False, "File does not exist", {}
    if os.path.getsize(filepath) == 0:
        return False, "Database file is empty (0 bytes)", {}

    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
            if not header.startswith(b"SQLite format 3\x00"):
                return False, "Invalid SQLite header magic bytes", {}

        conn = sqlite3.connect(f"file:{os.path.abspath(filepath)}?mode=ro", uri=True, timeout=10)
        cur = conn.cursor()

        # 1. Quick & Integrity Checks
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchall()
        if not res or res[0][0] != "ok":
            conn.close()
            return False, f"Integrity check failed: {res}", {}

        # 2. Foreign Key Check
        cur.execute("PRAGMA foreign_key_check;")
        fk_errors = cur.fetchall()
        if fk_errors:
            logger.warning(f"[BACKUP-VERIFY] Foreign key mismatches detected: {len(fk_errors)}")

        # 3. Collect Schema & Table Metrics
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cur.fetchall()]
        
        counts = {}
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM [{t}];")
                counts[t] = cur.fetchone()[0]
            except Exception:
                counts[t] = -1

        conn.close()
        return True, "ok", {"tables": tables, "counts": counts}

    except Exception as e:
        return False, f"Verification exception: {type(e).__name__} ({str(e)})", {}


class OffsiteStorageAdapter:
    """
    Adapter for syncing backups to an isolated off-site object store (S3, Cloudflare R2, GCS, or remote disk mount).
    Credentials are read dynamically from environment variables and never logged or persisted.
    """
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "bucket": os.getenv("BACKUP_S3_BUCKET") or os.getenv("OFFSITE_BACKUP_BUCKET"),
            "region": os.getenv("BACKUP_S3_REGION", "us-east-1"),
            "endpoint": os.getenv("BACKUP_S3_ENDPOINT") or os.getenv("AWS_ENDPOINT_URL"),
            "access_key": os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("BACKUP_S3_ACCESS_KEY"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("BACKUP_S3_SECRET_KEY"),
            "offsite_dir": os.getenv("BACKUP_OFFSITE_DIR")
        }

    @classmethod
    def is_configured(cls) -> bool:
        cfg = cls.get_config()
        has_s3 = bool(cfg["bucket"] and cfg["access_key"] and cfg["secret_key"])
        has_remote_dir = bool(cfg["offsite_dir"] and os.path.exists(cfg["offsite_dir"]))
        return has_s3 or has_remote_dir

    @classmethod
    def upload_backup(cls, backup_filepath: str, meta_filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Uploads local verified backup snapshot and metadata to offsite storage.
        """
        cfg = cls.get_config()
        if not cls.is_configured():
            logger.info("[OFFSITE-BACKUP] Off-site storage not configured in environment; skipping cloud sync.")
            return {"status": "SKIPPED", "reason": "No off-site credentials configured"}

        fname = os.path.basename(backup_filepath)
        t0 = time.time()

        # 1. Off-site Directory Mount Sync (Secondary Volume / NFS)
        if cfg["offsite_dir"]:
            dest_dir = os.path.abspath(cfg["offsite_dir"])
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, fname)
            shutil.copy2(backup_filepath, dest_file)
            if meta_filepath and os.path.exists(meta_filepath):
                shutil.copy2(meta_filepath, os.path.join(dest_dir, os.path.basename(meta_filepath)))
            duration_ms = int((time.time() - t0) * 1000)
            logger.info(f"[OFFSITE-BACKUP] Synced {fname} to secondary off-site mount ({duration_ms}ms)")
            return {
                "status": "SUCCESS",
                "provider": "secondary_volume",
                "remote_path": dest_file,
                "duration_ms": duration_ms
            }

        # 2. S3 / R2 / GCS Object Storage Sync
        if cfg["bucket"]:
            try:
                import boto3
                from botocore.config import Config
                
                s3_kwargs = {
                    "aws_access_key_id": cfg["access_key"],
                    "aws_secret_access_key": cfg["secret_key"],
                    "region_name": cfg["region"]
                }
                if cfg["endpoint"]:
                    s3_kwargs["endpoint_url"] = cfg["endpoint"]

                s3_client = boto3.client("s3", **s3_kwargs, config=Config(signature_version="s3v4"))
                
                # Upload DB file (enforcing AES256 server-side encryption)
                s3_client.upload_file(
                    backup_filepath,
                    cfg["bucket"],
                    f"orma_backups/{fname}",
                    ExtraArgs={"ServerSideEncryption": "AES256"}
                )

                # Upload Metadata sidecar
                if meta_filepath and os.path.exists(meta_filepath):
                    m_fname = os.path.basename(meta_filepath)
                    s3_client.upload_file(
                        meta_filepath,
                        cfg["bucket"],
                        f"orma_backups/{m_fname}",
                        ExtraArgs={"ServerSideEncryption": "AES256"}
                    )

                duration_ms = int((time.time() - t0) * 1000)
                logger.info(f"[OFFSITE-BACKUP] Uploaded {fname} to s3://{cfg['bucket']}/orma_backups/ ({duration_ms}ms)")
                return {
                    "status": "SUCCESS",
                    "provider": "s3_compatible",
                    "bucket": cfg["bucket"],
                    "remote_key": f"orma_backups/{fname}",
                    "duration_ms": duration_ms
                }
            except Exception as e:
                logger.error(f"[OFFSITE-BACKUP ERROR] Cloud upload failed: {type(e).__name__} ({str(e)})")
                return {"status": "FAILED", "error": f"{type(e).__name__}: {str(e)}"}

        return {"status": "SKIPPED", "reason": "Unknown provider"}


class BackupService:
    @staticmethod
    def create_backup(
        source_db_path: Optional[str] = None,
        destination_dir: Optional[str] = None,
        retention_count: int = 14,
        sync_offsite: bool = True
    ) -> Dict[str, Any]:
        """
        Creates a consistent, point-in-time online SQLite backup using the native
        SQLite Backup API (non-blocking for concurrent readers/writers in WAL mode).
        """
        from database import engine
        if engine.dialect.name != "sqlite":
            logger.info("[BACKUP] Database dialect is PostgreSQL. Local SQLite backup bypassed (managed via Supabase platform).")
            return {
                "backup_id": "managed-external-supabase",
                "status": "external_managed",
                "dialect": "postgresql",
                "message": "Database backup managed externally via Supabase cloud platform.",
                "duration_ms": 0
            }

        src_path = os.path.abspath(source_db_path or get_db_path())
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source database file not found at: {src_path}")

        dest_dir = get_backup_dir(src_path) if not destination_dir else os.path.abspath(destination_dir)
        os.makedirs(dest_dir, exist_ok=True)

        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = uuid.uuid4().hex[:8]
        backup_filename = f"orma_backup_{timestamp_str}_{backup_id}.db"
        backup_filepath = os.path.join(dest_dir, backup_filename)
        meta_filepath = os.path.join(dest_dir, f"{backup_filename}.meta.json")

        t0 = time.time()
        logger.info(f"[BACKUP] Starting consistent online backup from '{src_path}' to '{backup_filepath}'")

        try:
            # 1. Open read-only connection to source DB
            src_conn = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True, timeout=30)
            # 2. Open destination database connection
            dest_conn = sqlite3.connect(backup_filepath, timeout=30)

            # 3. Stream pages safely with native backup mechanism
            with dest_conn:
                src_conn.backup(dest_conn, pages=250, sleep=0.01)

            dest_conn.close()
            src_conn.close()

            # Set restricted filesystem permissions (Owner read/write only)
            try:
                os.chmod(backup_filepath, 0o600)
            except Exception:
                pass

            duration_ms = int((time.time() - t0) * 1000)
            file_size = os.path.getsize(backup_filepath)
            sha256 = compute_sha256(backup_filepath)

            # 4. Immediate Integrity Verification
            is_valid, msg, metrics = verify_sqlite_integrity(backup_filepath)
            if not is_valid:
                # Remove corrupted snapshot
                if os.path.exists(backup_filepath):
                    os.remove(backup_filepath)
                raise RuntimeError(f"Backup integrity verification failed immediately after creation: {msg}")

            # 5. Write metadata sidecar
            meta_payload = {
                "backup_id": backup_id,
                "filename": backup_filename,
                "filepath": backup_filepath,
                "created_at_utc": datetime.utcnow().isoformat() + "Z",
                "source_db": src_path,
                "file_size_bytes": file_size,
                "sha256_checksum": sha256,
                "duration_ms": duration_ms,
                "integrity_status": "VALID",
                "tables_count": len(metrics.get("tables", [])),
                "record_metrics": metrics.get("counts", {})
            }

            with open(meta_filepath, "w", encoding="utf-8") as mf:
                json.dump(meta_payload, mf, indent=2)

            logger.info(f"[BACKUP] Backup completed successfully: {backup_filename} ({file_size} bytes, {duration_ms}ms, sha256={sha256[:12]}...)")

            # 6. Apply retention pruning
            pruned_count = BackupService.prune_old_backups(dest_dir, max_backups_to_keep=retention_count)
            meta_payload["pruned_old_backups"] = pruned_count

            # 7. Off-site replication sync (if configured)
            if sync_offsite:
                offsite_res = OffsiteStorageAdapter.upload_backup(backup_filepath, meta_filepath)
                meta_payload["offsite_sync"] = offsite_res

            return meta_payload

        except Exception as e:
            logger.error(f"[BACKUP ERROR] Backup creation failed: {type(e).__name__} ({str(e)})")
            if os.path.exists(backup_filepath):
                try:
                    os.remove(backup_filepath)
                except Exception:
                    pass
            raise

    @staticmethod
    def list_backups(backup_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all existing backups with metadata and verification state."""
        b_dir = get_backup_dir() if not backup_dir else os.path.abspath(backup_dir)
        if not os.path.exists(b_dir):
            return []

        backups = []
        for fname in sorted(os.listdir(b_dir), reverse=True):
            if fname.startswith("orma_backup_") and fname.endswith(".db"):
                fpath = os.path.join(b_dir, fname)
                mpath = os.path.join(b_dir, f"{fname}.meta.json")
                
                meta = {}
                if os.path.exists(mpath):
                    try:
                        with open(mpath, "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                    except Exception:
                        pass

                backups.append({
                    "filename": fname,
                    "filepath": fpath,
                    "file_size_bytes": os.path.getsize(fpath) if os.path.exists(fpath) else 0,
                    "has_metadata": os.path.exists(mpath),
                    "sha256": meta.get("sha256_checksum", ""),
                    "created_at": meta.get("created_at_utc", ""),
                    "integrity_status": meta.get("integrity_status", "UNKNOWN")
                })
        return backups

    @staticmethod
    def prune_old_backups(backup_dir: str, max_backups_to_keep: int = 14) -> int:
        """Removes backups exceeding the retention count limit (FIFO)."""
        if not os.path.exists(backup_dir) or max_backups_to_keep <= 0:
            return 0

        db_files = []
        for fname in os.listdir(backup_dir):
            if fname.startswith("orma_backup_") and fname.endswith(".db"):
                fpath = os.path.join(backup_dir, fname)
                db_files.append((os.path.getmtime(fpath), fpath, fname))

        # Sort newest first
        db_files.sort(key=lambda x: x[0], reverse=True)

        pruned = 0
        if len(db_files) > max_backups_to_keep:
            to_remove = db_files[max_backups_to_keep:]
            for _, fpath, fname in to_remove:
                try:
                    os.remove(fpath)
                    meta_path = os.path.join(backup_dir, f"{fname}.meta.json")
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                    pruned += 1
                    logger.info(f"[BACKUP-RETENTION] Pruned aged backup file: {fname}")
                except Exception as e:
                    logger.warning(f"[BACKUP-RETENTION] Failed to delete pruned file {fname}: {e}")
        return pruned

    @staticmethod
    def restore_backup(
        backup_filepath: str,
        target_db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely restores a verified database backup into target database path.
        Validates the backup file before restoring, creates an isolated safety copy of existing DB,
        and performs full post-restore integrity check.
        """
        from database import engine
        if engine.dialect.name != "sqlite":
            raise NotImplementedError("Local SQLite restore cannot be performed when active database is PostgreSQL. Restore via Supabase cloud console.")

        b_path = os.path.abspath(backup_filepath)
        if not os.path.exists(b_path):
            raise FileNotFoundError(f"Backup file not found at: {b_path}")

        target_path = os.path.abspath(target_db_path or get_db_path())
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        # 1. Pre-Restore Integrity Validation
        is_valid, val_msg, metrics = verify_sqlite_integrity(b_path)
        if not is_valid:
            raise ValueError(f"Cannot restore corrupted backup file '{b_path}': {val_msg}")

        # 2. Create safeguard copy of existing target DB if it exists
        safeguard_path = None
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            safeguard_path = f"{target_path}.pre_restore_{uuid.uuid4().hex[:6]}.bak"
            try:
                src_ex = sqlite3.connect(f"file:{target_path}?mode=ro", uri=True, timeout=10)
                dest_ex = sqlite3.connect(safeguard_path, timeout=10)
                with dest_ex:
                    src_ex.backup(dest_ex)
                dest_ex.close()
                src_ex.close()
                logger.info(f"[RESTORE] Created pre-restore safeguard copy at: {safeguard_path}")
            except Exception as e:
                logger.warning(f"[RESTORE] Could not create safeguard copy (proceeding with caution): {e}")

        t0 = time.time()
        logger.info(f"[RESTORE] Restoring from backup '{b_path}' into '{target_path}'")

        try:
            # 3. Stream pages safely into target DB using native backup API
            src_conn = sqlite3.connect(f"file:{b_path}?mode=ro", uri=True, timeout=30)
            dest_conn = sqlite3.connect(target_path, timeout=30)
            
            with dest_conn:
                src_conn.backup(dest_conn, pages=250, sleep=0.01)

            dest_conn.close()
            src_conn.close()

            # 4. Post-Restore Verification
            post_valid, post_msg, post_metrics = verify_sqlite_integrity(target_path)
            if not post_valid:
                if safeguard_path and os.path.exists(safeguard_path):
                    # Rollback to safeguard copy
                    rollback_src = sqlite3.connect(f"file:{safeguard_path}?mode=ro", uri=True)
                    rollback_dest = sqlite3.connect(target_path)
                    with rollback_dest:
                        rollback_src.backup(rollback_dest)
                    rollback_dest.close()
                    rollback_src.close()
                raise RuntimeError(f"Post-restore database verification failed: {post_msg}")

            duration_ms = int((time.time() - t0) * 1000)
            logger.info(f"[RESTORE] Restore completed successfully in {duration_ms}ms")

            return {
                "status": "RESTORED",
                "source_backup": b_path,
                "target_database": target_path,
                "duration_ms": duration_ms,
                "tables_restored": len(post_metrics.get("tables", [])),
                "record_counts": post_metrics.get("counts", {})
            }

        except Exception as e:
            logger.error(f"[RESTORE ERROR] Restore operation failed: {type(e).__name__} ({str(e)})")
            raise

backup_service = BackupService()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = sys.argv[1:]
    
    if "--create" in args:
        res = BackupService.create_backup()
        print(json.dumps(res, indent=2))
    elif "--list" in args:
        res = BackupService.list_backups()
        print(json.dumps(res, indent=2))
    elif "--verify" in args:
        idx = args.index("--verify")
        target_file = args[idx + 1] if len(args) > idx + 1 else ""
        if not target_file:
            print("Usage: python -m infrastructure.backup_service --verify <filepath>")
            sys.exit(1)
        ok, msg, m = verify_sqlite_integrity(target_file)
        print(f"Integrity check: {msg} (Valid={ok})")
        print(json.dumps(m, indent=2))
    else:
        print("ORMA AI Backup Service CLI")
        print("Usage: python -m infrastructure.backup_service [--create | --list | --verify <file>]")
