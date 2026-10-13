"""User and guest transparent memory ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.commerce import GuestSession
    from omnimission.models.user import User


class UserMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Transparent shopper memory record capturing dietary, household, and brand preferences."""

    __tablename__ = "user_memories"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    guest_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guest_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="preference",
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    value: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user_explicit",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    user: Mapped[User | None] = relationship("User")
    guest_session: Mapped[GuestSession | None] = relationship("GuestSession")
