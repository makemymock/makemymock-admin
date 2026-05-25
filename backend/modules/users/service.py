import csv
import io
import logging
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import UserNotFound
from modules.users.repository import UsersRepository
from modules.users.schema import UserDetailResponse, UserListItem, UserListResponse

logger = logging.getLogger(__name__)


# Order matters — this is the CSV column order downstream tools (Excel,
# Sheets) will see. Keep it stable so admins can build pivots on top.
CSV_COLUMNS = [
    "id",
    "email",
    "username",
    "full_name",
    "phone_number",
    "gender",
    "date_of_birth",
    "class_grade",
    "target_exam",
    "state",
    "city",
    "school_name",
    "preferred_language",
    "is_verified",
    "is_active",
    "created_at",
    "updated_at",
]


class UsersService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = UsersRepository(db)

    @staticmethod
    def _flatten(user: dict, profile: Optional[dict]) -> dict:
        return {
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "username": user.get("username", ""),
            "is_verified": user.get("is_verified", False),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "full_name": (profile or {}).get("full_name"),
            "class_grade": (profile or {}).get("class_grade"),
            "target_exam": (profile or {}).get("target_exam"),
            "state": (profile or {}).get("state"),
            "city": (profile or {}).get("city"),
            "school_name": (profile or {}).get("school_name"),
            "preferred_language": (profile or {}).get("preferred_language"),
            "phone_number": (profile or {}).get("phone_number"),
            "gender": (profile or {}).get("gender"),
            "date_of_birth": (
                str((profile or {}).get("date_of_birth"))
                if (profile or {}).get("date_of_birth")
                else None
            ),
        }

    async def list_users(
        self, page: int, page_size: int, q: Optional[str]
    ) -> UserListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        query = await self.repo.search_query(q)
        total = await self.repo.count(query)
        rows = await self.repo.list_paginated(
            skip=(page - 1) * page_size, limit=page_size, query=query
        )
        profiles = await self.repo.get_profiles_for_users([r["_id"] for r in rows])
        items = [
            UserListItem(**self._flatten(r, profiles.get(str(r["_id"]))))
            for r in rows
        ]
        return UserListResponse(total=total, page=page, page_size=page_size, items=items)

    async def get_user(self, user_id: str) -> UserDetailResponse:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        profile = await self.repo.get_profile_by_user_id(user["_id"])
        total_sessions, completed_sessions = await self.repo.count_user_sessions(user["_id"])
        total_battles = await self.repo.count_user_battles(user["_id"])
        flat = self._flatten(user, profile)
        return UserDetailResponse(
            **flat,
            total_mock_tests=total_sessions,
            completed_mock_tests=completed_sessions,
            total_battles=total_battles,
        )

    async def export_csv(self, q: Optional[str]) -> tuple[str, str]:
        """Build a CSV blob ready to ship as a download.

        Returns (filename, csv_text). The controller wraps it in a Response
        with the right Content-Disposition header so it triggers a browser
        download on a single click.
        """
        query = await self.repo.search_query(q)
        users = await self.repo.all_for_export(query)
        profiles = await self.repo.get_profiles_for_users([u["_id"] for u in users])

        buf = io.StringIO(newline="")
        writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for u in users:
            row = self._flatten(u, profiles.get(str(u["_id"])))
            # Stringify datetimes for Excel-friendly output.
            for key in ("created_at", "updated_at"):
                if row.get(key) is not None:
                    row[key] = row[key].isoformat()
            writer.writerow(row)

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"makemymock_users_{ts}.csv"
        return filename, buf.getvalue()

    async def all_emails(self, q: Optional[str] = None) -> list[str]:
        """Return every user's email — used by the promo email composer's
        'select all' helper."""
        query = await self.repo.search_query(q)
        users = await self.repo.all_for_export(query)
        return [u["email"] for u in users if u.get("email")]
