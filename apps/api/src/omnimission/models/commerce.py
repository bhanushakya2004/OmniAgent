"""ORM models for Guest Sessions, Carts, Orders, and Simulated Payments."""

import datetime
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GuestSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Anonymous guest shopper session persisting cart and mission interactions before login."""

    __tablename__ = "guest_sessions"

    session_token: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )


class Cart(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Shopping cart owned by an authenticated user or anonymous guest session."""

    __tablename__ = "carts"

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
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
    )

    items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.created_at",
    )


class CartItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual product line item in a cart snapshotting unit price and aisle coordinates."""

    __tablename__ = "cart_items"

    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
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
    notes: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    cart: Mapped[Cart] = relationship(
        "Cart",
        back_populates="items",
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "store_id", "product_id", name="uq_cart_store_product"),
    )


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Placed order with simulated payment and physical store pickup coordinates."""

    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cart_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="SET NULL"),
        nullable=True,
    )
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="placed",
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
    )
    pickup_time_slot: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="simulated_paid",
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="simulated_upi",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base, UUIDPrimaryKeyMixin):
    """Snapshot line item in a placed order."""

    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
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
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
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
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items",
    )


class PaymentSimulated(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simulated payment transaction record for mock guest checkout."""

    __tablename__ = "payments_simulated"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="simulated_upi",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="succeeded",
    )
    reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
