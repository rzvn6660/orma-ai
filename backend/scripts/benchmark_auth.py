import time
import concurrent.futures
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def do_login(i):
    t0 = time.time()
    resp = client.post('/api/auth/login', json={'email': 'test1@gmail.com', 'password': 'Password123!'})
    dur = round((time.time() - t0) * 1000, 2)
    return (resp.status_code, dur)

def main():
    print("--- AUTH BENCHMARK ---")
    single = do_login(0)
    print(f"1 login: status {single[0]}, duration {single[1]} ms")

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        res_5 = list(pool.map(do_login, range(5)))
    tot_5 = round((time.time() - t0) * 1000, 2)
    print(f"5 concurrent logins (total time: {tot_5} ms):")
    for idx, r in enumerate(res_5):
        print(f"  Req {idx+1}: status {r[0]}, duration {r[1]} ms")

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        res_10 = list(pool.map(do_login, range(10)))
    tot_10 = round((time.time() - t0) * 1000, 2)
    print(f"10 concurrent logins (total time: {tot_10} ms):")
    for idx, r in enumerate(res_10):
        print(f"  Req {idx+1}: status {r[0]}, duration {r[1]} ms")

if __name__ == '__main__':
    main()
