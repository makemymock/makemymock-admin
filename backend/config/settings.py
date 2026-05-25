from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "MakeMyMock-Admin"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    API_V1_PREFIX: str = "/api/v1"

    # ---- MongoDB ----
    # Admin reads from the same MongoDB cluster the Client backend writes to.
    MONGO_URI: str
    MONGO_DB_NAME: str = "makemymock"
    # The questions catalog ships in a separate DB (bbd_db) in the Client
    # deployment. Keep that override available without forcing it.
    MONGO_QUESTIONS_DB_NAME: str = "makemymock"

    # ---- Admin credentials ----
    # Single-tenant admin: we don't store admin users in Mongo, we read the
    # credentials from env. ADMIN_PASSWORD_HASH is a bcrypt hash — generate
    # with `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('your-password'))"`.
    # If ADMIN_PASSWORD_HASH is blank we fall back to ADMIN_PASSWORD (plain).
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str = ""
    ADMIN_PASSWORD_HASH: str = ""

    # ---- JWT ----
    JWT_SECRET_KEY: str = Field(..., min_length=16)
    JWT_REFRESH_SECRET_KEY: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- SMTP (promo emails) ----
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "MakeMyMock"
    SMTP_USE_TLS: bool = True

    # ---- Brevo HTTPS email API ----
    # Strongly recommended for production sends — cloud hosts often block
    # outbound port 587, so SMTP times out. Brevo's HTTPS path works
    # from anywhere.
    BREVO_API_KEY: str = ""

    # ---- Promo email tuning ----
    # Number of parallel sends. Keep modest to respect provider rate limits.
    PROMO_EMAIL_CONCURRENCY: int = 5
    # Max recipients accepted per single API request.
    PROMO_EMAIL_MAX_RECIPIENTS: int = 5000


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
