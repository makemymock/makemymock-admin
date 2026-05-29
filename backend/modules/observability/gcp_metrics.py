"""Cloud Monitoring API wrapper — 4 key Cloud Run infra metrics.

Caches results in-process for `_CACHE_TTL` seconds so admin-panel
refreshes don't hammer the Monitoring API.

Setup required (one-time, per deploy):
  1. `pip install google-cloud-monitoring` (already in requirements.txt)
  2. Grant the Admin backend's runtime service account
     `roles/monitoring.viewer` on the project named in `GCP_PROJECT_ID`
     (that's the **Client** project — Admin queries Client metrics).
  3. The Monitoring API is enabled by default on every GCP project
     that runs any service — no explicit enable step needed.

If the import fails (package not installed) OR the API call errors,
the service returns an empty payload with `error` populated so the
frontend can render a placeholder instead of crashing."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from config.settings import settings
from modules.observability.schema import InfraResponse, TimePoint

logger = logging.getLogger(__name__)

# How long to keep a successful payload before refetching. Cloud
# Monitoring data updates every ~minute; 60s cache halves request
# volume without making the page feel stale.
_CACHE_TTL = 60.0

# Default time window covered by each chart. 6h is long enough to spot
# daily traffic patterns without paginating through too many points at
# the chart's 5-minute alignment step.
_WINDOW_SECONDS = 6 * 3600
_ALIGNMENT_SECONDS = 300


@dataclass
class _Cache:
    payload: Optional[InfraResponse] = None
    expires_at: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class GcpMetricsService:
    def __init__(self) -> None:
        self._cache = _Cache()

    async def fetch_infra(self) -> InfraResponse:
        """Cached fetch of Cloud Run infra metrics. Concurrent callers
        share one in-flight refresh via the cache lock."""
        now = time.monotonic()
        if self._cache.payload and now < self._cache.expires_at:
            return self._cache.payload

        async with self._cache.lock:
            # Re-check inside the lock — another waiter may have just
            # refreshed.
            now = time.monotonic()
            if self._cache.payload and now < self._cache.expires_at:
                return self._cache.payload

            payload = await self._fetch()
            self._cache.payload = payload
            # Cache successes longer; back off briefly on error so we
            # don't hammer the API in a tight retry loop.
            self._cache.expires_at = now + (_CACHE_TTL if payload.error is None else 15)
            return payload

    async def _fetch(self) -> InfraResponse:
        empty = InfraResponse(
            fetched_at=datetime.now(timezone.utc),
            window_seconds=_WINDOW_SECONDS,
            cloud_run_request_count=[],
            cloud_run_5xx_count=[],
            cloud_run_instance_count=[],
            cloud_run_p95_latency_ms=[],
            error=None,
        )
        if not settings.GCP_PROJECT_ID:
            empty.error = "GCP_PROJECT_ID is not configured."
            return empty

        try:
            from google.cloud import monitoring_v3  # type: ignore
        except Exception as exc:  # noqa: BLE001 — surface the real cause
            # Catch broadly so import-time errors from sub-deps (grpc,
            # protobuf, etc.) get reported with their actual message
            # instead of a generic "not installed" — that misleads on
            # environments where the top-level package is present but
            # a transitive dep is broken.
            empty.error = (
                f"google-cloud-monitoring import failed "
                f"({type(exc).__name__}): {exc}"
            )
            logger.warning(empty.error)
            return empty

        try:
            client = monitoring_v3.MetricServiceClient()
            project = f"projects/{settings.GCP_PROJECT_ID}"
            end_seconds = int(time.time())
            start_seconds = end_seconds - _WINDOW_SECONDS
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": end_seconds},
                "start_time": {"seconds": start_seconds},
            })

            def query(filter_str: str, reducer: str = "REDUCE_SUM") -> list[TimePoint]:
                # Blocking SDK call; offload to thread pool so we
                # don't stall the event loop.
                agg = monitoring_v3.Aggregation({
                    "alignment_period": {"seconds": _ALIGNMENT_SECONDS},
                    "per_series_aligner": (
                        monitoring_v3.Aggregation.Aligner.ALIGN_PERCENTILE_95
                        if "latencies" in filter_str
                        else monitoring_v3.Aggregation.Aligner.ALIGN_RATE
                        if reducer == "REDUCE_SUM"
                        else monitoring_v3.Aggregation.Aligner.ALIGN_MEAN
                    ),
                    "cross_series_reducer": getattr(
                        monitoring_v3.Aggregation.Reducer, reducer,
                    ),
                    "group_by_fields": [],
                })
                results = client.list_time_series(
                    request={
                        "name": project,
                        "filter": filter_str,
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        "aggregation": agg,
                    }
                )
                points: list[TimePoint] = []
                for ts in results:
                    for p in ts.points:
                        end = p.interval.end_time
                        iso = datetime.fromtimestamp(
                            end.seconds + end.nanos / 1e9,
                            tz=timezone.utc,
                        ).isoformat()
                        val = (
                            p.value.double_value
                            or p.value.int64_value
                            or 0
                        )
                        points.append(TimePoint(x=iso, y=float(val)))
                # Sort oldest-first so the chart reads L→R.
                points.sort(key=lambda tp: tp.x)
                return points

            # Cloud Monitoring's metric-filter syntax — scope to Cloud
            # Run revisions, split error rate by response_code_class.
            req_filter = (
                'metric.type="run.googleapis.com/request_count" '
                'AND resource.type="cloud_run_revision"'
            )
            err_filter = (
                'metric.type="run.googleapis.com/request_count" '
                'AND resource.type="cloud_run_revision" '
                'AND metric.labels.response_code_class="5xx"'
            )
            inst_filter = (
                'metric.type="run.googleapis.com/container/instance_count" '
                'AND resource.type="cloud_run_revision"'
            )
            lat_filter = (
                'metric.type="run.googleapis.com/request_latencies" '
                'AND resource.type="cloud_run_revision"'
            )

            loop = asyncio.get_event_loop()
            requests_task = loop.run_in_executor(None, query, req_filter, "REDUCE_SUM")
            errors_task = loop.run_in_executor(None, query, err_filter, "REDUCE_SUM")
            instances_task = loop.run_in_executor(None, query, inst_filter, "REDUCE_MEAN")
            latency_task = loop.run_in_executor(None, query, lat_filter, "REDUCE_PERCENTILE_95")

            requests, errors, instances, latency = await asyncio.gather(
                requests_task, errors_task, instances_task, latency_task,
                return_exceptions=True,
            )

            def or_empty(x):
                if isinstance(x, Exception):
                    logger.warning("metric query failed: %s", x)
                    return []
                return x

            return InfraResponse(
                fetched_at=datetime.now(timezone.utc),
                window_seconds=_WINDOW_SECONDS,
                cloud_run_request_count=or_empty(requests),
                cloud_run_5xx_count=or_empty(errors),
                cloud_run_instance_count=or_empty(instances),
                cloud_run_p95_latency_ms=or_empty(latency),
                error=None,
            )
        except Exception as exc:  # noqa: BLE001 — never break the admin page
            logger.exception("Cloud Monitoring fetch failed")
            empty.error = f"Cloud Monitoring error: {exc}"
            return empty


# Module-level singleton — the in-process cache lives on this instance
# so it survives across requests.
gcp_metrics_service = GcpMetricsService()
