"""Mongo I/O for admin contest CRUD + the read-only participants view."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from modules.contest.constants import (
    CONTESTS_COLLECTION,
    PARTICIPATIONS_COLLECTION,
    QUESTIONS_COLLECTION,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContestRepository:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        questions_db: AsyncIOMotorDatabase,
    ):
        self.db = db
        self.questions_db = questions_db
        self.col = db[CONTESTS_COLLECTION]
        self.q_col = questions_db[QUESTIONS_COLLECTION]
        self.part_col = db[PARTICIPATIONS_COLLECTION]

    # --------------------- contests ---------------------

    async def list_contests(self) -> list[dict[str, Any]]:
        cursor = self.col.find({}).sort("start_time", DESCENDING)
        return [d async for d in cursor]

    async def get(self, contest_id: str) -> Optional[dict[str, Any]]:
        try:
            oid = ObjectId(contest_id)
        except Exception:
            return None
        return await self.col.find_one({"_id": oid})

    async def find_overlapping(
        self,
        start: datetime,
        end: datetime,
        *,
        exclude_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Return any contest whose [start_time, end_time] intersects
        [start, end]. Two windows do NOT overlap iff one ends before the
        other starts; we negate that with `$lt` on the boundaries."""
        query: dict[str, Any] = {
            "start_time": {"$lt": end},
            "end_time": {"$gt": start},
        }
        if exclude_id:
            try:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            except Exception:
                pass
        return await self.col.find_one(query)

    async def insert(self, doc: dict[str, Any]) -> str:
        now = _utcnow()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, contest_id: str, updates: dict[str, Any]) -> bool:
        try:
            oid = ObjectId(contest_id)
        except Exception:
            return False
        updates = {**updates, "updated_at": _utcnow()}
        result = await self.col.update_one({"_id": oid}, {"$set": updates})
        return result.matched_count > 0

    async def delete(self, contest_id: str) -> bool:
        try:
            oid = ObjectId(contest_id)
        except Exception:
            return False
        result = await self.col.delete_one({"_id": oid})
        return result.deleted_count > 0

    # --------------------- questions (picker) ---------------------

    async def fetch_questions(self, ids: list[str]) -> list[dict[str, Any]]:
        """Resolve picked question IDs in the order they were picked.

        Mongo's `$in` returns results in arbitrary order, so we re-sort
        client-side by the input list so the admin sees their selection
        in the order they built it."""
        oids: list[ObjectId] = []
        order: dict[str, int] = {}
        for i, raw in enumerate(ids):
            try:
                oid = ObjectId(raw)
            except Exception:
                continue
            oids.append(oid)
            order[str(oid)] = i
        if not oids:
            return []
        docs = [d async for d in self.q_col.find({"_id": {"$in": oids}})]
        docs.sort(key=lambda d: order.get(str(d.get("_id")), 1 << 30))
        return docs

    # --------------------- participants (read-only) ---------------------

    async def list_participants(self, contest_id: str) -> list[dict[str, Any]]:
        try:
            oid = ObjectId(contest_id)
        except Exception:
            return []
        cursor = self.part_col.find({"contest_id": oid}).sort(
            [("score", DESCENDING), ("time_taken_seconds", ASCENDING)]
        )
        return [d async for d in cursor]

    async def count_participants(self, contest_id: str) -> int:
        try:
            oid = ObjectId(contest_id)
        except Exception:
            return 0
        return await self.part_col.count_documents({"contest_id": oid})

    async def hydrate_users(self, user_ids: list[ObjectId]) -> dict[str, dict[str, Any]]:
        if not user_ids:
            return {}
        cursor = self.db["users"].find(
            {"_id": {"$in": user_ids}},
            {"username": 1, "email": 1},
        )
        return {str(d["_id"]): d async for d in cursor}
