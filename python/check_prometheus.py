import subprocess
import time
import json
import sys
import functools

print = functools.partial(print, flush=True)  # Ensure print is flushed immediately

def check_prometheus_targets(max_attempts=10, delay=10):
    for attempt in range(1, max_attempts + 1):
        print(f"[INFO] Checking Prometheus targets (attempt {attempt}/{max_attempts})", flush=True)
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:9090/api/v1/targets"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                print("[WARN] Prometheus not reachable yet.")
                time.sleep(delay)
                continue

            data = json.loads(result.stdout)
            targets = data.get("data", {}).get("activeTargets", [])

            if any(t.get("health") == "up" for t in targets):
                print("✅ Prometheus has active targets.")
                return 0
            else:
                print("[WAIT] Prometheus up, but targets not healthy.")
        except Exception as e:
            print(f"[ERROR] Exception: {e}")

        time.sleep(delay)

    print("❌ Prometheus targets not healthy after timeout.")
    return 1

if __name__ == "__main__":
    sys.exit(check_prometheus_targets())
