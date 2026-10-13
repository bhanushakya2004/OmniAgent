"""Store inventory ORM model."""

import datetime
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.product import Product
    from omnimission.models.store import Store


class StoreInventory(Base, UUIDPrimaryKeyMixin):
    """Specific stock levels and physical in-store coordinates for a SKU in a store."""

    __tablename__ = "store_inventory"

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
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    mrp: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
    )
    stock_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
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
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    store: Mapped["Store"] = relationship("Store", back_populates="inventory_items")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_records")

    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_store_inventory_store_product"),
    )
