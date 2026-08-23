import sqlite3

conn = sqlite3.connect('orma.db')
cursor = conn.cursor()

tables = ['medicine_reminders', 'health_events', 'health_records']
columns_to_add = [
    ("actor_id", "VARCHAR"),
    ("subject_id", "VARCHAR"),
    ("created_by", "VARCHAR"),
    ("owned_by", "VARCHAR"),
    ("role", "VARCHAR"),
    ("permission_scope", "VARCHAR"),
    ("organization_id", "VARCHAR"),
    ("session_id", "VARCHAR"),
    ("request_id", "VARCHAR"),
    ("timestamp", "DATETIME")
]

for table in tables:
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass
            else:
                print(f"Error adding {col_name} to {table}: {e}")

conn.commit()
conn.close()
print("Migration completed.")
