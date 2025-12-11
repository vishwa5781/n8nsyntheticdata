import random
import datetime
import numpy as np
from typing import List, Dict, Any
import json

# ===== Configuration =====
ENVIRONMENTS = ["dev", "staging", "prod"]
SERVICES = [
    "payment-api", "auth-service", "user-service", 
    "db-proxy", "cache-service", "notification-service",
    "order-service", "inventory-service"
]
PODS_PER_SERVICE = {"dev": 2, "staging": 3, "prod": 5}
METRICS_TYPES = ["cpu_usage", "memory_usage", "request_rate", "latency_p50", "latency_p95", "latency_p99", "error_rate"]

# ===== Time Series Generation =====
def generate_baseline_timeseries(hours: int = 24, interval_minutes: int = 5, 
                                  baseline: float = 50.0, noise: float = 5.0) -> List[Dict]:
    """Generate realistic time-series with daily patterns and noise"""
    points = int(hours * 60 / interval_minutes)
    now = datetime.datetime.utcnow()
    
    data = []
    for i in range(points):
        timestamp = now - datetime.timedelta(minutes=(points - i) * interval_minutes)
        
        # Daily cycle: lower at night, higher during business hours
        hour = timestamp.hour
        daily_factor = 1.0 + 0.3 * np.sin((hour - 6) * np.pi / 12)  # Peak at ~18:00
        
        # Add noise and trend
        value = baseline * daily_factor + np.random.normal(0, noise)
        value = max(0, value)  # No negative values
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "value": round(value, 2)
        })
    
    return data

def inject_anomaly(data: List[Dict], anomaly_type: str = "spike", 
                   start_percent: float = 0.6, duration_percent: float = 0.1,
                   magnitude: float = 2.0) -> List[Dict]:
    """Inject realistic anomalies into time-series"""
    total = len(data)
    start_idx = int(total * start_percent)
    duration = int(total * duration_percent)
    
    for i in range(start_idx, min(start_idx + duration, total)):
        if anomaly_type == "spike":
            # Sudden spike with gradual recovery
            factor = magnitude * np.exp(-(i - start_idx) / (duration / 3))
            data[i]["value"] *= factor
        elif anomaly_type == "gradual":
            # Gradual increase then plateau
            progress = (i - start_idx) / duration
            factor = 1.0 + (magnitude - 1.0) * min(progress * 2, 1.0)
            data[i]["value"] *= factor
        elif anomaly_type == "drop":
            # Sudden drop (service degradation)
            data[i]["value"] *= 0.3
    
    return data

# ===== Metrics Generation =====
def generate_cpu_metrics(service: str, env: str, hours: int = 24, 
                         with_anomaly: bool = False) -> Dict[str, Any]:
    """Generate CPU usage metrics for a service"""
    baseline = {"dev": 30, "staging": 45, "prod": 60}[env]
    data = generate_baseline_timeseries(hours=hours, baseline=baseline, noise=5)
    
    if with_anomaly:
        data = inject_anomaly(data, anomaly_type="spike", magnitude=2.5)
    
    # Per-pod breakdown
    num_pods = PODS_PER_SERVICE[env]
    pod_data = {}
    for i in range(num_pods):
        pod_name = f"{service}-{i:02d}"
        # Vary pod utilization slightly
        pod_baseline = baseline * (0.8 + random.random() * 0.4)
        pod_series = generate_baseline_timeseries(hours=hours, baseline=pod_baseline, noise=3)
        pod_data[pod_name] = pod_series
    
    return {
        "service": service,
        "environment": env,
        "metric": "cpu_usage",
        "unit": "percent",
        "aggregated": data,
        "pods": pod_data,
        "statistics": calculate_statistics(data)
    }

def generate_latency_metrics(service: str, env: str, hours: int = 24,
                             with_anomaly: bool = False) -> Dict[str, Any]:
    """Generate latency metrics (P50, P95, P99)"""
    baseline_p50 = {"dev": 50, "staging": 80, "prod": 120}[env]
    
    p50_data = generate_baseline_timeseries(hours=hours, baseline=baseline_p50, noise=10)
    p95_data = generate_baseline_timeseries(hours=hours, baseline=baseline_p50 * 2.5, noise=20)
    p99_data = generate_baseline_timeseries(hours=hours, baseline=baseline_p50 * 4.0, noise=30)
    
    if with_anomaly:
        p50_data = inject_anomaly(p50_data, anomaly_type="gradual", magnitude=1.8)
        p95_data = inject_anomaly(p95_data, anomaly_type="spike", magnitude=3.0)
        p99_data = inject_anomaly(p99_data, anomaly_type="spike", magnitude=4.0)
    
    return {
        "service": service,
        "environment": env,
        "metric": "latency",
        "unit": "milliseconds",
        "p50": p50_data,
        "p95": p95_data,
        "p99": p99_data,
        "statistics": {
            "p50": calculate_statistics(p50_data),
            "p95": calculate_statistics(p95_data),
            "p99": calculate_statistics(p99_data)
        }
    }

