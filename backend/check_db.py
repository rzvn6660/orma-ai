import sqlite3

conn = sqlite3.connect('orma.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(medicine_reminders);")
columns = cursor.fetchall()
print("medicine_reminders columns:", [c[1] for c in columns])

cursor.execute("PRAGMA table_info(health_events);")
columns = cursor.fetchall()
print("health_events columns:", [c[1] for c in columns])

conn.close()
