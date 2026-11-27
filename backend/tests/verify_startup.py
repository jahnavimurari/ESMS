import subprocess
import time
import urllib.request
import json
import sys
import os

def test_startup():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    python_exe = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    run_py = os.path.join(backend_dir, "run.py")

    print(f"[*] Starting backend server: {python_exe} {run_py}")
    proc = subprocess.Popen(
        [python_exe, run_py],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        time.sleep(3)
        print("[*] Probing GET http://127.0.0.1:5000/api/health ...")
        req = urllib.request.Request("http://127.0.0.1:5000/api/health")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            print(f"[+] /api/health returned HTTP {res.status}:")
            print(json.dumps(data, indent=2))
            assert data["status"] == "healthy"
            assert data["success"] is True

        print("[*] Probing GET http://127.0.0.1:5000/api/health/db ...")
        req_db = urllib.request.Request("http://127.0.0.1:5000/api/health/db")
        try:
            with urllib.request.urlopen(req_db, timeout=5) as res_db:
                data_db = json.loads(res_db.read().decode())
                print(f"[+] /api/health/db returned HTTP {res_db.status}:")
                print(json.dumps(data_db, indent=2))
        except urllib.error.HTTPError as e:
            err_data = json.loads(e.read().decode())
            print(f"[+] /api/health/db returned expected HTTP {e.code} (Safe unconfigured state):")
            print(json.dumps(err_data, indent=2))
            assert err_data["status"] == "unconfigured"

        print("\n[SUCCESS] Flask Backend startup and health checks validated successfully!")
        return 0
    finally:
        print("[*] Terminating test server process...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("[*] Test server terminated.")

if __name__ == "__main__":
    sys.exit(test_startup())
