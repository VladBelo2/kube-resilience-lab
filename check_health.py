import subprocess
import time
import sys
import json

def check_all_pods_ready(max_attempts=20, delay=15):
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ["kubectl", "get", "pods", "-A", "-o", "json"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[ERROR] Failed to run kubectl: {result.stderr}")
            sys.exit(1)

        data = json.loads(result.stdout)
        unready_pods = []

        for pod in data["items"]:
            phase = pod["status"].get("phase", "")
            container_statuses = pod["status"].get("containerStatuses", [])
            ready_conditions = pod["status"].get("conditions", [])

            if (
                phase != "Running"
                or not isinstance(container_statuses, list)
                or any(not c.get("ready", False) for c in container_statuses)
                or any(
                    cond.get("type") == "Ready" and cond.get("status") != "True"
                    for cond in ready_conditions
                )
            ):
                unready_pods.append(pod["metadata"]["name"])

        print(f"[CHECK] Unready pods: {len(unready_pods)} (attempt {attempt}/{max_attempts})")

        if not unready_pods:
            print("✅ All pods are Ready!")
            return 0

        time.sleep(delay)

    print("❌ Pods failed to become Ready in time.")
    return 1


if __name__ == "__main__":
    sys.exit(check_all_pods_ready())
