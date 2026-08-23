import sqlite3

def run_migration():
    conn = sqlite3.connect('backend/orma.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE notification_preferences ADD COLUMN reminder_language VARCHAR DEFAULT 'en-IN'")
        conn.commit()
        print("Successfully added reminder_language column to notification_preferences table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("reminder_language column already exists.")
        else:
            print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
