"""FastAPI routes for admin contest CRUD.

Mounted under /api/v1/contests by api/__init__.py.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from core.dependencies import CurrentAdmin, DBDep, QuestionsDBDep
from modules.contest.schema import (
    ContestCreateRequest,
    ContestDeleteResponse,
    ContestDetailResponse,
    ContestParticipantsResponse,
    ContestSummaryListResponse,
    ContestUpdateRequest,
    DefaultRulesResponse,
)
from modules.contest.service import ContestService

router = APIRouter(prefix="/contests", tags=["Contests"])


@router.get(
    "/default-rules",
    response_model=DefaultRulesResponse,
    summary="Default rules markdown — used to prefill the create form",
)
async def default_rules(
    db: DBDep, questions_db: QuestionsDBDep, _: CurrentAdmin,
) -> DefaultRulesResponse:
    rules = ContestService(db, questions_db).default_rules()
    return DefaultRulesResponse(rules=rules)


@router.get(
    "",
    response_model=ContestSummaryListResponse,
    summary="List every contest (newest start time first)",
)
async def list_contests(
    db: DBDep, questions_db: QuestionsDBDep, _: CurrentAdmin,
) -> ContestSummaryListResponse:
    return await ContestService(db, questions_db).list_summaries()


@router.post(
    "",
    response_model=ContestDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contest. Rejects overlapping time windows.",
)
async def create_contest(
    payload: ContestCreateRequest,
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> ContestDetailResponse:
    return await ContestService(db, questions_db).create(payload)


@router.get(
    "/{contest_id}",
    response_model=ContestDetailResponse,
    summary="Fetch a contest with its hydrated question list",
)
async def get_contest(
    contest_id: str,
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> ContestDetailResponse:
    return await ContestService(db, questions_db).get(contest_id)


@router.patch(
    "/{contest_id}",
    response_model=ContestDetailResponse,
    summary="Update a scheduled contest (locked once it starts)",
)
async def update_contest(
    contest_id: str,
    payload: ContestUpdateRequest,
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> ContestDetailResponse:
    return await ContestService(db, questions_db).update(contest_id, payload)


@router.delete(
    "/{contest_id}",
    response_model=ContestDeleteResponse,
    summary="Delete a scheduled contest (not allowed after it starts)",
)
async def delete_contest(
    contest_id: str,
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> ContestDeleteResponse:
    deleted = await ContestService(db, questions_db).delete(contest_id)
    return ContestDeleteResponse(deleted=deleted)


@router.get(
    "/{contest_id}/participants",
    response_model=ContestParticipantsResponse,
    summary="Leaderboard-ordered participants for a contest",
)
async def list_participants(
    contest_id: str,
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> ContestParticipantsResponse:
    return await ContestService(db, questions_db).list_participants(contest_id)
