from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    email: EmailStr
    username: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Profile fields (flattened when present)
    full_name: Optional[str] = None
    class_grade: Optional[str] = None
    target_exam: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    school_name: Optional[str] = None
    preferred_language: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserListItem]


class UserDetailResponse(UserListItem):
    """Same shape as the list item — exposed so the detail page has a
    contract independent of the listing one."""
    total_mock_tests: int = 0
    completed_mock_tests: int = 0
    total_battles: int = 0
