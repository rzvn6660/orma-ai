import urllib.request
import json
import time
import sqlite3
from datetime import datetime, timedelta
import pytz

BASE_URL = 'http://127.0.0.1:8000'

def login(email, password):
    url = f"{BASE_URL}/api/auth/login"
    payload = json.dumps({'email': email, 'password': password}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        return data['access_token'], data['user']

def make_req(method, endpoint, token, payload=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Authorization': f"Bearer {token}", 'Content-Type': 'application/json'}
    data_bytes = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        return res.status, json.loads(res.read().decode())

def get_db_triggered_at(med_id):
    conn = sqlite3.connect('orma.db')
    cur = conn.cursor()
    cur.execute("SELECT reminder_triggered_at FROM medicine_reminders WHERE id=?", (med_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

print("=== 1. LOGGING IN ===")
token, user = login('test1@gmail.com', 'Password123!')
tz_name = user.get('timezone') or 'Asia/Calcutta'
print(f"Logged in user: {user['email']}, timezone: {tz_name}")

test_cases = [
    ("Once Daily AM", "Once Daily", "08:00 AM"),
    ("Once Daily PM", "Once Daily", "08:00 PM"),
    ("Twice Daily", "Twice Daily", "08:00 AM, 08:00 PM"),
    ("Three Times Daily", "Three Times Daily", "08:00 AM, 01:00 PM, 08:00 PM"),
    ("Boundary 12:00 AM", "Once Daily", "12:00 AM"),
    ("Boundary 12:00 PM", "Once Daily", "12:00 PM"),
    ("Boundary 11:59 PM", "Once Daily", "11:59 PM"),
]

created_ids = []

print("\n=== 2. CREATING MEDICINES WITH ALL TIME PICKER FORMATS ===")
for title, freq, reminder_time in test_cases:
    p = {
        "medicine_name": f"Test {title}",
        "dosage": "10mg",
        "reminder_time": reminder_time,
        "frequency": freq,
        "purpose": "Automated Picker Test",
        "timezone": tz_name
    }
    st, res = make_req('POST', '/api/medicines/', token, p)
    print(f"Created '{title}' -> Status: {st}, ID: {res['id']}, Saved Time: '{res['reminder_time']}'")
    assert res['reminder_time'] == reminder_time
    created_ids.append(res['id'])

print("\n=== 3. VERIFYING RELOAD FROM API ===")
st_get, all_meds = make_req('GET', '/api/medicines/', token)
assert st_get == 200
med_map = {m['id']: m for m in all_meds}
for cid in created_ids:
    assert cid in med_map
    print(f"Reloaded ID {cid}: name='{med_map[cid]['medicine_name']}', time='{med_map[cid]['reminder_time']}'")

print("\n=== 4. REAL SCHEDULER REGRESSION TEST (FUTURE TIME SCHEDULING) ===")
try:
    local_tz = pytz.timezone(tz_name)
except Exception:
    local_tz = pytz.timezone('Asia/Calcutta')

now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
local_now = now_utc.astimezone(local_tz)

# Schedule for next minute + 10s to ensure we catch the next scheduler cycle
future_time = local_now + timedelta(seconds=60)
future_time_str = future_time.strftime("%I:%M %p")

print(f"Current local time: {local_now.strftime('%I:%M:%S %p')}")
print(f"Scheduling future reminder for: {future_time_str}")

p_future = {
    "medicine_name": "Future Reminder Regression Test",
    "dosage": "1 tablet",
    "reminder_time": future_time_str,
    "frequency": "Once Daily",
    "purpose": "Live Scheduler Trigger Test",
    "timezone": tz_name
}

st_fut, res_fut = make_req('POST', '/api/medicines/', token, p_future)
fut_id = res_fut['id']
created_ids.append(fut_id)
print(f"Created future medicine ID: {fut_id} for time '{future_time_str}'")

print("\n=== 5. WAITING FOR SCHEDULER TO TRIGGER IN DB (UP TO 90 SECONDS) ===")
triggered = False
start_wait = time.time()
while time.time() - start_wait < 95:
    db_trig = get_db_triggered_at(fut_id)
    if db_trig is not None:
        print(f"\nSUCCESS! Scheduler triggered reminder at {datetime.now().strftime('%H:%M:%S')}! DB timestamp: {db_trig}")
        triggered = True
        break
    time.sleep(3)
    print(".", end="", flush=True)

print()
for cid in created_ids:
    make_req('DELETE', f"/api/medicines/{cid}", token)
print("Cleaned up test medicine records.")

assert triggered, "Scheduler failed to trigger reminder at scheduled time!"
print("\nALL TIME PICKER & SCHEDULER REGRESSION TESTS PASSED PERFECTLY!")
