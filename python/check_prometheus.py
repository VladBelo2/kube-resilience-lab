import subprocess
import time
import sys
import json
import functools

print = functools.partial(print, flush=True)

def check_prometheus_targets(max_attempts=10, delay=10):
    url = "http://localhost/api/v1/targets"
    headers = {"Host": "prometheus.kube-lab.local"}

    for attempt in range(1, max_attempts + 1):
        print(f"[INFO] Checking Prometheus targets (attempt {attempt}/{max_attempts})")

        try:
            result = subprocess.run(
                ["curl", "-s", "--resolve", f"{headers['Host']}:80:127.0.0.1", url],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0 or not result.stdout.strip():
                print("[WARN] Prometheus not reachable yet.")
                time.sleep(delay)
                continue

            stdout = result.stdout.strip()

            try:
                data = json.loads(stdout)
            except json.JSONDecodeError as json_err:
                print(f"[ERROR] Failed to parse JSON: {json_err}")
                print(f"[DEBUG] Raw output:\n{stdout[:300]}...")  # print first 300 chars for inspection
                time.sleep(delay)
                continue

            active_targets = data.get("data", {}).get("activeTargets", [])
            healthy = [t for t in active_targets if t.get("health", "").lower() == "up"]

            if healthy:
                print(f"✅ Prometheus has {len(healthy)} healthy targets")
                return 0
            else:
                print(f"[WAIT] Prometheus up, but targets not healthy (attempt {attempt}/{max_attempts})")

        except Exception as e:
            print(f"[ERROR] Exception occurred: {e}")

        time.sleep(delay)

    print("❌ Prometheus targets not healthy after timeout.")
    return 1

if __name__ == "__main__":
    sys.exit(check_prometheus_targets())
