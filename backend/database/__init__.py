from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
import logging

logger = logging.getLogger(__name__)

# Beginner-friendly SQLite setup using robust absolute path with env override support
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("SQLITE_DB_PATH") or os.getenv("DATABASE_PATH") or os.path.join(BASE_DIR, "orma.db")

# Ensure database directory exists if custom path provided
db_dir = os.path.dirname(os.path.abspath(DB_PATH))
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH}"
resolved_db_path = DB_PATH
logger.info(f"[DATABASE] Resolved absolute SQLite database path: {resolved_db_path}")

# connect_args={"check_same_thread": False} is needed for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=10000;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema_migrations():
    """Ensures SQLite tables contain all columns required by updated SQLAlchemy models."""
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        columns_to_add_ocme = [
            ("archived", "BOOLEAN DEFAULT 0"),
            ("trust_score", "FLOAT DEFAULT 50.0"),
            ("source", "VARCHAR(100) DEFAULT 'system'"),
            ("expires_at", "DATETIME")
        ]

        for col_name, col_type in columns_to_add_ocme:
            try:
                cursor.execute(f"ALTER TABLE ocme_memories ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        columns_to_add_audit = [
            ("resource", "VARCHAR"),
            ("outcome", "VARCHAR"),
            ("reason", "VARCHAR"),
            ("actor_id", "VARCHAR"),
            ("subject_id", "VARCHAR"),
            ("created_by", "VARCHAR"),
            ("owned_by", "VARCHAR"),
            ("role", "VARCHAR"),
            ("permission_scope", "VARCHAR"),
            ("organization_id", "VARCHAR"),
            ("session_id", "VARCHAR"),
            ("request_id", "VARCHAR")
        ]
        for col_name, col_type in columns_to_add_audit:
            try:
                cursor.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        columns_to_add_users = [
            ("token_version", "INTEGER DEFAULT 1"),
            ("email_verified", "BOOLEAN DEFAULT 1")
        ]
        for col_name, col_type in columns_to_add_users:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        columns_to_add_notif = [
            ("reminder_language", "VARCHAR DEFAULT 'en-IN'"),
            ("voice_language", "VARCHAR DEFAULT 'auto'")
        ]
        for col_name, col_type in columns_to_add_notif:
            try:
                cursor.execute(f"ALTER TABLE notification_preferences ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        columns_to_add_memory_events = [
            ("visibility", "VARCHAR DEFAULT 'private'")
        ]
        for col_name, col_type in columns_to_add_memory_events:
            try:
                cursor.execute(f"ALTER TABLE memory_events ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        # Create email_verification_otps table if not present
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verification_otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR,
                email VARCHAR,
                otp_hash VARCHAR,
                expires_at DATETIME,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 5,
                is_used BOOLEAN DEFAULT 0,
                created_at DATETIME,
                used_at DATETIME,
                last_sent_at DATETIME
            );
        """)

        # Create notification_preferences table if not present
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR UNIQUE,
                medication_reminder_notifications BOOLEAN NOT NULL DEFAULT 1,
                medication_spoken_alerts BOOLEAN NOT NULL DEFAULT 1,
                missed_medication_alerts BOOLEAN NOT NULL DEFAULT 1,
                medication_adherence_summary BOOLEAN NOT NULL DEFAULT 1,
                reminder_language VARCHAR DEFAULT 'en-IN',
                voice_language VARCHAR DEFAULT 'auto',
                updated_at DATETIME
            );
        """)

        # Populate defaults for existing users without preference records
        cursor.execute("""
            INSERT INTO notification_preferences (user_id, medication_reminder_notifications, medication_spoken_alerts, missed_medication_alerts, medication_adherence_summary, updated_at)
            SELECT id, 
                   CASE WHEN role = 'caregiver' THEN 0 ELSE 1 END,
                   CASE WHEN role = 'caregiver' THEN 0 ELSE 1 END,
                   1,
                   1,
                   CURRENT_TIMESTAMP
            FROM users
            WHERE id NOT IN (SELECT user_id FROM notification_preferences WHERE user_id IS NOT NULL);
        """)

        # Create performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_med_elder_subj ON medicine_reminders(elder_id, subject_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_med_taken_status ON medicine_reminders(taken_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ocme_user_cat ON ocme_memories(user_id, category);")

        # Create RAG documents and chunks tables if not present
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                document_type VARCHAR DEFAULT 'general_document',
                source VARCHAR DEFAULT 'uploaded_file',
                file_path VARCHAR,
                file_size INTEGER DEFAULT 0,
                page_count INTEGER DEFAULT 1,
                content_hash VARCHAR,
                processing_status VARCHAR DEFAULT 'READY',
                extraction_method VARCHAR DEFAULT 'native_text',
                ocr_used BOOLEAN DEFAULT 0,
                ocr_confidence FLOAT,
                error_message TEXT,
                doctor_name VARCHAR,
                hospital_name VARCHAR,
                document_date VARCHAR,
                language VARCHAR DEFAULT 'en',
                metadata_json TEXT,
                created_at DATETIME,
                updated_at DATETIME
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_document_chunks (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                page INTEGER DEFAULT 1,
                section VARCHAR,
                page_or_section VARCHAR,
                source_type VARCHAR DEFAULT 'pdf',
                text_content TEXT NOT NULL,
                embedding TEXT,
                token_count INTEGER DEFAULT 0,
                created_at DATETIME
            );
        """)
        
        # Add any missing columns to existing rag_documents table
        rag_doc_cols = [
            ("file_size", "INTEGER DEFAULT 0"),
            ("page_count", "INTEGER DEFAULT 1"),
            ("content_hash", "VARCHAR"),
            ("processing_status", "VARCHAR DEFAULT 'READY'"),
            ("extraction_method", "VARCHAR DEFAULT 'native_text'"),
            ("ocr_used", "BOOLEAN DEFAULT 0"),
            ("ocr_confidence", "FLOAT"),
            ("error_message", "TEXT"),
            ("doctor_name", "VARCHAR"),
            ("hospital_name", "VARCHAR"),
            ("document_date", "VARCHAR"),
            ("language", "VARCHAR DEFAULT 'en'")
        ]
        for col_name, col_type in rag_doc_cols:
            try:
                cursor.execute(f"ALTER TABLE rag_documents ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        rag_chunk_cols = [
            ("page", "INTEGER DEFAULT 1"),
            ("section", "VARCHAR"),
            ("source_type", "VARCHAR DEFAULT 'pdf'")
        ]
        for col_name, col_type in rag_chunk_cols:
            try:
                cursor.execute(f"ALTER TABLE rag_document_chunks ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_doc_user ON rag_documents(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_doc_hash ON rag_documents(user_id, content_hash);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_chunk_user_doc ON rag_document_chunks(user_id, document_id);")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[MIGRATION WARN] Schema migration bypassed: {e}")

# Run automatic migration on import
ensure_schema_migrations()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
