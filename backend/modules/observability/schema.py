"""Response schemas for the observability endpoints.

Two sources, two response shapes:
  • UsageResponse  — Mongo `usage_events` (written by the Client backend
                     every time SolverX makes a Vertex AI call).
  • InfraResponse  — GCP Cloud Monitoring (Cloud Run request rate,
                     5xx, instance count, p95 latency).

Time series points use ISO 8601 strings (Vite / React date parsers
round-trip these cleanly into the LineChart `{x, y}` shape)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TimePoint(BaseModel):
    """One bucket in a time-series chart. `x` is ISO 8601 (day or
    timestamp), `y` is the numeric value at that bucket."""
    x: str
    y: float


class ModelUsageRow(BaseModel):
    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int


class UsageResponse(BaseModel):
    """All numbers come from Mongo `usage_events`. No GCP calls."""
    # Disable Pydantic's `model_` namespace protection so the
    # `model_usage_7d` field name (which describes Gemini model usage,
    # nothing to do with Pydantic) doesn't trigger a UserWarning at
    # import time.
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    # Counters (last 24h / 7d windows)
    calls_24h: int
    calls_7d: int
    tokens_24h: int
    tokens_7d: int

    # Distinct user activity in those windows. Counts only events
    # carrying a user_id (anonymous events excluded).
    dau: int   # last 24h
    wau: int   # last 7d
    mau: int   # last 30d

    # Per-model split for the last 7 days, sorted by total_tokens desc.
    model_usage_7d: list[ModelUsageRow]

    # Daily SolverX call counts for the last 14 days (sparkline).
    daily_calls_14d: list[TimePoint]

    # Error rate for last 24h, as a fraction in [0, 1].
    error_rate_24h: float


class InfraResponse(BaseModel):
    """GCP Cloud Monitoring sourced. Empty lists + populated `error`
    if the Monitoring API isn't reachable so the frontend can show a
    helpful banner instead of crashing."""
    model_config = ConfigDict(populate_by_name=True)

    fetched_at: datetime
    window_seconds: int
    cloud_run_request_count: list[TimePoint]
    cloud_run_5xx_count: list[TimePoint]
    cloud_run_instance_count: list[TimePoint]
    cloud_run_p95_latency_ms: list[TimePoint]
    error: Optional[str] = None
