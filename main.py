from datetime import datetime, timezone
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    MetricsResponse,
    LogsResponse,
    generate_time_series,
    generate_logs,
)

SERVICE_NAME = "payment-api"
ENV_NAME = "prod"

app = FastAPI(title="Synthetic Observability API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    window_minutes: int = Query(60, ge=5, le=24 * 60),
):
    """Synthetic metrics for a single service (payment-api)."""
    now = datetime.now(timezone.utc)
    points = generate_time_series(now=now, window_minutes=window_minutes)
    return MetricsResponse(
        service=SERVICE_NAME,
        env=ENV_NAME,
        window_minutes=window_minutes,
        points=points,
    )


@app.get("/logs", response_model=LogsResponse)
def get_logs(
    count: int = Query(50, ge=10, le=500),
):
    """Synthetic logs for a single service (payment-api)."""
    now = datetime.now(timezone.utc)
    entries = generate_logs(now=now, count=count)
    return LogsResponse(service=SERVICE_NAME, env=ENV_NAME, entries=entries)
