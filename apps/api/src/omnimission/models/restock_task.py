"""Restock Task ORM model for merchant replenishment workflows."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.product import Product
    from omnimission.models.store import Store


class RestockTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Restock replenishment task drafted by shelf audits or stockout velocity."""

    __tablename__ = "restock_tasks"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aisle: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    bay: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    shelf: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    current_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    recommended_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="shelf_audit",
    )

    store: Mapped["Store"] = relationship("Store")
    product: Mapped["Product"] = relationship("Product")
