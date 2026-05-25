from typing import Optional

from fastapi import APIRouter, Query

from core.dependencies import CurrentAdmin, QuestionsDBDep
from modules.questions.schema import (
    CatalogResponse,
    QuestionItem,
    QuestionListResponse,
)
from modules.questions.service import QuestionsService

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Subject → chapter → topic tree with question counts",
)
async def catalog(db: QuestionsDBDep, _: CurrentAdmin) -> CatalogResponse:
    return await QuestionsService(db).catalog()


@router.get(
    "",
    response_model=QuestionListResponse,
    summary="List questions with chapter/topic/type filters",
)
async def list_questions(
    db: QuestionsDBDep,
    _: CurrentAdmin,
    subject: Optional[str] = Query(None),
    chapter: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Substring match on the question text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> QuestionListResponse:
    return await QuestionsService(db).list_questions(
        subject=subject,
        chapter=chapter,
        topic=topic,
        question_type=question_type,
        difficulty=difficulty,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{question_id}",
    response_model=QuestionItem,
    summary="Fetch a single question with answers + solution",
)
async def get_question(
    question_id: str,
    db: QuestionsDBDep,
    _: CurrentAdmin,
) -> QuestionItem:
    return await QuestionsService(db).get_question(question_id)
