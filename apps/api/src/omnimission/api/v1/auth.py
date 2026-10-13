"""Authentication API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.config import get_settings
from omnimission.core.deps import get_auth_service, get_current_user, require_merchant
from omnimission.core.errors import BadRequestError
from omnimission.db.session import get_db_session
from omnimission.models.user import User
from omnimission.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from omnimission.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Set secure, HttpOnly refresh token cookie."""
    settings = get_settings()
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        max_age=settings.jwt_refresh_ttl_days * 86400,
        httponly=True,
        samesite="lax",
        secure=False,  # Local development: False. Set to True in production HTTPS
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        httponly=True,
        samesite="lax",
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user or merchant account",
)
async def register(
    payload: UserRegisterRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Register account, issue JWT access token, and establish refresh session."""
    user, access_token, raw_refresh, expires_in = await auth_service.register_user(
        session=session,
        payload=payload,
        user_agent=user_agent,
    )
    await session.commit()
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with email and password",
)
async def login(
    payload: UserLoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Log in user with email and password."""
    user, access_token, raw_refresh, expires_in = await auth_service.authenticate_user(
        session=session,
        email=payload.email,
        password=payload.password,
        user_agent=user_agent,
    )
    await session.commit()
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    payload: RefreshTokenRequest | None = None,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Rotate refresh token. Accepts token in HttpOnly cookie or request body."""
    raw_token = refresh_token_cookie or (payload.refresh_token if payload else None)
    if not raw_token:
        raise BadRequestError(
            detail="No refresh token provided in cookie or payload",
            code="MISSING_REFRESH_TOKEN",
        )

    user, access_token, new_raw_refresh, expires_in = await auth_service.rotate_refresh_token(
        session=session,
        raw_refresh_token=raw_token,
        user_agent=user_agent,
    )
    await session.commit()
    _set_refresh_cookie(response, new_raw_refresh)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out and revoke refresh token",
)
async def logout(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    payload: RefreshTokenRequest | None = None,
) -> None:
    """Revoke refresh token and clear cookie."""
    raw_token = refresh_token_cookie or (payload.refresh_token if payload else None)
    if raw_token:
        await auth_service.revoke_refresh_token(session, raw_token)
        await session.commit()
    _clear_refresh_cookie(response)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return profile details for the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/merchant-check",
    summary="Verify merchant role authorization",
)
async def merchant_check(
    current_merchant: Annotated[User, Depends(require_merchant)],
) -> dict[str, str]:
    """Test probe verifying merchant role guard."""
    return {"status": "ok", "merchant_id": str(current_merchant.id)}
