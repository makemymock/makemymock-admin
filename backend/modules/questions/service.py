"""Question browsing for the admin console.

The `questions` collection has a single canonical shape (the Client
backend's mock_test module is the source of truth). It uses camelCase
for everything and flat option fields rather than an array:

    {
      _id, subject, chapter, topic,
      questionType: "single_correct" | "multi_correct" | "integer"
                    | "matching" | "passage",
      difficulty: "easy" | "medium" | "hard",
      questionText, questionImg,
      optionA, optionB, optionC, optionD,
      correctOptions: ["A", "C"],
      integerAnswer: 42,
      matchingData: { leftColumn, rightColumn, correctMapping },
      passageData: { passageText, passageImg, subQuestions: [...] },
      solution, solutionImg,
    }

This service translates that into the admin's stable response shape so
the frontend has one well-defined contract.
"""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import QuestionNotFound
from modules.questions.repository import QuestionsRepository
from modules.questions.schema import (
    CatalogResponse,
    ChapterNode,
    QuestionItem,
    QuestionListResponse,
    SubjectNode,
    TopicNode,
)


def _as_str_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values.strip().upper()] if values.strip() else []
    if isinstance(values, (list, tuple, set)):
        return [str(v).strip().upper() for v in values if str(v).strip()]
    return [str(values).strip().upper()]


def _options_from_doc(doc: dict, correct_keys: list[str]) -> list[dict[str, Any]]:
    """Read the flat optionA/B/C/D fields into a list with `is_correct` annotated."""
    out: list[dict[str, Any]] = []
    correct_set = {k.upper() for k in correct_keys}
    for key in ("A", "B", "C", "D"):
        text = doc.get(f"option{key}")
        if text is None or str(text).strip() == "":
            continue
        out.append(
            {
                "key": key,
                "text": str(text),
                "image": doc.get(f"option{key}Img") or None,
                "is_correct": key in correct_set,
            }
        )
    return out


def _matching_cols(doc: dict) -> tuple[list[dict], list[dict], dict[str, str]]:
    md = doc.get("matchingData") or {}
    left_raw = md.get("leftColumn") or []
    right_raw = md.get("rightColumn") or []
    correct_raw = md.get("correctMapping") or {}

    def _normalise(items: list, default_prefix: str) -> list[dict]:
        out: list[dict] = []
        for i, item in enumerate(items):
            if isinstance(item, dict):
                key = str(item.get("key") or item.get("id") or f"{default_prefix}{i+1}")
                text = str(item.get("text") or item.get("value") or "")
                image = item.get("image") or item.get("img")
                out.append({"key": key, "text": text, "image": image})
            else:
                out.append({"key": f"{default_prefix}{i+1}", "text": str(item), "image": None})
        return out

    # correctMapping can ship as either a dict or a list of pairs. Coerce
    # to a flat str→str dict so the frontend never has to branch.
    if isinstance(correct_raw, list):
        try:
            correct_map = {str(k): str(v) for k, v in correct_raw}
        except Exception:
            correct_map = {}
    elif isinstance(correct_raw, dict):
        correct_map = {str(k): str(v) for k, v in correct_raw.items()}
    else:
        correct_map = {}

    return _normalise(left_raw, "L"), _normalise(right_raw, "R"), correct_map


