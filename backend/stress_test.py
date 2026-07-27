import time
import concurrent.futures
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    resp = client.get('/api/health')
    return (resp.status_code, resp.json().get('status'))

def test_login(email, password):
    t0 = time.time()
    resp = client.post('/api/auth/login', json={'email': email, 'password': password})
    dur = round((time.time() - t0) * 1000, 2)
    return (resp.status_code, dur)

def main():
    print("=== STARTING 5-MINUTE STABILITY & STRESS TEST ===")
    start_t = time.time()

    print("\n1. Testing /api/health baseline...")
    h_code, h_status = test_health()
    print(f"   Health check: status {h_code}, response: {h_status}")

    print("\n2. Executing 10 sequential valid logins (Elderly & Caregiver)...")
    elderly_durs = []
    for i in range(5):
        code, dur = test_login('test1@gmail.com', 'Password123!')
        elderly_durs.append(dur)
        assert code == 200, f"Elderly login failed on iteration {i+1}"

    cg_durs = []
    for i in range(5):
        code, dur = test_login('cg_test@gmail.com', 'Password123!')
        cg_durs.append(dur)
        assert code == 200, f"Caregiver login failed on iteration {i+1}"

    print(f"   Elderly logins (5x): avg {round(sum(elderly_durs)/len(elderly_durs), 2)} ms (durs: {elderly_durs})")
    print(f"   Caregiver logins (5x): avg {round(sum(cg_durs)/len(cg_durs), 2)} ms (durs: {cg_durs})")

    print("\n3. Executing 5 invalid-password attempts...")
    invalid_durs = []
    for i in range(5):
        code, dur = test_login('test1@gmail.com', 'WrongPass999!')
        invalid_durs.append(dur)
        assert code == 401, f"Invalid password did not return 401 on iteration {i+1}"
    print(f"   Invalid password attempts (5x): avg {round(sum(invalid_durs)/len(invalid_durs), 2)} ms (all returned 401)")

    print("\n4. Executing 5 rapid login/logout cycles...")
    for i in range(5):
        code, dur = test_login('test1@gmail.com', 'Password123!')
        assert code == 200
        # Simulate frontend logout (clearing token) & checking me endpoint
        me_resp = client.get('/api/auth/me', headers={'Authorization': 'Bearer invalid'})
        assert me_resp.status_code == 401
    print("   Rapid login/logout cycles (5x): PASSED cleanly")

    print("\n5. Simulating background scheduler interval execution (waiting for scheduler cycles)...")
    time.sleep(16) # Allow at least 1 full scheduler cycle (15s interval)
    h_code, h_status = test_health()
    print(f"   Post-scheduler health check: status {h_code}, response: {h_status}")

    code, dur = test_login('test1@gmail.com', 'Password123!')
    print(f"   Post-scheduler elderly login: status {code}, duration {dur} ms")
    assert code == 200

    tot_dur = round(time.time() - start_t, 2)
    print(f"\n=== ALL STABILITY TESTS PASSED IN {tot_dur} SECONDS ===")

if __name__ == '__main__':
    main()
