from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from functions import *

app = FastAPI(
    title="EOA Synthetic Data Generator API",
    description="Engineering Operations Assistant - Synthetic observability data for testing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for n8n/Slack integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Configuration Endpoints =====

@app.get("/api/config/environments", tags=["Configuration"])
async def get_environments():
    """List all available environments"""
    return {
        "environments": ENVIRONMENTS,
        "count": len(ENVIRONMENTS)
    }

@app.get("/api/config/services", tags=["Configuration"])
async def get_services(environment: Optional[str] = Query(None, description="Filter by environment")):
    """List all available services"""
    response = {
        "services": SERVICES,
        "count": len(SERVICES)
    }
    
    if environment:
        response["pods_per_service"] = PODS_PER_SERVICE.get(environment, 3)
    
    return response

@app.get("/api/config/metrics-types", tags=["Configuration"])
async def get_metrics_types():
    """List all available metric types"""
    return {
        "metric_types": METRICS_TYPES,
        "count": len(METRICS_TYPES)
    }

# ===== Metrics Endpoints =====

@app.get("/api/metrics/cpu", tags=["Metrics"])
async def get_cpu_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment (dev/staging/prod)"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get CPU metrics for a service"""
    data = generate_cpu_metrics(service, environment, hours, anomaly)
    return data

@app.get("/api/metrics/latency", tags=["Metrics"])
async def get_latency_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get latency metrics (P50/P95/P99) for a service"""
    data = generate_latency_metrics(service, environment, hours, anomaly)
    return data

@app.get("/api/metrics/error-rate", tags=["Metrics"])
async def get_error_rate_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get error rate metrics for a service"""
    data = generate_error_rate_metrics(service, environment, hours, anomaly)
    return data

@app.get("/api/metrics/memory", tags=["Metrics"])
async def get_memory_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get memory usage metrics for a service"""
    data = generate_memory_metrics(service, environment, hours, anomaly)
    return data

@app.get("/api/metrics/request-rate", tags=["Metrics"])
async def get_request_rate_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get request rate metrics for a service"""
    data = generate_request_rate_metrics(service, environment, hours, anomaly)
    return data

@app.get("/api/metrics/all", tags=["Metrics"])
async def get_all_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    anomaly: bool = Query(False, description="Include anomaly injection")
):
    """Get all metrics for a service in one call"""
    return {
        "service": service,
        "environment": environment,
        "time_window_hours": hours,
        "cpu": generate_cpu_metrics(service, environment, hours, anomaly),
        "latency": generate_latency_metrics(service, environment, hours, anomaly),
        "error_rate": generate_error_rate_metrics(service, environment, hours, anomaly),
        "memory": generate_memory_metrics(service, environment, hours, anomaly),
        "request_rate": generate_request_rate_metrics(service, environment, hours, anomaly)
    }

# ===== Comparison Endpoints =====

@app.get("/api/metrics/compare", tags=["Metrics"])
async def compare_metrics(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    metric_type: str = Query("cpu", description="Metric type (cpu/latency/error_rate)")
):
    """Compare current metrics with past 24 hours"""
    data = compare_metrics_with_past(service, environment, metric_type, 
                                     current_hours=24, past_hours=24)
    return data

# ===== Logs Endpoints =====

@app.get("/api/logs", tags=["Observability"])
async def get_logs(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(1, ge=1, le=24, description="Time window in hours"),
    errors: bool = Query(False, description="Include more error logs")
):
    """Get application logs for a service"""
    logs = generate_logs(service, environment, hours, errors)
    return {
        "service": service,
        "environment": environment,
        "time_window_hours": hours,
        "count": len(logs),
        "logs": logs
    }

# ===== Traces Endpoints =====

@app.get("/api/traces", tags=["Observability"])
async def get_traces(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    count: int = Query(10, ge=1, le=100, description="Number of traces"),
    slow: bool = Query(False, description="Generate slow traces for debugging")
):
    """Get distributed traces for a service"""
    traces = generate_traces(service, environment, count, slow)
    return {
        "service": service,
        "environment": environment,
        "count": len(traces),
        "traces": traces
    }

# ===== Alerts Endpoints =====

@app.get("/api/alerts", tags=["Observability"])
async def get_alerts(
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours")
):
    """Get alert history for a service"""
    alerts = generate_alerts(service, environment, hours)
    return {
        "service": service,
        "environment": environment,
        "time_window_hours": hours,
        "count": len(alerts),
        "alerts": alerts
    }

# ===== Scenario Endpoints =====

@app.get("/api/scenarios/{scenario_type}", tags=["Scenarios"])
async def get_scenario(
    scenario_type: str,
    service: str = Query("payment-api", description="Service name"),
    environment: str = Query("prod", description="Environment")
):
    """
    Get complete incident scenario with correlated data
    
    Available scenarios:
    - cpu_spike
    - database_slowdown
    - traffic_surge
    """
    scenario = generate_incident_scenario(scenario_type, service, environment)
    return scenario

@app.get("/api/scenarios/list", tags=["Scenarios"])
async def list_scenarios():
    """List all available scenario types"""
    return {
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
    }

# ===== Health Check =====

@app.get("/health", tags=["System"])
@app.get("/", tags=["System"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EOA Synthetic Data Generator",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# ===== Startup Message =====

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("EOA Synthetic Data Generator API (FastAPI)")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
