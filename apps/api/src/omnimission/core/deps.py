"""FastAPI dependencies for dependency injection, authentication, and RBAC."""

import datetime
import uuid
from collections.abc import Callable
from typing import Literal

from fastapi import Cookie, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.errors import ForbiddenError, UnauthorizedError
from omnimission.core.principal import Principal
from omnimission.core.security import decode_access_token
from omnimission.db.session import get_db_session
from omnimission.models.user import User
from omnimission.repositories.user_repo import UserRepository
from omnimission.services.auth_service import AuthService

security_bearer = HTTPBearer(auto_error=False)


def get_user_repo() -> UserRepository:
    """Dependency provider for UserRepository."""
    return UserRepository()


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(user_repo=user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    token: str | None = Query(None, description="Optional access token for SSE EventSource"),
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Authenticate request using bearer access token or query parameter and return current User."""
    raw_token = credentials.credentials if credentials else token
    if not raw_token:
        raise UnauthorizedError(detail="Missing authorization token", code="MISSING_TOKEN")

    payload = decode_access_token(raw_token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(detail="Invalid token subject", code="INVALID_TOKEN_SUB")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as err:
        raise UnauthorizedError(
            detail="Malformed token user identifier", code="MALFORMED_TOKEN"
        ) from err

    user = await user_repo.get_by_id(session, user_id)
    if user is None:
        raise UnauthorizedError(detail="User no longer exists", code="USER_NOT_FOUND")

    if not user.is_active:
        raise UnauthorizedError(detail="User account is deactivated", code="ACCOUNT_INACTIVE")

    return user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """Dependency factory checking that the authenticated user possesses one of the allowed roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                detail=f"Operation requires one of roles: {list(allowed_roles)}. Current role: '{current_user.role}'",
                code="ROLE_NOT_AUTHORIZED",
            )
        return current_user

    return role_checker


# Role guards
require_user = require_role("user", "merchant")
require_merchant = require_role("merchant")


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    token: str | None = Query(None, description="Optional access token"),
    x_guest_session: str | None = Header(None, alias="X-Guest-Session-ID"),
    omni_guest_session: str | None = Cookie(None, alias="omni_guest_session"),
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Principal:
    """Resolve current caller as authenticated User/Merchant or anonymous Guest."""
    raw_token = credentials.credentials if credentials else token
    if raw_token:
        try:
            payload = decode_access_token(raw_token)
            user_id_str = payload.get("sub")
            if user_id_str:
                user_id = uuid.UUID(user_id_str)
                user = await user_repo.get_by_id(session, user_id)
                if user and user.is_active:
                    p_type: Literal["guest", "user", "merchant"] = (
                        "merchant" if user.role == "merchant" else "user"
                    )
                    return Principal(
                        principal_type=p_type,
                        user_id=user.id,
                        guest_session_id=None,
                        session_token=None,
                        email=user.email,
                        role=user.role,
                        user=user,
                    )
        except Exception:
            pass  # Fall back to guest session if token is expired/invalid

    # Resolve or create GuestSession
    session_token = x_guest_session or omni_guest_session or f"guest_{uuid.uuid4().hex}"

    from sqlalchemy import select

    from omnimission.models.commerce import GuestSession

    stmt = select(GuestSession).where(GuestSession.session_token == session_token)
    res = await session.execute(stmt)
    g_session = res.scalar_one_or_none()
    if g_session is None:
        g_session = GuestSession(
            session_token=session_token,
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30),
            properties={},
        )
        session.add(g_session)
        await session.commit()
        await session.refresh(g_session)

    return Principal(
        principal_type="guest",
        user_id=None,
        guest_session_id=g_session.id,
        session_token=session_token,
        email=None,
        role=None,
        user=None,
    )
