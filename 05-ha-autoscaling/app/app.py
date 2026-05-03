from flask import Flask, jsonify, request
import os
import time
import random

app = Flask(__name__)

# Simulate work for load testing
WORK_FACTOR = float(os.environ.get('WORK_FACTOR', 1.0))

@app.route('/')
def index():
    return jsonify({
        'message': 'HA App on EKS',
        'status': 'ok',
        'work_factor': WORK_FACTOR
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ready')
def ready():
    return jsonify({'status': 'ready'}), 200

@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint"""
    cpu_usage = random.uniform(0.1, 0.9)
    return f"""# HELP app_cpu_usage CPU usage percentage
# TYPE app_cpu_usage gauge
app_cpu_usage {cpu_usage}
""", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/work', methods=['POST'])
def do_work():
    """Simulate CPU-intensive work"""
    duration = float(request.json.get('duration', 1)) * WORK_FACTOR
    start = time.time()
    
    # Burn CPU
    while time.time() - start < duration:
        _ = sum(i * i for i in range(10000))
    
    return jsonify({
        'work_completed': duration,
        'elapsed': time.time() - start
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)