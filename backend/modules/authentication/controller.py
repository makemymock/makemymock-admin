from fastapi import APIRouter, status

from core.dependencies import CurrentAdmin
from modules.authentication.schema import (
    AdminPublic,
    AuthSuccessResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenPair,
)
from modules.authentication.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate the admin with email + password",
)
async def login(payload: LoginRequest) -> AuthSuccessResponse:
    return await AuthService().login(payload)


@router.post(
    "/refresh-token",
    response_model=TokenPair,
    summary="Exchange a refresh token for a new token pair",
)
async def refresh_token(payload: RefreshTokenRequest) -> TokenPair:
    return await AuthService().refresh(payload.refresh_token)


@router.get(
    "/me",
    response_model=AdminPublic,
    summary="Get the currently authenticated admin",
)
async def me(current_admin: CurrentAdmin) -> AdminPublic:
    return AdminPublic(email=current_admin["email"], role=current_admin["role"])
