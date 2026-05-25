from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.users.constants import (
    BATTLES_COLLECTION,
    MOCK_TEST_SESSIONS_COLLECTION,
    STUDENT_PROFILES_COLLECTION,
    USERS_COLLECTION,
)


class UsersRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db[USERS_COLLECTION]
        self.profiles = db[STUDENT_PROFILES_COLLECTION]
        self.sessions = db[MOCK_TEST_SESSIONS_COLLECTION]
        self.battles = db[BATTLES_COLLECTION]

    async def count(self, query: dict[str, Any] | None = None) -> int:
        return await self.users.count_documents(query or {})

    async def list_paginated(
        self,
        skip: int,
        limit: int,
        query: dict[str, Any] | None = None,
    ) -> list[dict]:
        cursor = (
            self.users.find(query or {}, {"hashed_password": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def all_for_export(
        self, query: dict[str, Any] | None = None
    ) -> list[dict]:
        """Read every user matching the query without the password column.

        For the volume of an early-stage product this is fine in-memory; if
        the user table balloons past ~50k rows, switch to a streaming
        StreamingResponse that pipes from the cursor.
        """
        cursor = self.users.find(query or {}, {"hashed_password": 0}).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        return await self.users.find_one({"_id": oid}, {"hashed_password": 0})

    async def get_profile_by_user_id(self, user_id: ObjectId | str) -> Optional[dict]:
        oid = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
        return await self.profiles.find_one({"user_id": oid})

    async def get_profiles_for_users(self, user_ids: list[ObjectId]) -> dict[str, dict]:
        """Bulk profile fetch keyed by user_id string. Avoids N+1 in list
        endpoints."""
        if not user_ids:
            return {}
        cursor = self.profiles.find({"user_id": {"$in": user_ids}})
        out: dict[str, dict] = {}
        async for doc in cursor:
            out[str(doc["user_id"])] = doc
        return out

    async def count_user_sessions(self, user_id: ObjectId) -> tuple[int, int]:
        """Return (total, completed) session counts for a single user."""
        total = await self.sessions.count_documents({"user_id": user_id})
        completed = await self.sessions.count_documents(
            {"user_id": user_id, "status": "completed"}
        )
        return total, completed

    async def count_user_battles(self, user_id: ObjectId) -> int:
        return await self.battles.count_documents(
            {
                "$or": [
                    {"player_a.user_id": user_id},
                    {"player_b.user_id": user_id},
                ]
            }
        )

    async def search_query(self, q: Optional[str]) -> dict[str, Any]:
        """Build a substring-search Mongo filter for the listing endpoint."""
        if not q:
            return {}
        q = q.strip()
        if not q:
            return {}
        # Case-insensitive prefix on email and username; exact-substring on
        # full_name handled separately because that lives in the profile
        # collection.
        return {
            "$or": [
                {"email": {"$regex": q, "$options": "i"}},
                {"username": {"$regex": q, "$options": "i"}},
            ]
        }
