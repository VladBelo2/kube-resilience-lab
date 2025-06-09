from flask import Flask
from prometheus_client import Counter, generate_latest
import time

app = Flask(__name__)

REQUEST_COUNTER = Counter('http_requests_total', 'Total HTTP Requests')

@app.route('/')
def hello():
    REQUEST_COUNTER.inc()
    return 'Hello from Flask!'

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
