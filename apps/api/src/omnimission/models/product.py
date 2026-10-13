"""Product catalog ORM model."""

from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from omnimission.models.inventory import StoreInventory


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Product catalog item with rich dietary metadata and vector embeddings."""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    brand: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    subcategory: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    size_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_travel_size: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    dietary_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    tsv: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        nullable=True,
    )

    inventory_records: Mapped[list["StoreInventory"]] = relationship(
        "StoreInventory",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_products_dietary_tags", "dietary_tags", postgresql_using="gin"),
        Index("ix_products_tsv", "tsv", postgresql_using="gin"),
    )
