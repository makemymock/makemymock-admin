from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.database import get_database, get_questions_database
from config.settings import settings
from core.exceptions import Forbidden, InvalidToken
from core.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=True
)

DBDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]
QuestionsDBDep = Annotated[AsyncIOMotorDatabase, Depends(get_questions_database)]


async def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Resolve the current admin from the access token.

    There is exactly one admin identity (configured via env vars). The
    token simply has to be valid and tagged with `role=admin`. We return
    a small dict describing the admin so routes can log who did what.
    """
    payload = decode_token(token, token_type="access")
    sub = payload.get("sub")
    if not sub:
        raise InvalidToken()
    if sub.lower().strip() != settings.ADMIN_EMAIL.lower().strip():
        raise Forbidden("Token subject does not match the configured admin.")
    return {"email": sub, "role": "admin"}


CurrentAdmin = Annotated[dict, Depends(get_current_admin)]