def generate_error_rate_metrics(service: str, env: str, hours: int = 24,
                                with_anomaly: bool = False) -> Dict[str, Any]:
    """Generate error rate metrics"""
    baseline = {"dev": 0.5, "staging": 0.3, "prod": 0.1}[env]
    data = generate_baseline_timeseries(hours=hours, baseline=baseline, noise=0.1)
    
    if with_anomaly:
        data = inject_anomaly(data, anomaly_type="spike", magnitude=10.0)
    
    return {
        "service": service,
        "environment": env,
        "metric": "error_rate",
        "unit": "percent",
        "data": data,
        "statistics": calculate_statistics(data)
    }

def generate_memory_metrics(service: str, env: str, hours: int = 24,
                            with_anomaly: bool = False) -> Dict[str, Any]:
    """Generate memory usage metrics"""
    baseline = {"dev": 40, "staging": 55, "prod": 70}[env]
    data = generate_baseline_timeseries(hours=hours, baseline=baseline, noise=3)
    
    if with_anomaly:
        data = inject_anomaly(data, anomaly_type="gradual", magnitude=1.6)
    
    return {
        "service": service,
        "environment": env,
        "metric": "memory_usage",
        "unit": "percent",
        "data": data,
        "statistics": calculate_statistics(data)
    }

def generate_request_rate_metrics(service: str, env: str, hours: int = 24,
                                  with_anomaly: bool = False) -> Dict[str, Any]:
    """Generate request rate metrics"""
    baseline = {"dev": 50, "staging": 200, "prod": 1000}[env]
    data = generate_baseline_timeseries(hours=hours, baseline=baseline, noise=baseline * 0.1)
    
    if with_anomaly:
        data = inject_anomaly(data, anomaly_type="spike", magnitude=3.0)
    
    return {
        "service": service,
        "environment": env,
        "metric": "request_rate",
        "unit": "requests_per_second",
        "data": data,
        "statistics": calculate_statistics(data)
    }

# ===== Statistics =====
def calculate_statistics(data: List[Dict]) -> Dict[str, float]:
    """Calculate statistical summary of time-series"""
    values = [point["value"] for point in data]
    
    # Compare with previous period (first half vs second half)
    midpoint = len(values) // 2
    previous_avg = np.mean(values[:midpoint])
    current_avg = np.mean(values[midpoint:])
    delta_percent = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
    
    return {
        "min": round(float(np.min(values)), 2),
        "max": round(float(np.max(values)), 2),
        "mean": round(float(np.mean(values)), 2),
        "median": round(float(np.median(values)), 2),
        "p95": round(float(np.percentile(values, 95)), 2),
        "p99": round(float(np.percentile(values, 99)), 2),
        "std_dev": round(float(np.std(values)), 2),
        "delta_vs_previous_period": round(delta_percent, 2)
    }

# ===== Logs Generation =====
def generate_logs(service: str, env: str, hours: int = 1, 
                 with_errors: bool = False) -> List[Dict[str, Any]]:
    """Generate structured application logs"""
    logs = []
    now = datetime.datetime.utcnow()
    
    # Log frequency based on environment
    logs_per_hour = {"dev": 50, "staging": 200, "prod": 1000}[env]
    num_logs = hours * logs_per_hour
    
    log_levels = ["INFO", "WARN", "ERROR"]
    log_weights = [0.85, 0.12, 0.03] if not with_errors else [0.60, 0.20, 0.20]
    
    for i in range(num_logs):
        timestamp = now - datetime.timedelta(seconds=random.randint(0, hours * 3600))
        level = random.choices(log_levels, weights=log_weights)[0]
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "service": service,
            "environment": env,
            "level": level,
            "trace_id": f"trace-{random.randint(100000, 999999)}",
            "span_id": f"span-{random.randint(100000, 999999)}",
            "pod": f"{service}-{random.randint(0, PODS_PER_SERVICE[env]-1):02d}",
        }
        
        if level == "INFO":
            log_entry["message"] = random.choice([
                "Request processed successfully",
                "Database query executed",
                "Cache hit for key",
                "User authenticated",
                "Payment processed"
            ])
        elif level == "WARN":
            log_entry["message"] = random.choice([
                "High latency detected",
                "Connection pool near capacity",
                "Retry attempt for failed request",
                "Rate limit approaching threshold"
            ])
        else:  # ERROR
            log_entry["message"] = random.choice([
                "Database connection timeout",
                "Failed to process payment",
                "Service unavailable: downstream dependency",
                "Memory allocation failed",
                "Invalid request parameters"
            ])
            log_entry["stack_trace"] = "at com.example.service.Handler.process(Handler.java:42)"
        
        logs.append(log_entry)
    
    return sorted(logs, key=lambda x: x["timestamp"])

