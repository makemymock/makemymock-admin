"""Business logic for admin contest CRUD + read-only participants view.

The admin owns writes to the `contests` collection. Live (already-started)
contests cannot be edited or deleted — we don't want a participant to
see their question set mutate mid-session. Overlap detection runs on
every create / update and rejects with a 409.

Statuses are computed on read from the stored timestamps so we never
have to run a background job to mutate them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import (
    ContestInvalid,
    ContestNotEditable,
    ContestNotFound,
    ContestOverlap,
    QuestionNotFound,
)
from modules.contest.constants import (
    DEFAULT_RULES_MARKDOWN,
    STATUS_COMPLETED,
    STATUS_LIVE,
    STATUS_SCHEDULED,
)
from modules.contest.repository import ContestRepository
from modules.contest.schema import (
    ContestCreateRequest,
    ContestDetailResponse,
    ContestParticipantsResponse,
    ContestSummary,
    ContestSummaryListResponse,
    ContestUpdateRequest,
    MarkingScheme,
    ParticipantRow,
    QuestionPick,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """Coerce an incoming datetime to a tz-aware UTC datetime.

    The admin form posts ISO strings with a `Z` or offset; Pydantic gives
    us aware values for those. If a naive value sneaks through we assume
    it was meant as UTC (matches the rest of the codebase)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _status(start: datetime, end: datetime, now: datetime | None = None) -> str:
    """Pure helper — used by both list + detail responses."""
    now = now or _utcnow()
    if now < start:
        return STATUS_SCHEDULED
    if now >= end:
        return STATUS_COMPLETED
    return STATUS_LIVE