def _normalise_doc(doc: dict) -> dict[str, Any]:
    qtype = (doc.get("questionType") or doc.get("question_type") or "single_correct").lower()
    difficulty = doc.get("difficulty") or doc.get("level")

    correct_option_keys = _as_str_list(
        doc.get("correctOptions") or doc.get("correctOption")
    )
    options = _options_from_doc(doc, correct_option_keys)

    matching_left, matching_right, matching_correct = ([], [], {})
    if qtype == "matching":
        matching_left, matching_right, matching_correct = _matching_cols(doc)

    sub_questions: list[QuestionItem] = []
    passage_text = None
    passage_image = None
    if qtype == "passage":
        passage = doc.get("passageData") or {}
        passage_text = passage.get("passageText") or doc.get("passageText")
        passage_image = passage.get("passageImg") or doc.get("passageImg")
        for i, sub in enumerate(passage.get("subQuestions") or []):
            sub_doc = {
                **sub,
                "subject": doc.get("subject"),
                "chapter": doc.get("chapter"),
                "topic": doc.get("topic"),
                "questionType": "single_correct",
                "difficulty": sub.get("difficulty") or difficulty,
                # Sub-questions don't have their own ObjectId; synthesize a
                # stable display id from the parent + position.
                "_id": sub.get("_id") or f"{doc.get('_id')}::{i}",
            }
            sub_questions.append(QuestionItem(**_normalise_doc(sub_doc)))

    return {
        "id": str(doc.get("_id", "")),
        "subject": str(doc.get("subject") or "Uncategorized"),
        "chapter": str(doc.get("chapter") or "Uncategorized"),
        "topic": str(doc.get("topic") or "Uncategorized"),
        "question_type": qtype,
        "difficulty": str(difficulty).lower() if difficulty else None,
        "question_text": str(doc.get("questionText") or doc.get("question_text") or ""),
        "question_image": doc.get("questionImg") or doc.get("question_image") or None,
        "options": options,
        "correct_option_keys": correct_option_keys,
        "correct_integer": doc.get("integerAnswer") if doc.get("integerAnswer") is not None
        else doc.get("integer_answer"),
        "matching_left": matching_left,
        "matching_right": matching_right,
        "matching_correct": matching_correct,
        "passage_text": passage_text,
        "passage_image": passage_image,
        "sub_questions": sub_questions,
        "solution_text": doc.get("solution") or doc.get("solutionText") or doc.get("solution_text"),
        "solution_image": doc.get("solutionImg") or doc.get("solution_image"),
    }


class QuestionsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = QuestionsRepository(db)

    async def catalog(self) -> CatalogResponse:
        rows = await self.repo.aggregate_catalog()
        subjects: dict[str, dict[str, list[TopicNode]]] = {}
        subject_counts: dict[str, int] = {}
        chapter_counts: dict[tuple[str, str], int] = {}
        total = 0

        for r in rows:
            key = r["_id"]
            s, c, t = key["subject"], key["chapter"], key["topic"]
            count = int(r["question_count"])
            subjects.setdefault(s, {}).setdefault(c, []).append(
                TopicNode(name=t, question_count=count)
            )
            subject_counts[s] = subject_counts.get(s, 0) + count
            chapter_counts[(s, c)] = chapter_counts.get((s, c), 0) + count
            total += count

        out: list[SubjectNode] = []
        for s_name, chapters in subjects.items():
            chapter_nodes = [
                ChapterNode(
                    name=c_name,
                    question_count=chapter_counts[(s_name, c_name)],
                    topics=topics,
                )
                for c_name, topics in chapters.items()
            ]
            out.append(
                SubjectNode(
                    name=s_name,
                    question_count=subject_counts[s_name],
                    chapters=chapter_nodes,
                )
            )

        return CatalogResponse(subjects=out, total_questions=total)

    async def list_questions(
        self,
        *,
        subject: Optional[str],
        chapter: Optional[str],
        topic: Optional[str],
        question_type: Optional[str],
        difficulty: Optional[str],
        q: Optional[str],
        page: int,
        page_size: int,
    ) -> QuestionListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        total, docs = await self.repo.list_filtered(
            subject=subject,
            chapter=chapter,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            q=q,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        items = [QuestionItem(**_normalise_doc(d)) for d in docs]
        return QuestionListResponse(total=total, page=page, page_size=page_size, items=items)

    async def get_question(self, question_id: str) -> QuestionItem:
        doc = await self.repo.get_by_id(question_id)
        if doc is None:
            raise QuestionNotFound()
        return QuestionItem(**_normalise_doc(doc))
