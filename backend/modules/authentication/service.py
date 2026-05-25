import logging

from config.settings import settings
from core.exceptions import InvalidCredentials, InvalidToken
from core.jwt_handler import create_access_token, create_refresh_token, decode_token
from core.security import verify_password
from modules.authentication.schema import (
    AdminPublic,
    AuthSuccessResponse,
    LoginRequest,
    TokenPair,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Single-tenant admin auth.

    The admin identity is configured purely via env vars — no user
    collection, no signup. Tokens carry `role=admin` so the rest of the
    app can guard against accidental Client-token reuse.
    """

    @staticmethod
    def _issue_tokens(email: str) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(email),
            refresh_token=create_refresh_token(email),
        )

    @staticmethod
    def _verify_credentials(email: str, password: str) -> bool:
        if email.lower().strip() != settings.ADMIN_EMAIL.lower().strip():
            return False
        if settings.ADMIN_PASSWORD_HASH:
            return verify_password(password, settings.ADMIN_PASSWORD_HASH)
        # Plain-password fallback for first-run / local dev. Constant-time
        # comparison avoids leaking length through timing.
        import hmac
        return hmac.compare_digest(password, settings.ADMIN_PASSWORD or "")

    async def login(self, payload: LoginRequest) -> AuthSuccessResponse:
        if not self._verify_credentials(payload.email, payload.password):
            raise InvalidCredentials()
        return AuthSuccessResponse(
            user=AdminPublic(email=payload.email, role="admin"),
            tokens=self._issue_tokens(payload.email),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token, token_type="refresh")
        email = payload["sub"]
        if email.lower().strip() != settings.ADMIN_EMAIL.lower().strip():
            raise InvalidToken("Token subject is not the configured admin.")
        return self._issue_tokens(email)
