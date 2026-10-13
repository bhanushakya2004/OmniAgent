"""Action Proposal model for Human-in-the-Loop (HITL) merchant agent actions."""

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.store import Store
    from omnimission.models.user import User


class ActionProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Human-in-the-loop action proposed by merchant Store Analyst agent."""

    __tablename__ = "action_proposals"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending_approval",
        index=True,
    )
    decision_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    decided_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    store: Mapped["Store"] = relationship("Store", lazy="selectin")
    decider: Mapped["User | None"] = relationship(
        "User", foreign_keys=[decided_by], lazy="selectin"
    )
