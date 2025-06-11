from flask import Flask, jsonify
from prometheus_client import Counter, generate_latest
import time, threading, os

app = Flask(__name__)

# Prometheus metrics
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests', ['code'])
FAILURES = Counter('http_failures_total', 'Failure Count')
LOAD_REQUESTS = Counter('load_requests_total', 'CPU Load triggered')
DISKFILL_REQUESTS = Counter('diskfill_triggered_total', 'Disk Fill triggered')

@app.route('/')
def hello():
    REQUESTS.labels(code="200").inc()
    return "👋 Hello from Microfail App!"

@app.route('/health')
def health():
    REQUESTS.labels(code="200").inc()
    return jsonify(status="ok")

@app.route('/fail')
def fail():
    REQUESTS.labels(code="500").inc()
    FAILURES.inc()
    return "💥 Intentional Failure", 500

@app.route('/load')
def load():
    LOAD_REQUESTS.inc()
    def cpu_burn():
        t_end = time.time() + 5
        while time.time() < t_end:
            _ = sum(i*i for i in range(10000))
    threading.Thread(target=cpu_burn).start()
    return "🔥 CPU load triggered!"

@app.route('/diskfill')
def diskfill():
    DISKFILL_REQUESTS.inc()
    try:
        with open("/tmp/filljunk", "wb") as f:
            f.write(os.urandom(100 * 1024 * 1024))  # 100MB
        return "💾 Disk fill complete (100MB written)."
    except Exception as e:
        return f"❌ Disk fill failed: {str(e)}", 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
