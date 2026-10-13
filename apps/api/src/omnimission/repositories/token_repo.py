"""RefreshToken repository managing token lifecycle."""

import datetime
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Data access repository for RefreshToken entities."""

    async def create_token(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime.datetime,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """Persist a new refresh token record."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
        )
        session.add(token)
        await session.flush()
        return token

    async def get_by_hash(self, session: AsyncSession, token_hash: str) -> RefreshToken | None:
        """Find a refresh token record by SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, session: AsyncSession, token: RefreshToken) -> None:
        """Mark a specific refresh token as revoked."""
        token.revoked_at = datetime.datetime.now(datetime.UTC)
        await session.flush()

    async def revoke_all_user_tokens(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user upon detected token reuse."""
        now = datetime.datetime.now(datetime.UTC)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.execute(stmt)
        await session.flush()
