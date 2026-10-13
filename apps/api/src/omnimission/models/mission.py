"""Mission, MissionItem, and MissionRun (Agent Trace) ORM models."""

import datetime
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.product import Product
    from omnimission.models.store import Store
    from omnimission.models.user import User


class Mission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Shopping mission initiated by a user across selected physical stores."""

    __tablename__ = "missions"

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
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    raw_text: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )
    input_modalities: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: ["text"],
    )
    constraints: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    selected_store_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
    )
    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")
    items: Mapped[list["MissionItem"]] = relationship(
        "MissionItem",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionItem.aisle_snapshot",
    )
    traces: Mapped[list["MissionRun"]] = relationship(
        "MissionRun",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionRun.created_at",
    )
    events: Mapped[list["MissionEvent"]] = relationship(
        "MissionEvent",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionEvent.sequence_id",
    )


class MissionItem(Base, UUIDPrimaryKeyMixin):
    """Specific item in a mission basket grounded in physical store inventory."""

    __tablename__ = "mission_items"

    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    requested_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="matched",
    )
    substitute_for_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mission_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    aisle_snapshot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    bay_snapshot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    shelf_snapshot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    mission: Mapped["Mission"] = relationship("Mission", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product")
    store: Mapped["Store | None"] = relationship("Store")


class MissionRun(Base, UUIDPrimaryKeyMixin):
    """Agent execution trace step powering the reasoning timeline."""

    __tablename__ = "mission_runs"

    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    agent: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    input_summary: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    output_summary: Mapped[str] = mapped_column(
        String(4000),
        nullable=False,
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    mission: Mapped["Mission"] = relationship("Mission", back_populates="traces")


class MissionEvent(Base, UUIDPrimaryKeyMixin):
    """Persisted Server-Sent Event for resumable streaming replay."""

    __tablename__ = "mission_events"

    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    mission: Mapped["Mission"] = relationship("Mission", back_populates="events")

    __table_args__ = (UniqueConstraint("mission_id", "sequence_id", name="uq_mission_sequence"),)
