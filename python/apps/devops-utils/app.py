from flask import Flask, request, render_template
from prometheus_client import Counter, generate_latest
import subprocess

app = Flask(__name__)

# Prometheus metrics
PING_COUNT = Counter('ping_requests_total', 'Ping command usage')
TRACEROUTE_COUNT = Counter('traceroute_requests_total', 'Traceroute command usage')
DNS_COUNT = Counter('dns_requests_total', 'DNS lookup usage')
PKG_COUNT = Counter('package_check_total', 'Package check attempts')
CRASH_COUNT = Counter('crash_triggered_total', 'Crash endpoint triggered')
MEMORY_COUNT = Counter('memory_spike_total', 'Memory spike triggered')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ping')
def ping():
    host = request.args.get('ping_host')
    PING_COUNT.inc()
    if not host:
        return render_template("index.html", result="<div class='alert alert-warning'>Missing host parameter.</div>")
    try:
        output = subprocess.check_output(['ping', '-c', '4', host], stderr=subprocess.STDOUT, timeout=10)
        return render_template("index.html", result=wrap_result("✅ Ping Result", output.decode(), success=True))
    except subprocess.CalledProcessError as e:
        return render_template("index.html", result=wrap_result("❌ Ping Failed", e.output.decode(), success=False)), 500
    except Exception as e:
        return render_template("index.html", result=error_box(str(e))), 500

@app.route('/traceroute')
def traceroute():
    host = request.args.get("traceroute_host")
    if not host:
        return render_template("index.html", result=wrap_result("❌ Missing host parameter.", "", success=False)), 400

    try:
        output = subprocess.check_output(
            ['traceroute', '-m', '8', host],
            stderr=subprocess.STDOUT,
            timeout=10  # Increased timeout
        )
        return render_template("index.html", result=wrap_result("🧭 Traceroute Result", output.decode(), success=True))
    except subprocess.TimeoutExpired:
        return render_template("index.html", result=wrap_result("🧭 Traceroute Timed Out", f"Traceroute to {host} took too long. Try a different host or increase hops.", success=False)), 504
    except Exception as e:
        return render_template("index.html", result=wrap_result("❌ Error", str(e), success=False)), 500

@app.route('/dns')
def dns():
    host = request.args.get('dns_host')
    DNS_COUNT.inc()
    if not host:
        return render_template("index.html", result="<div class='alert alert-warning'>Missing host parameter.</div>")
    try:
        output = subprocess.check_output(['dig', '+short', host], stderr=subprocess.STDOUT, timeout=10)
        return render_template("index.html", result=wrap_result("🔍 DNS Lookup Result", output.decode(), success=True))
    except subprocess.CalledProcessError as e:
        return render_template("index.html", result=wrap_result("❌ DNS Lookup Failed", e.output.decode(), success=False)), 500
    except Exception as e:
        return render_template("index.html", result=error_box(str(e))), 500

@app.route('/package')
def package():
    name = request.args.get('name')
    PKG_COUNT.inc()

    if not name or " " in name.strip():
        return render_template("index.html", result=wrap_result("📦 Invalid Input", "Only single-word package names allowed.", success=False)), 400

    try:
        result = subprocess.run(['which', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stdout:
            msg = f"<b>{name}</b> is installed at: <code>{result.stdout.decode().strip()}</code>"
            return render_template("index.html", result=wrap_result("📦 Package Found", msg, success=True))
        else:
            msg = f"<b>{name}</b> is <span style='color:red;'>NOT</span> installed."
            return render_template("index.html", result=wrap_result("📦 Package Missing", msg, success=False)), 404
    except Exception as e:
        return render_template("index.html", result=error_box(str(e))), 500

@app.route('/memory')
def memory():
    MEMORY_COUNT.inc()
    try:
        _ = bytearray(300 * 1024 * 1024)  # 300MB
        return render_template("index.html", result=wrap_result("🧠 Memory Spike", "Allocated 300MB successfully.", success=True))
    except Exception as e:
        return render_template("index.html", result=error_box(f"❌ Memory allocation failed: {e}")), 500

@app.route('/crash')
def crash():
    CRASH_COUNT.inc()
    return "💥 Simulated crash!", 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

# Helpers

def wrap_result(title, content, success=True):
    header_class = "bg-success" if success else "bg-danger"
    return f"""
    <div class='card mt-4'>
      <div class='card-header {header_class} text-white'>{title}</div>
      <div class='card-body'><pre>{content}</pre></div>
    </div>
    """

def error_box(message):
    return f"<div class='alert alert-danger'>❌ {message}</div>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
