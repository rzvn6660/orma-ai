import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "orma.db")

def migrate():
    if not os.path.exists(db_path):
        print("Database not found, skipping migration script execution.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(notification_preferences)")
    columns = [row[1] for row in cursor.fetchall()]

    if "voice_language" not in columns:
        print("Adding 'voice_language' column to notification_preferences table...")
        cursor.execute("ALTER TABLE notification_preferences ADD COLUMN voice_language VARCHAR DEFAULT 'auto'")
        conn.commit()
        print("Column 'voice_language' successfully added.")
    else:
        print("Column 'voice_language' already exists in notification_preferences.")

    conn.close()

if __name__ == "__main__":
    migrate()
