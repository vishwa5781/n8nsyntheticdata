from flask import Flask, request, jsonify
from functions import *
import json

app = Flask(__name__)

# ===== Configuration Endpoints =====

@app.route('/api/config/environments', methods=['GET'])
def get_environments():
    """List all available environments"""
    return jsonify({
        "environments": ENVIRONMENTS,
        "count": len(ENVIRONMENTS)
    })

@app.route('/api/config/services', methods=['GET'])
def get_services():
    """List all available services"""
    env = request.args.get('environment')
    
    response = {
        "services": SERVICES,
        "count": len(SERVICES)
    }
    
    if env:
        response["pods_per_service"] = PODS_PER_SERVICE.get(env, 3)
    
    return jsonify(response)

@app.route('/api/config/metrics-types', methods=['GET'])
def get_metrics_types():
    """List all available metric types"""
    return jsonify({
        "metric_types": METRICS_TYPES,
        "count": len(METRICS_TYPES)
    })

# ===== Metrics Endpoints =====

@app.route('/api/metrics/cpu', methods=['GET'])
def get_cpu_metrics():
    """Get CPU metrics for a service
    Query params: service, environment, hours (default 24), anomaly (true/false)
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    data = generate_cpu_metrics(service, env, hours, with_anomaly)
    return jsonify(data)

@app.route('/api/metrics/latency', methods=['GET'])
def get_latency_metrics():
    """Get latency metrics (P50/P95/P99) for a service"""
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    data = generate_latency_metrics(service, env, hours, with_anomaly)
    return jsonify(data)

@app.route('/api/metrics/error-rate', methods=['GET'])
def get_error_rate_metrics():
    """Get error rate metrics for a service"""
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    data = generate_error_rate_metrics(service, env, hours, with_anomaly)
    return jsonify(data)

@app.route('/api/metrics/memory', methods=['GET'])
def get_memory_metrics():
    """Get memory usage metrics for a service"""
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    data = generate_memory_metrics(service, env, hours, with_anomaly)
    return jsonify(data)

@app.route('/api/metrics/request-rate', methods=['GET'])
def get_request_rate_metrics():
    """Get request rate metrics for a service"""
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    data = generate_request_rate_metrics(service, env, hours, with_anomaly)
    return jsonify(data)

@app.route('/api/metrics/all', methods=['GET'])
def get_all_metrics():
    """Get all metrics for a service"""
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    with_anomaly = request.args.get('anomaly', 'false').lower() == 'true'
    
    return jsonify({
        "service": service,
        "environment": env,
        "time_window_hours": hours,
        "cpu": generate_cpu_metrics(service, env, hours, with_anomaly),
        "latency": generate_latency_metrics(service, env, hours, with_anomaly),
        "error_rate": generate_error_rate_metrics(service, env, hours, with_anomaly),
        "memory": generate_memory_metrics(service, env, hours, with_anomaly),
        "request_rate": generate_request_rate_metrics(service, env, hours, with_anomaly)
    })

# ===== Comparison Endpoints =====

@app.route('/api/metrics/compare', methods=['GET'])
def compare_metrics():
    """Compare current metrics with past 24 hours
    Query params: service, environment, metric_type (cpu/latency/error_rate)
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    metric_type = request.args.get('metric_type', 'cpu')
    
    data = compare_metrics_with_past(service, env, metric_type, 
                                     current_hours=24, past_hours=24)
    return jsonify(data)

# ===== Logs Endpoints =====

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get application logs for a service
    Query params: service, environment, hours (default 1), errors (true/false)
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 1))
    with_errors = request.args.get('errors', 'false').lower() == 'true'
    
    logs = generate_logs(service, env, hours, with_errors)
    return jsonify({
        "service": service,
        "environment": env,
        "time_window_hours": hours,
        "count": len(logs),
        "logs": logs
    })

# ===== Traces Endpoints =====

@app.route('/api/traces', methods=['GET'])
def get_traces():
    """Get distributed traces for a service
    Query params: service, environment, count (default 10), slow (true/false)
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    count = int(request.args.get('count', 10))
    with_slow = request.args.get('slow', 'false').lower() == 'true'
    
    traces = generate_traces(service, env, count, with_slow)
    return jsonify({
        "service": service,
        "environment": env,
        "count": len(traces),
        "traces": traces
    })

# ===== Alerts Endpoints =====

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alert history for a service
    Query params: service, environment, hours (default 24)
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    hours = int(request.args.get('hours', 24))
    
    alerts = generate_alerts(service, env, hours)
    return jsonify({
        "service": service,
        "environment": env,
        "time_window_hours": hours,
        "count": len(alerts),
        "alerts": alerts
    })

# ===== Scenario Endpoints =====

@app.route('/api/scenarios/<scenario_type>', methods=['GET'])
def get_scenario(scenario_type):
    """Get complete incident scenario
    Scenario types: cpu_spike, database_slowdown, traffic_surge
    Query params: service, environment
    """
    service = request.args.get('service', 'payment-api')
    env = request.args.get('environment', 'prod')
    
    scenario = generate_incident_scenario(scenario_type, service, env)
    return jsonify(scenario)

@app.route('/api/scenarios/list', methods=['GET'])
def list_scenarios():
    """List all available scenario types"""
    return jsonify({
        "scenarios": [
            {
                "type": "cpu_spike",
                "description": "CPU spike leading to increased latency and pod restarts"
            },
            {
                "type": "database_slowdown",
                "description": "Database query latency causing cascading slowdown"
            },
            {
                "type": "traffic_surge",
                "description": "Sudden traffic increase overwhelming service capacity"
            }
        ]
    })

# ===== Health Check =====

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "EOA Synthetic Data Generator",
        "version": "1.0.0"
    })
