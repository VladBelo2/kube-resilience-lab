import subprocess
import time
import sys
import json
import functools

print = functools.partial(print, flush=True)  # Ensure print is flushed immediately

def is_ignorable_pod(pod):
    name = pod["metadata"]["name"]
    labels = pod["metadata"].get("labels", {})
    owner_refs = pod["metadata"].get("ownerReferences", [])
    phase = pod["status"].get("phase", "")

    return (
        name.startswith("svclb-") or
        phase == "Succeeded" or
        labels.get("app") == "svclb" or
        any(o.get("kind") == "Job" or o.get("name", "").startswith("helm-install-") for o in owner_refs)
    )

def check_all_pods_ready(max_attempts=20, delay=15):
    last_data = None  # Save for final output

    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ["kubectl", "get", "pods", "-A", "-o", "json"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[ERROR] Failed to run kubectl: {result.stderr}")
            sys.exit(1)

        data = json.loads(result.stdout)
        last_data = data  # Save for final report
        unready_pods = []

        for pod in data["items"]:
            if is_ignorable_pod(pod):
                continue

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
            print("✅ All important pods are Ready!")
            return 0

        time.sleep(delay)

    print("❌ Pods failed to become Ready in time.")
    print("\n📋 Final pod status (wide):")
    subprocess.run(["kubectl", "get", "pods", "-A", "-o", "wide"])

    print("\n🧪 Detailed unready pods:")
    for pod in last_data["items"]:
        if is_ignorable_pod(pod):
            continue

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
            print(f"- Namespace: {pod['metadata']['namespace']}")
            print(f"  Pod:       {pod['metadata']['name']}")
            print(f"  Phase:     {phase}")
            print(f"  Ready:     {[c.get('ready') for c in container_statuses]}")
            print("---")

    return 1

if __name__ == "__main__":
    sys.exit(check_all_pods_ready())
