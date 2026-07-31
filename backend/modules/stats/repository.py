from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

USERS_COLLECTION = "users"
PROFILES_COLLECTION = "student_profiles"
SESSIONS_COLLECTION = "mock_test_sessions"
BATTLES_COLLECTION = "battles"
QUESTIONS_COLLECTION = "questions_public"


class StatsRepository:
    def __init__(self, db: AsyncIOMotorDatabase, questions_db: AsyncIOMotorDatabase):
        self.db = db
        self.questions_db = questions_db
        self.users = db[USERS_COLLECTION]
        self.profiles = db[PROFILES_COLLECTION]
        self.sessions = db[SESSIONS_COLLECTION]
        self.battles = db[BATTLES_COLLECTION]
        self.questions = questions_db[QUESTIONS_COLLECTION]

    # ---------- users ----------
    async def count_users(self) -> int:
        return await self.users.count_documents({})

    async def count_verified_users(self) -> int:
        return await self.users.count_documents({"is_verified": True})

    async def count_active_users(self) -> int:
        return await self.users.count_documents({"is_active": True})

    async def count_users_with_profile(self) -> int:
        return await self.profiles.count_documents({})

    async def count_users_since(self, since: datetime) -> int:
        return await self.users.count_documents({"created_at": {"$gte": since}})

    async def signup_trend(self, days: int) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days - 1)
        pipeline = [
            {"$match": {"created_at": {"$gte": since}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        return [row async for row in self.users.aggregate(pipeline)]

    async def by_target_exam(self) -> list[dict]:
        pipeline = [
            {
                "$group": {
                    "_id": {"$ifNull": ["$target_exam", "unspecified"]},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
        ]
        return [row async for row in self.profiles.aggregate(pipeline)]

    # ---------- sessions ----------
    async def count_sessions(self, status: str | None = None) -> int:
        q: dict = {}
        if status:
            q["status"] = status
        return await self.sessions.count_documents(q)

    async def count_sessions_since(self, since: datetime) -> int:
        return await self.sessions.count_documents({"created_at": {"$gte": since}})

    # ---------- battles ----------
    async def count_battles(self) -> int:
        return await self.battles.count_documents({})

    async def count_battles_since(self, since: datetime) -> int:
        return await self.battles.count_documents({"completed_at": {"$gte": since}})

    # ---------- questions ----------
    async def count_questions(self) -> int:
        return await self.questions.count_documents({})
