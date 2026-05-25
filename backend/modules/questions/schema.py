from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ----- Catalog tree -----

class TopicNode(BaseModel):
    name: str
    question_count: int


class ChapterNode(BaseModel):
    name: str
    question_count: int
    topics: list[TopicNode]


class SubjectNode(BaseModel):
    name: str
    question_count: int
    chapters: list[ChapterNode]


class CatalogResponse(BaseModel):
    subjects: list[SubjectNode]
    total_questions: int


# ----- Question payloads -----
#
# All of the loose collections below are typed as `list[dict[str, Any]]`
# rather than dedicated submodels because the upstream `questions`
# collection ships heterogeneous shapes (a half-dozen historical ingest
# sources). The service normalises everything to a stable dict shape
# before it hits the schema; bullet-proofing the schema with strict
# submodels keeps biting us when an edge case appears in production.

class QuestionItem(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    subject: str
    chapter: str
    topic: str
    question_type: str
    difficulty: Optional[str] = None
    question_text: str = ""
    question_image: Optional[str] = None

    # Single/multi-correct options. Each item: {key, text, image?, is_correct}
    options: list[dict[str, Any]] = Field(default_factory=list)
    correct_option_keys: list[str] = Field(default_factory=list)

    # Integer answer
    correct_integer: Optional[Any] = None

    # Matching: left/right columns are lists of {key, text, image?}; the
    # correct mapping is a dict like {"L1": "R2", "L2": "R1"}.
    matching_left: list[dict[str, Any]] = Field(default_factory=list)
    matching_right: list[dict[str, Any]] = Field(default_factory=list)
    matching_correct: dict[str, str] = Field(default_factory=dict)

    # Passage
    passage_text: Optional[str] = None
    passage_image: Optional[str] = None
    sub_questions: list["QuestionItem"] = Field(default_factory=list)

    # Solution
    solution_text: Optional[str] = None
    solution_image: Optional[str] = None


QuestionItem.model_rebuild()


class QuestionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QuestionItem]
