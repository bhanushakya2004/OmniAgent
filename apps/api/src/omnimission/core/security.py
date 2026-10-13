"""Argon2id password hashing and JWT token management."""

import datetime
import hashlib
import secrets
import uuid
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from omnimission.core.config import get_settings
from omnimission.core.errors import UnauthorizedError

_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, int]:
    """Create a signed JWT access token. Returns (token, expires_in_seconds)."""
    settings = get_settings()
    expires_delta = datetime.timedelta(minutes=settings.jwt_access_ttl_min)
    now = datetime.datetime.now(datetime.UTC)
    exp = now + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "role", "exp", "iat"]},
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise UnauthorizedError(detail="Token has expired", code="TOKEN_EXPIRED") from err
    except jwt.InvalidTokenError as err:
        raise UnauthorizedError(detail="Invalid token", code="INVALID_TOKEN") from err


def generate_refresh_token() -> str:
    """Generate high-entropy random refresh token string."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of refresh token for safe storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