# ===== Traces Generation =====
def generate_traces(service: str, env: str, count: int = 10,
                   with_slow_traces: bool = False) -> List[Dict[str, Any]]:
    """Generate distributed traces"""
    traces = []
    now = datetime.datetime.utcnow()
    
    for i in range(count):
        trace_id = f"trace-{random.randint(100000, 999999)}"
        start_time = now - datetime.timedelta(seconds=random.randint(0, 3600))
        
        # Create trace tree
        spans = []
        
        # Root span (API gateway)
        root_duration = random.randint(50, 200) if not with_slow_traces else random.randint(500, 2000)
        spans.append({
            "trace_id": trace_id,
            "span_id": f"span-{i}-0",
            "parent_span_id": None,
            "service": "api-gateway",
            "operation": "POST /api/payment",
            "start_time": start_time.isoformat(),
            "duration_ms": root_duration,
            "status": "ok"
        })
        
        # Child spans
        child_services = [service, "db-proxy", "auth-service"]
        offset = 5
        for idx, child_service in enumerate(child_services):
            duration = random.randint(10, 50) if not with_slow_traces else random.randint(100, 800)
            spans.append({
                "trace_id": trace_id,
                "span_id": f"span-{i}-{idx+1}",
                "parent_span_id": f"span-{i}-0",
                "service": child_service,
                "operation": f"{child_service}.process",
                "start_time": (start_time + datetime.timedelta(milliseconds=offset)).isoformat(),
                "duration_ms": duration,
                "status": "ok" if not with_slow_traces or random.random() > 0.3 else "error"
            })
            offset += duration
        
        traces.append({
            "trace_id": trace_id,
            "root_service": "api-gateway",
            "environment": env,
            "total_duration_ms": root_duration,
            "span_count": len(spans),
            "spans": spans
        })
    
    return traces