class ContestService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        questions_db: AsyncIOMotorDatabase,
    ):
        self.repo = ContestRepository(db, questions_db)

    # --------------------- defaults ---------------------

    def default_rules(self) -> str:
        return DEFAULT_RULES_MARKDOWN

    # --------------------- create / update ---------------------

    async def create(self, payload: ContestCreateRequest) -> ContestDetailResponse:
        start = _as_utc(payload.start_time)
        end = start + timedelta(seconds=payload.duration_seconds)

        if start <= _utcnow():
            raise ContestInvalid("Contest start time must be in the future.")

        await self._assert_no_overlap(start, end)
        question_docs = await self._resolve_questions(payload.question_ids)

        doc = {
            "title": payload.title,
            "description": payload.description,
            "rules": payload.rules,
            "start_time": start,
            "end_time": end,
            "duration_seconds": payload.duration_seconds,
            "question_ids": [ObjectId(q["_id"]) if not isinstance(q["_id"], ObjectId) else q["_id"]
                             for q in question_docs],
            "marking": payload.marking.model_dump(),
        }
        contest_id = await self.repo.insert(doc)
        return await self.get(contest_id)

    async def update(
        self, contest_id: str, payload: ContestUpdateRequest,
    ) -> ContestDetailResponse:
        existing = await self.repo.get(contest_id)
        if existing is None:
            raise ContestNotFound()

        now = _utcnow()
        current_start = _as_utc(existing["start_time"])
        if now >= current_start:
            # Locked once the doors open. Doing otherwise would shift
            # questions / timing under live participants.
            raise ContestNotEditable()

        updates: dict[str, Any] = {}
        new_start = _as_utc(payload.start_time) if payload.start_time else current_start
        new_duration = (
            payload.duration_seconds
            if payload.duration_seconds is not None
            else int(existing["duration_seconds"])
        )
        new_end = new_start + timedelta(seconds=new_duration)

        if payload.start_time is not None:
            if new_start <= now:
                raise ContestInvalid("Contest start time must be in the future.")
            updates["start_time"] = new_start
            updates["end_time"] = new_end
        if payload.duration_seconds is not None:
            updates["duration_seconds"] = new_duration
            updates["end_time"] = new_end

        if payload.start_time is not None or payload.duration_seconds is not None:
            await self._assert_no_overlap(new_start, new_end, exclude_id=contest_id)

        if payload.question_ids is not None:
            qdocs = await self._resolve_questions(payload.question_ids)
            updates["question_ids"] = [
                q["_id"] if isinstance(q["_id"], ObjectId) else ObjectId(q["_id"])
                for q in qdocs
            ]
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.rules is not None:
            updates["rules"] = payload.rules
        if payload.marking is not None:
            updates["marking"] = payload.marking.model_dump()

        if updates:
            ok = await self.repo.update(contest_id, updates)
            if not ok:
                raise ContestNotFound()

        return await self.get(contest_id)

    async def delete(self, contest_id: str) -> bool:
        existing = await self.repo.get(contest_id)
        if existing is None:
            raise ContestNotFound()
        now = _utcnow()
        if now >= _as_utc(existing["start_time"]):
            raise ContestNotEditable("Cannot delete a contest after it has started.")
        return await self.repo.delete(contest_id)

    # --------------------- read ---------------------

    async def list_summaries(self) -> ContestSummaryListResponse:
        docs = await self.repo.list_contests()
        # Cheap participant counts via parallel awaits would matter at
        # scale; for an admin console the linear pass is fine.
        items: list[ContestSummary] = []
        for d in docs:
            part_count = await self.repo.count_participants(str(d["_id"]))
            items.append(self._to_summary(d, part_count))
        return ContestSummaryListResponse(items=items)

    async def get(self, contest_id: str) -> ContestDetailResponse:
        doc = await self.repo.get(contest_id)
        if doc is None:
            raise ContestNotFound()
        part_count = await self.repo.count_participants(contest_id)
        summary = self._to_summary(doc, part_count)

        # Hydrate the picked questions from bbd_db.
        ids = [str(q) for q in (doc.get("question_ids") or [])]
        qdocs = await self.repo.fetch_questions(ids)
        questions = [
            QuestionPick(
                id=str(q.get("_id", "")),
                subject=str(q.get("subject") or "Uncategorized"),
                chapter=str(q.get("chapter") or "Uncategorized"),
                topic=str(q.get("topic") or "Uncategorized"),
                question_type=(q.get("questionType") or q.get("question_type") or "single_correct"),
                difficulty=(str(q.get("difficulty")).lower() if q.get("difficulty") else None),
                question_text=str(q.get("questionText") or q.get("question_text") or ""),
            )
            for q in qdocs
        ]

        return ContestDetailResponse(
            **summary.model_dump(),
            rules=doc.get("rules") or "",
            questions=questions,
        )

    async def list_participants(self, contest_id: str) -> ContestParticipantsResponse:
        existing = await self.repo.get(contest_id)
        if existing is None:
            raise ContestNotFound()
        rows = await self.repo.list_participants(contest_id)
        user_oids: list[ObjectId] = []
        for r in rows:
            uid = r.get("user_id")
            if isinstance(uid, ObjectId):
                user_oids.append(uid)
        user_map = await self.repo.hydrate_users(user_oids)

        items: list[ParticipantRow] = []
        for i, r in enumerate(rows):
            uid = r.get("user_id")
            uid_str = str(uid)
            udoc = user_map.get(uid_str) or {}
            items.append(
                ParticipantRow(
                    user_id=uid_str,
                    username=udoc.get("username") or "—",
                    email=udoc.get("email"),
                    entered_at=r.get("entered_at"),
                    started_at=r.get("started_at"),
                    submitted_at=r.get("submitted_at"),
                    score=r.get("score"),
                    correct_count=r.get("correct_count"),
                    wrong_count=r.get("wrong_count"),
                    unattempted_count=r.get("unattempted_count"),
                    time_taken_seconds=r.get("time_taken_seconds"),
                    rank=(i + 1) if r.get("submitted_at") else None,
                )
            )
        return ContestParticipantsResponse(
            contest_id=contest_id, total=len(items), items=items,
        )

    # --------------------- helpers ---------------------

    async def _assert_no_overlap(
        self,
        start: datetime,
        end: datetime,
        *,
        exclude_id: str | None = None,
    ) -> None:
        conflict = await self.repo.find_overlapping(start, end, exclude_id=exclude_id)
        if conflict is not None:
            raise ContestOverlap(
                f"Contest time overlaps existing contest '{conflict.get('title', '')}'."
            )

    async def _resolve_questions(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            raise ContestInvalid("At least one question must be selected.")
        docs = await self.repo.fetch_questions(ids)
        if len(docs) != len(ids):
            # Either an invalid id or a question removed from the catalog.
            raise QuestionNotFound("One or more selected questions could not be found.")
        # v1 limitation — passage parents are excluded from contests
        # because the grader/UI only handle leaf types today. The admin
        # picker filters them out on the client side; we re-check here.
        for d in docs:
            qtype = (d.get("questionType") or d.get("question_type") or "").lower()
            if qtype == "passage":
                raise ContestInvalid(
                    "Passage-type questions are not supported in contests yet."
                )
        return docs

    def _to_summary(self, doc: dict[str, Any], participant_count: int) -> ContestSummary:
        start = _as_utc(doc["start_time"])
        end = _as_utc(doc["end_time"])
        marking_raw = doc.get("marking") or {}
        return ContestSummary(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            description=doc.get("description", "") or "",
            start_time=start,
            end_time=end,
            duration_seconds=int(doc.get("duration_seconds", 0)),
            question_count=len(doc.get("question_ids") or []),
            marking=MarkingScheme(**{
                "correct": float(marking_raw.get("correct", 0)),
                "wrong": float(marking_raw.get("wrong", 0)),
                "unattempted": float(marking_raw.get("unattempted", 0)),
            }),
            status=_status(start, end),
            participant_count=participant_count,
            created_at=_as_utc(doc.get("created_at") or _utcnow()),
            updated_at=_as_utc(doc.get("updated_at") or _utcnow()),
        )
