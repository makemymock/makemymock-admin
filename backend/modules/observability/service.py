"""Composes usage_events aggregations + GCP infra fetch into the two
response payloads the controller serves."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.observability.gcp_metrics import gcp_metrics_service
from modules.observability.repository import ObservabilityRepository
from modules.observability.schema import (
    InfraResponse,
    ModelUsageRow,
    TimePoint,
    UsageResponse,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _fill_daily_gaps(rows: list[dict], days: int) -> list[TimePoint]:
    """Walk back `days` days and emit one point per day, using 0 for
    any day missing from `rows`. Keeps the line visually continuous."""
    by_day = {r["day"]: r["n"] for r in rows}
    out: list[TimePoint] = []
    today = _utc_now().date()
    for offset in range(days - 1, -1, -1):
        d = today - timedelta(days=offset)
        out.append(TimePoint(x=d.isoformat(), y=float(by_day.get(d.isoformat(), 0))))
    return out


class ObservabilityService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.repo = ObservabilityRepository(db)

    async def usage(self) -> UsageResponse:
        now = _utc_now()
        h24 = now - timedelta(hours=24)
        d7 = now - timedelta(days=7)
        d30 = now - timedelta(days=30)

        calls_24h = await self.repo.count_since(h24)
        calls_7d = await self.repo.count_since(d7)
        tokens_24h = await self.repo.token_sum_since(h24)
        tokens_7d = await self.repo.token_sum_since(d7)
        errors_24h = await self.repo.error_count_since(h24)

        dau = await self.repo.distinct_users_since(h24)
        wau = await self.repo.distinct_users_since(d7)
        mau = await self.repo.distinct_users_since(d30)

        model_rows = await self.repo.model_usage_since(d7)
        daily_rows = await self.repo.daily_buckets(days=14)
        daily_series = _fill_daily_gaps(daily_rows, days=14)

        error_rate = (errors_24h / calls_24h) if calls_24h else 0.0

        return UsageResponse(
            calls_24h=calls_24h,
            calls_7d=calls_7d,
            tokens_24h=tokens_24h,
            tokens_7d=tokens_7d,
            dau=dau,
            wau=wau,
            mau=mau,
            model_usage_7d=[ModelUsageRow(**r) for r in model_rows],
            daily_calls_14d=daily_series,
            error_rate_24h=round(error_rate, 4),
        )

    async def infra(self) -> InfraResponse:
        return await gcp_metrics_service.fetch_infra()
