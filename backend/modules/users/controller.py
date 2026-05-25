from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import Response

from core.dependencies import CurrentAdmin, DBDep
from modules.users.schema import UserDetailResponse, UserListResponse
from modules.users.service import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users with pagination and optional search",
)
async def list_users(
    db: DBDep,
    _: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    q: Optional[str] = Query(None, description="Search by email or username"),
) -> UserListResponse:
    return await UsersService(db).list_users(page=page, page_size=page_size, q=q)


@router.get(
    "/export.csv",
    summary="Download the full user list as CSV",
    response_class=Response,
)
async def export_csv(
    db: DBDep,
    _: CurrentAdmin,
    q: Optional[str] = Query(None, description="Filter by email or username"),
) -> Response:
    filename, body = await UsersService(db).export_csv(q=q)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/emails",
    summary="Return every email address (used by the promo composer)",
)
async def all_emails(
    db: DBDep,
    _: CurrentAdmin,
    q: Optional[str] = Query(None),
) -> dict:
    emails = await UsersService(db).all_emails(q=q)
    return {"emails": emails, "count": len(emails)}


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get a single user's record",
)
async def get_user(
    user_id: str,
    db: DBDep,
    _: CurrentAdmin,
) -> UserDetailResponse:
    return await UsersService(db).get_user(user_id)
