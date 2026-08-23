import sqlite3

conn = sqlite3.connect('orma.db')
cursor = conn.cursor()

tables = [
    'wellness', 'tsgp', 'rlj', 'owe', 'notifications', 'memories', 
    'audits', 'ale', 'medicine_reminders', 'health_events', 'health_records'
]

# also need to make sure the actual table names are correct.
# let's just query the sqlite_master for all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
all_tables = [r[0] for r in cursor.fetchall()]

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
    ("timestamp", "DATETIME"),
    ("is_caregiver_notified", "BOOLEAN DEFAULT 0"),
    ("caregiver_notified_at", "DATETIME")
]

for table in all_tables:
    if table.startswith('sqlite_') or table == 'alembic_version':
        continue
        
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass
            else:
                pass

conn.commit()
conn.close()
print("Migration completed.")
