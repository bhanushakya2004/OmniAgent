"""Authentication request and response schemas."""

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, description="User password, minimum 8 characters")
    full_name: str = Field(min_length=2, max_length=100)
    role: Literal["user", "merchant"] = Field(default="user")
    preferred_language: str = Field(default="en", max_length=10)
    store_name: str | None = Field(
        default=None, description="Optional store name if registering as merchant"
    )


class UserLoginRequest(BaseModel):
    """Payload for credentials login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    preferred_language: str
    is_active: bool
    created_at: datetime.datetime


class TokenResponse(BaseModel):
    """Access token payload returned upon login and refresh."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Explicit refresh token payload for non-cookie HTTP clients."""

    refresh_token: str | None = None
