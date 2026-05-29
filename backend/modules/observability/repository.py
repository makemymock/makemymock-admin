"""Mongo aggregations over `usage_events` for the observability page.

The `usage_events` collection is written by the **Client backend**
(via `core/usage_events.py` + the SolverX instrumentation). The Admin
service is read-only here — indexes live in the Client backend's
`_ensure_indexes()` per the project rule."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ObservabilityRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.events = db["usage_events"]

    # ---- Simple counters ----
    async def count_since(self, since: datetime, source: str = "solverx") -> int:
        return await self.events.count_documents(
            {"ts": {"$gte": since}, "source": source},
        )

    async def error_count_since(self, since: datetime, source: str = "solverx") -> int:
        return await self.events.count_documents(
            {"ts": {"$gte": since}, "source": source, "status": "error"},
        )

    async def token_sum_since(self, since: datetime, source: str = "solverx") -> int:
        pipeline = [
            {"$match": {"ts": {"$gte": since}, "source": source}},
            {"$group": {"_id": None, "n": {"$sum": "$total_tokens"}}},
        ]
        async for row in self.events.aggregate(pipeline):
            return int(row.get("n", 0))
        return 0

    # ---- Distinct active users ----
    async def distinct_users_since(self, since: datetime) -> int:
        """Distinct user_ids producing any usage_event since the cutoff.
        Anonymous events (user_id=None) are excluded so the number
        reflects actual logged-in usage."""
        pipeline = [
            {"$match": {"ts": {"$gte": since}, "user_id": {"$ne": None}}},
            {"$group": {"_id": "$user_id"}},
            {"$count": "n"},
        ]
        async for row in self.events.aggregate(pipeline):
            return int(row.get("n", 0))
        return 0

    # ---- Per-model breakdown ----
    async def model_usage_since(self, since: datetime) -> list[dict[str, Any]]:
        pipeline = [
            {"$match": {"ts": {"$gte": since}, "source": "solverx"}},
            {"$group": {
                "_id": "$model",
                "calls": {"$sum": 1},
                "input_tokens": {"$sum": "$input_tokens"},
                "output_tokens": {"$sum": "$output_tokens"},
                "total_tokens": {"$sum": "$total_tokens"},
            }},
            {"$sort": {"total_tokens": -1}},
        ]
        out: list[dict[str, Any]] = []
        async for row in self.events.aggregate(pipeline):
            out.append({
                "model": row.get("_id") or "(unknown)",
                "calls": int(row.get("calls", 0)),
                "input_tokens": int(row.get("input_tokens", 0)),
                "output_tokens": int(row.get("output_tokens", 0)),
                "total_tokens": int(row.get("total_tokens", 0)),
            })
        return out

    # ---- Daily call buckets ----
    async def daily_buckets(self, days: int) -> list[dict[str, Any]]:
        """Day-by-day SolverX call counts. Empty days are NOT padded
        here — caller pads them so the line stays continuous."""
        since = _utc_now() - timedelta(days=days)
        pipeline = [
            {"$match": {"ts": {"$gte": since}, "source": "solverx"}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$ts",
                        "timezone": "UTC",
                    },
                },
                "n": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
        ]
        out: list[dict[str, Any]] = []
        async for row in self.events.aggregate(pipeline):
            out.append({"day": row["_id"], "n": int(row.get("n", 0))})
        return out
