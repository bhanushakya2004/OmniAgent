"""Authentication service encapsulating registration, login, and token rotation."""

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.config import get_settings
from omnimission.core.errors import ConflictError, UnauthorizedError
from omnimission.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from omnimission.models.user import User
from omnimission.repositories.token_repo import RefreshTokenRepository
from omnimission.repositories.user_repo import UserRepository
from omnimission.schemas.auth import UserRegisterRequest


class AuthService:
    """Business logic for user authentication and session security."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        token_repo: RefreshTokenRepository | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.token_repo = token_repo or RefreshTokenRepository()
        self.settings = get_settings()

    async def register_user(
        self,
        session: AsyncSession,
        payload: UserRegisterRequest,
        user_agent: str | None = None,
    ) -> tuple[User, str, str, int]:
        """Register a new user and generate access/refresh tokens."""
        existing = await self.user_repo.get_by_email(session, payload.email)
        if existing is not None:
            raise ConflictError(
                detail=f"An account with email '{payload.email}' already exists",
                code="USER_ALREADY_EXISTS",
            )

        password_hash = hash_password(payload.password)
        user = await self.user_repo.create_user(
            session=session,
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
            role=payload.role,
            preferred_language=payload.preferred_language,
        )

        access_token, expires_in = create_access_token(user.id, user.role)
        raw_refresh_token = generate_refresh_token()
        refresh_hash = hash_token(raw_refresh_token)
        refresh_expires = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=self.settings.jwt_refresh_ttl_days
        )

        await self.token_repo.create_token(
            session=session,
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
            user_agent=user_agent,
        )

        return user, access_token, raw_refresh_token, expires_in

    async def authenticate_user(
        self,
        session: AsyncSession,
        email: str,
        password: str,
        user_agent: str | None = None,
    ) -> tuple[User, str, str, int]:
        """Authenticate user credentials and issue token pair."""
        user = await self.user_repo.get_by_email(session, email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError(
                detail="Invalid email or password",
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise UnauthorizedError(
                detail="Account is inactive",
                code="ACCOUNT_INACTIVE",
            )

        access_token, expires_in = create_access_token(user.id, user.role)
        raw_refresh_token = generate_refresh_token()
        refresh_hash = hash_token(raw_refresh_token)
        refresh_expires = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=self.settings.jwt_refresh_ttl_days
        )

        await self.token_repo.create_token(
            session=session,
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
            user_agent=user_agent,
        )

        return user, access_token, raw_refresh_token, expires_in

    async def rotate_refresh_token(
        self,
        session: AsyncSession,
        raw_refresh_token: str,
        user_agent: str | None = None,
    ) -> tuple[User, str, str, int]:
        """Rotate refresh token with reuse detection."""
        token_hash = hash_token(raw_refresh_token)
        stored_token = await self.token_repo.get_by_hash(session, token_hash)

        if stored_token is None:
            raise UnauthorizedError(
                detail="Invalid refresh token",
                code="INVALID_REFRESH_TOKEN",
            )

        now = datetime.datetime.now(datetime.UTC)

        # Token reuse detection: if a previously revoked token is presented, revoke the entire chain
        if stored_token.revoked_at is not None:
            await self.token_repo.revoke_all_user_tokens(session, stored_token.user_id)
            await session.commit()
            raise UnauthorizedError(
                detail="Refresh token reuse detected. All sessions revoked for security.",
                code="TOKEN_REUSE_DETECTED",
            )

        if stored_token.expires_at < now:
            await self.token_repo.revoke_token(session, stored_token)
            raise UnauthorizedError(
                detail="Refresh token has expired",
                code="REFRESH_TOKEN_EXPIRED",
            )

        # Revoke the current token
        await self.token_repo.revoke_token(session, stored_token)

        user = await self.user_repo.get_by_id(session, stored_token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(
                detail="User account no longer active",
                code="USER_NOT_FOUND",
            )

        # Issue new token pair
        access_token, expires_in = create_access_token(user.id, user.role)
        new_raw_token = generate_refresh_token()
        new_hash = hash_token(new_raw_token)
        new_expires = now + datetime.timedelta(days=self.settings.jwt_refresh_ttl_days)

        await self.token_repo.create_token(
            session=session,
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires,
            user_agent=user_agent,
        )

        return user, access_token, new_raw_token, expires_in

    async def revoke_refresh_token(self, session: AsyncSession, raw_refresh_token: str) -> None:
        """Revoke a refresh token on user logout."""
        token_hash = hash_token(raw_refresh_token)
        stored_token = await self.token_repo.get_by_hash(session, token_hash)
        if stored_token and stored_token.revoked_at is None:
            await self.token_repo.revoke_token(session, stored_token)
