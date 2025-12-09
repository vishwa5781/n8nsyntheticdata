from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
import math
import random


class MetricPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    latency_ms_p50: float
    latency_ms_p95: float
    error_rate_per_min: float


class MetricsResponse(BaseModel):
    service: str
    env: str
    window_minutes: int
    points: List[MetricPoint]


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str


class LogsResponse(BaseModel):
    service: str
    env: str
    entries: List[LogEntry]


def generate_time_series(
    *,
    now: datetime,
    window_minutes: int,
    step_seconds: int = 60,
) -> List[MetricPoint]:
    """Single synthetic pattern for one service (payment-api)."""
    points: List[MetricPoint] = []
    total_steps = int(window_minutes * 60 / step_seconds)

    base_cpu = 50.0
    base_mem = 60.0

    for i in range(total_steps):
        t = now - timedelta(seconds=(total_steps - 1 - i) * step_seconds)
        phase = i / total_steps * 2 * math.pi

        cpu = base_cpu + 25 * math.sin(phase) + random.uniform(-5, 5)
        if 0.6 < i / total_steps < 0.8:
            cpu += random.uniform(10, 30)
        cpu = max(1.0, min(cpu, 99.0))

        mem = base_mem + random.uniform(-7, 7)
        mem = max(5.0, min(mem, 95.0))

        p50 = max(10, 40 + 2 * cpu + random.uniform(-15, 15))
        p95 = p50 + random.uniform(80, 200)

        error_rate = max(0.0, 0.01 * (cpu / 50.0) + random.uniform(0.0, 0.03))

        points.append(
            MetricPoint(
                timestamp=t,
                cpu_percent=round(cpu, 1),
                memory_percent=round(mem, 1),
                latency_ms_p50=round(p50, 1),
                latency_ms_p95=round(p95, 1),
                error_rate_per_min=round(error_rate, 4),
            )
        )

    return points


def generate_logs(*, now: datetime, count: int = 50):
    levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
    base_msgs = [
        "Handled request GET /health",
        "Handled request POST /checkout",
        "Cache miss for key session",
        "Background job completed",
        "Slow response from db-primary",
        "Timeout talking to payment-gateway",
        "High CPU detected on pod payment-api-01",
        "Restarting container due to OOM",
    ]

    entries: List[LogEntry] = []
    for i in range(count):
        ts = now - timedelta(seconds=(count - i) * 15)
        level = random.choice(levels)
        msg = random.choice(base_msgs)
        if i > count * 0.5:
            level = random.choice(["WARN", "ERROR", "ERROR"])
        entries.append(LogEntry(timestamp=ts, level=level, message=msg))

    return entries
