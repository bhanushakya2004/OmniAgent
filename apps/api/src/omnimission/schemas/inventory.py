"""Inventory request and response schemas."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from omnimission.schemas.product import ProductResponse


class InventoryItemResponse(BaseModel):
    """Store inventory item with product details and aisle location."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    price: Decimal
    mrp: Decimal
    currency: str
    stock_qty: int
    low_stock_threshold: int
    aisle: int
    bay: int
    shelf: int
    product: ProductResponse | None = None


class InventoryBulkUpdateItem(BaseModel):
    """Payload item for updating store stock levels or aisle locations."""

    product_id: uuid.UUID
    price: Decimal | None = None
    stock_qty: int | None = None
    aisle: int | None = Field(default=None, ge=1, le=50)
    bay: int | None = Field(default=None, ge=1, le=50)
    shelf: int | None = Field(default=None, ge=1, le=20)
