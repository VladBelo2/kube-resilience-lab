from prometheus_client import Counter, start_http_server, generate_latest
import requests
import subprocess
import time
from kubernetes import client, config
import sys

try:
    config.load_incluster_config()
    apps_v1 = client.AppsV1Api()
except Exception as e:
    print(f"❌ Failed to initialize Kubernetes client: {e}", flush=True)
    sys.exit(1)  # or retry loop if you want

# Prometheus metrics
RESTART_COUNTER = Counter('remediator_restart_total', 'Total successful remediations', ['job'])
FAILURE_COUNTER = Counter('remediator_failure_total', 'Total failed remediations', ['job'])
CHECK_COUNTER = Counter('remediator_check_total', 'Total checks performed')

# 👇 Emit zero by default so Grafana sees something
RESTART_COUNTER.labels(job="remediator").inc(0)
FAILURE_COUNTER.labels(job="remediator").inc(0)
CHECK_COUNTER.inc(0)

# === Prometheus URL inside the cluster ===
# PROMETHEUS_URL = "http://prometheus.default.svc.cluster.local:9090/api/v1/query"
# PROMETHEUS_URL = "http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/query"
PROMETHEUS_URL = "http://monitoring-kube-prometheus-prometheus.monitoring.svc:9090/api/v1/query"


# Initialize Kubernetes client (auto in-cluster)
config.load_incluster_config()
apps_v1 = client.AppsV1Api()


def get_failed_targets():
    CHECK_COUNTER.inc()
    try:
        resp = requests.get(PROMETHEUS_URL, params={"query": "up == 0 and job != remediator" })
        resp.raise_for_status()  # Raise HTTPError for bad responses
        json_data = resp.json()

        if json_data.get("status") != "success":
            print(f"❌ Prometheus query status: {json_data.get('status')}", flush=True)
            return []

        results = json_data.get("data", {}).get("result", [])
        return [r["metric"]["job"] for r in results]

    except Exception as e:
        print(f"❌ Prometheus query failed: {e}", flush=True)
        # print(f"❌ Full Prometheus response: {resp.text}", flush=True)
        return []

def remediate(job):
    print(f"🛠️ Restarting deployment for: {job}", flush=True)
    try:
        apps_v1.patch_namespaced_deployment(
            name=job,
            namespace="default",
            body={"spec": {"template": {"metadata": {"annotations": {"restarted-at": str(time.time())}}}}}
        )
        RESTART_COUNTER.labels(job=job).inc()
    except Exception as e:
        print(f"❌ Failed to restart {job}: {e}", flush=True)
        FAILURE_COUNTER.labels(job=job).inc()

if __name__ == "__main__":
    print("🚀 Remediator started. Exposing /metrics on port 8001...", flush=True)
    # start_http_server(8001)  # Serve metrics on :8001
    start_http_server(8001, addr="0.0.0.0")

    while True:
        print("🔍 Checking Prometheus for failed targets...", flush=True)
        failed = get_failed_targets()
        for job in failed:
            remediate(job)
        time.sleep(60)
