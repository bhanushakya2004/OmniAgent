"""Store ORM model."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.inventory import StoreInventory
    from omnimission.models.user import User


class Store(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Physical retail store location managed by a merchant."""

    __tablename__ = "stores"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    lat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    lng: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    opening_hours: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    merchant: Mapped["User"] = relationship("User")
    inventory_items: Mapped[list["StoreInventory"]] = relationship(
        "StoreInventory",
        back_populates="store",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_stores_lat_lng", "lat", "lng"),)