# ===== Alerts Generation =====
def generate_alerts(service: str, env: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Generate alert events"""
    alerts = []
    now = datetime.datetime.utcnow()
    
    # Generate 0-3 alerts in the time window
    num_alerts = random.randint(0, 3)
    
    alert_types = [
        {"name": "HighCPUUsage", "threshold": "80%", "severity": "warning"},
        {"name": "HighLatency", "threshold": "500ms", "severity": "critical"},
        {"name": "ErrorRateSpike", "threshold": "5%", "severity": "critical"},
        {"name": "MemoryPressure", "threshold": "85%", "severity": "warning"},
        {"name": "LowDiskSpace", "threshold": "90%", "severity": "warning"}
    ]
    
    for i in range(num_alerts):
        alert_type = random.choice(alert_types)
        fired_at = now - datetime.timedelta(minutes=random.randint(30, hours * 60))
        duration_minutes = random.randint(5, 45)
        resolved_at = fired_at + datetime.timedelta(minutes=duration_minutes)
        
        alerts.append({
            "alert_id": f"alert-{random.randint(10000, 99999)}",
            "alert_name": alert_type["name"],
            "service": service,
            "environment": env,
            "severity": alert_type["severity"],
            "threshold": alert_type["threshold"],
            "fired_at": fired_at.isoformat(),
            "resolved_at": resolved_at.isoformat() if random.random() > 0.2 else None,
            "duration_minutes": duration_minutes if random.random() > 0.2 else None,
            "status": "resolved" if random.random() > 0.2 else "firing"
        })
    
    return sorted(alerts, key=lambda x: x["fired_at"], reverse=True)

# ===== Scenario Generation =====
def generate_incident_scenario(scenario_type: str, service: str, env: str) -> Dict[str, Any]:
    """Generate complete incident scenario with correlated data"""
    now = datetime.datetime.utcnow()
    
    scenarios = {
        "cpu_spike": {
            "description": "CPU spike leading to increased latency and pod restarts",
            "cpu": generate_cpu_metrics(service, env, hours=24, with_anomaly=True),
            "latency": generate_latency_metrics(service, env, hours=24, with_anomaly=True),
            "memory": generate_memory_metrics(service, env, hours=24, with_anomaly=False),
            "error_rate": generate_error_rate_metrics(service, env, hours=24, with_anomaly=False),
            "logs": generate_logs(service, env, hours=1, with_errors=True),
            "traces": generate_traces(service, env, count=20, with_slow_traces=True),
            "alerts": generate_alerts(service, env, hours=24),
            "root_cause": "CPU hot loop in payment processing code",
            "recommended_actions": [
                "Investigate payment-api logs for CPU-intensive operations",
                "Profile code for optimization opportunities",
                "Consider horizontal scaling: increase replicas from 3 to 5"
            ]
        },
        "database_slowdown": {
            "description": "Database query latency causing cascading slowdown",
            "cpu": generate_cpu_metrics(service, env, hours=24, with_anomaly=False),
            "latency": generate_latency_metrics(service, env, hours=24, with_anomaly=True),
            "memory": generate_memory_metrics(service, env, hours=24, with_anomaly=False),
            "error_rate": generate_error_rate_metrics(service, env, hours=24, with_anomaly=True),
            "logs": generate_logs(service, env, hours=1, with_errors=True),
            "traces": generate_traces(service, env, count=20, with_slow_traces=True),
            "alerts": generate_alerts(service, env, hours=24),
            "root_cause": "Missing database index on frequently queried table",
            "recommended_actions": [
                "Check db-proxy connection pool utilization",
                "Review slow query logs",
                "Add missing indexes on payment_transactions table"
            ]
        },
        "traffic_surge": {
            "description": "Sudden traffic increase overwhelming service capacity",
            "cpu": generate_cpu_metrics(service, env, hours=24, with_anomaly=True),
            "latency": generate_latency_metrics(service, env, hours=24, with_anomaly=True),
            "memory": generate_memory_metrics(service, env, hours=24, with_anomaly=True),
            "error_rate": generate_error_rate_metrics(service, env, hours=24, with_anomaly=True),
            "request_rate": generate_request_rate_metrics(service, env, hours=24, with_anomaly=True),
            "logs": generate_logs(service, env, hours=1, with_errors=True),
            "traces": generate_traces(service, env, count=20, with_slow_traces=True),
            "alerts": generate_alerts(service, env, hours=24),
            "root_cause": "Marketing campaign drove 3x normal traffic",
            "recommended_actions": [
                "Enable auto-scaling for payment-api",
                "Increase rate limiting thresholds temporarily",
                "Scale replicas: 3 → 8 immediately"
            ]
        }
    }
    
    return scenarios.get(scenario_type, scenarios["cpu_spike"])

# ===== Comparison with Past Period =====
def compare_metrics_with_past(service: str, env: str, metric_type: str,
                              current_hours: int = 24, past_hours: int = 24) -> Dict[str, Any]:
    """Compare current metrics with previous period"""
    
    # Generate current and past data
    if metric_type == "cpu":
        current = generate_cpu_metrics(service, env, hours=current_hours, with_anomaly=True)
        past = generate_cpu_metrics(service, env, hours=past_hours, with_anomaly=False)
    elif metric_type == "latency":
        current = generate_latency_metrics(service, env, hours=current_hours, with_anomaly=True)
        past = generate_latency_metrics(service, env, hours=past_hours, with_anomaly=False)
    elif metric_type == "error_rate":
        current = generate_error_rate_metrics(service, env, hours=current_hours, with_anomaly=True)
        past = generate_error_rate_metrics(service, env, hours=past_hours, with_anomaly=False)
    else:
        return {"error": "Invalid metric type"}
    
    # Calculate comparison
    comparison = {
        "service": service,
        "environment": env,
        "metric_type": metric_type,
        "current_period": current,
        "past_period": past,
        "comparison_summary": {
            "significant_change": True,
            "trend": "increasing",
            "explanation": f"{metric_type} has increased significantly in the current period"
        }
    }
    
    return comparison
