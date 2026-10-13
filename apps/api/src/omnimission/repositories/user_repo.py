"""User repository for encapsulated database access."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.user import User


class UserRepository:
    """Data access repository for User entities."""

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = "user",
        preferred_language: str = "en",
    ) -> User:
        """Create and persist a new User entity."""
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            role=role,
            preferred_language=preferred_language,
        )
        session.add(user)
        await session.flush()
        return user

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Find a user by case-insensitive email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, session: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Find a user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
