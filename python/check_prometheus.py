import subprocess
import time
import sys
import json
import functools

print = functools.partial(print, flush=True)

def get_ingress_ip():
    try:
        result = subprocess.run(
            ["kubectl", "get", "ingress", "-A", "-o", "json"],
            capture_output=True, text=True, timeout=10
        )
        ingress_data = json.loads(result.stdout)
        for item in ingress_data.get("items", []):
            addresses = item.get("status", {}).get("loadBalancer", {}).get("ingress", [])
            if addresses:
                ip = addresses[0].get("ip") or addresses[0].get("hostname")
                if ip:
                    return ip
    except Exception as e:
        print(f"[ERROR] Failed to extract Ingress IP: {e}")
    # Fallback to localhost if nothing is found
    print("[WARN] Falling back to 127.0.0.1 as Ingress IP.")
    return "127.0.0.1"

def check_prometheus_targets(max_attempts=10, delay=10):
    ingress_ip = get_ingress_ip()
    url = f"http://{ingress_ip}/api/v1/targets"
    headers = {"Host": "prometheus.kube-lab.local"}

    for attempt in range(1, max_attempts + 1):
        print(f"[INFO] Checking Prometheus targets (attempt {attempt}/{max_attempts})")

        if attempt == 1:
            print("🔎 Verifying Ingress status:")
            subprocess.run(["kubectl", "get", "ingress", "-A", "-o", "wide"])
            print()

        try:
            result = subprocess.run(
                ["curl", "-s", "-H", f"Host: {headers['Host']}", url],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0 or not result.stdout.strip():
                print("[WARN] Prometheus not reachable yet.")
                time.sleep(delay)
                continue

            if not result.stdout.strip().startswith("{"):
                print("[WARN] Prometheus responded but not with JSON.")
                print("[DEBUG] Raw output snippet:")
                print(result.stdout.strip()[:300] + "...\n")
                time.sleep(delay)
                continue

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse JSON: {e}")
                print("[DEBUG] Full raw output:")
                print(result.stdout.strip()[:500] + "...\n")
                time.sleep(delay)
                continue

            active_targets = data.get("data", {}).get("activeTargets", [])

            if not active_targets:
                print("[WARN] No active targets found yet.")
                time.sleep(delay)
                continue

            healthy = 0
            for target in active_targets:
                job = target.get("labels", {}).get("job", "unknown")
                status = target.get("health", "unknown")
                print(f"[INFO] Prometheus target: {job} — status: {status}")
                if status == "up":
                    healthy += 1

            if healthy:
                print(f"✅ Prometheus has {healthy} healthy targets")
                return 0
            else:
                print(f"[WAIT] Prometheus is up, but targets not healthy (attempt {attempt}/{max_attempts})")

        except Exception as e:
            print(f"[ERROR] Exception occurred: {e}")

        time.sleep(delay)

    print("❌ Prometheus targets not healthy after timeout.")
    return 1

if __name__ == "__main__":
    sys.exit(check_prometheus_targets())
