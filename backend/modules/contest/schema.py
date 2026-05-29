"""Request / response models for admin contest endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from modules.contest.constants import (
    DEFAULT_MARKS_CORRECT,
    DEFAULT_MARKS_UNATTEMPTED,
    DEFAULT_MARKS_WRONG,
    MAX_DURATION_SECONDS,
    MAX_QUESTIONS,
    MIN_DURATION_SECONDS,
    MIN_QUESTIONS,
)

Title = Annotated[str, StringConstraints(min_length=1, max_length=160, strip_whitespace=True)]
Description = Annotated[str, StringConstraints(max_length=2000, strip_whitespace=True)]
Rules = Annotated[str, StringConstraints(max_length=20000)]


class MarkingScheme(BaseModel):
    correct: float = DEFAULT_MARKS_CORRECT
    wrong: float = DEFAULT_MARKS_WRONG
    unattempted: float = DEFAULT_MARKS_UNATTEMPTED


class ContestCreateRequest(BaseModel):
    title: Title
    description: Description = ""
    rules: Rules
    start_time: datetime
    duration_seconds: int = Field(..., ge=MIN_DURATION_SECONDS, le=MAX_DURATION_SECONDS)
    question_ids: list[str] = Field(..., min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)
    marking: MarkingScheme = Field(default_factory=MarkingScheme)


class ContestUpdateRequest(BaseModel):
    """Partial update — only fields that are set will be touched. Admins
    can only update a contest that hasn't started yet (server-enforced)."""
    title: Optional[Title] = None
    description: Optional[Description] = None
    rules: Optional[Rules] = None
    start_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=MIN_DURATION_SECONDS, le=MAX_DURATION_SECONDS)
    question_ids: Optional[list[str]] = Field(None, min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)
    marking: Optional[MarkingScheme] = None


class ContestSummary(BaseModel):
    """Light-weight contest row for the list view."""
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    question_count: int
    marking: MarkingScheme
    status: Literal["scheduled", "live", "completed"]
    participant_count: int = 0
    created_at: datetime
    updated_at: datetime


class ContestSummaryListResponse(BaseModel):
    items: list[ContestSummary]


class QuestionPick(BaseModel):
    """A single question as it appears in the admin's selected list."""
    id: str
    subject: str
    chapter: str
    topic: str
    question_type: str
    difficulty: Optional[str] = None
    question_text: str = ""


class ContestDetailResponse(ContestSummary):
    """Full contest detail — includes the resolved question list so the
    admin sees what was picked without a second round-trip."""
    rules: str
    questions: list[QuestionPick] = Field(default_factory=list)


class ContestDeleteResponse(BaseModel):
    deleted: bool


class ParticipantRow(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    entered_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    correct_count: Optional[int] = None
    wrong_count: Optional[int] = None
    unattempted_count: Optional[int] = None
    time_taken_seconds: Optional[int] = None
    rank: Optional[int] = None


class ContestParticipantsResponse(BaseModel):
    contest_id: str
    total: int
    items: list[ParticipantRow]


class DefaultRulesResponse(BaseModel):
    """Returned by GET /contests/default-rules so the admin form can
    prefill the textarea without hard-coding the template on the client."""
    rules: str

    model_config = ConfigDict(extra="forbid")
