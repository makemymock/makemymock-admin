from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

Password = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: Password


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class AdminPublic(BaseModel):
    email: EmailStr
    role: str = "admin"


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthSuccessResponse(BaseModel):
    user: AdminPublic
    tokens: TokenPair


class MessageResponse(BaseModel):
    message: str
