from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.questions.constants import QUESTIONS_COLLECTION


class QuestionsRepository:
    """Read-only access to the `questions` catalog.

    The catalog can live either in the primary makemymock DB (single-DB
    deployments) or in the `bbd_db` schema (Client's split deployment).
    `get_questions_database()` resolves the right handle, so this repo
    just consumes whichever DB is passed in.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db[QUESTIONS_COLLECTION]

    # ---------- catalog tree ----------

    async def aggregate_catalog(self) -> list[dict[str, Any]]:
        """Subject → chapter → topic counts in a single aggregation."""
        pipeline = [
            {
                "$project": {
                    "subject": {"$ifNull": ["$subject", "Uncategorized"]},
                    "chapter": {"$ifNull": ["$chapter", "Uncategorized"]},
                    "topic": {"$ifNull": ["$topic", "Uncategorized"]},
                    "questionType": {"$ifNull": ["$questionType", "single_correct"]},
                    "subCount": {
                        "$cond": [
                            {"$eq": [{"$ifNull": ["$questionType", "single_correct"]}, "passage"]},
                            {"$size": {"$ifNull": ["$passageData.subQuestions", []]}},
                            1,
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": {
                        "subject": "$subject",
                        "chapter": "$chapter",
                        "topic": "$topic",
                    },
                    "question_count": {"$sum": "$subCount"},
                }
            },
            {"$sort": {"_id.subject": 1, "_id.chapter": 1, "_id.topic": 1}},
        ]
        return [row async for row in self.col.aggregate(pipeline)]

    # ---------- listing ----------

    async def list_filtered(
        self,
        *,
        subject: Optional[str],
        chapter: Optional[str],
        topic: Optional[str],
        question_type: Optional[str],
        difficulty: Optional[str],
        q: Optional[str],
        skip: int,
        limit: int,
    ) -> tuple[int, list[dict]]:
        filt = self._build_filter(subject, chapter, topic, question_type, difficulty, q)
        total = await self.col.count_documents(filt)
        cursor = self.col.find(filt).sort("_id", -1).skip(skip).limit(limit)
        items = [doc async for doc in cursor]
        return total, items

    @staticmethod
    def _build_filter(
        subject: Optional[str],
        chapter: Optional[str],
        topic: Optional[str],
        question_type: Optional[str],
        difficulty: Optional[str],
        q: Optional[str],
    ) -> dict[str, Any]:
        # Each filter is its own clause inside a top-level $and. Tolerate
        # camelCase + snake_case storage variants for question_type and
        # difficulty so old ingest jobs don't get hidden by a stricter
        # filter than Mongo actually requires.
        clauses: list[dict[str, Any]] = []
        if subject:
            clauses.append({"subject": subject})
        if chapter:
            clauses.append({"chapter": chapter})
        if topic:
            clauses.append({"topic": topic})
        if question_type:
            clauses.append(
                {
                    "$or": [
                        {"questionType": question_type},
                        {"question_type": question_type},
                    ]
                }
            )
        if difficulty:
            clauses.append(
                {
                    "$or": [
                        {"difficulty": difficulty},
                        {"level": difficulty},
                    ]
                }
            )
        if q and q.strip():
            clauses.append(
                {
                    "$or": [
                        {"questionText": {"$regex": q, "$options": "i"}},
                        {"question_text": {"$regex": q, "$options": "i"}},
                    ]
                }
            )
        if not clauses:
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    async def get_by_id(self, question_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(question_id)
        except Exception:
            return None
        return await self.col.find_one({"_id": oid})
