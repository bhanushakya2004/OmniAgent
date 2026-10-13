"""Schemas for merchant stores, inventory management, shelf audits, and restock tasks."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MerchantStoreResponse(BaseModel):
    """Store owned by merchant."""

    id: uuid.UUID
    name: str
    address: str
    city: str
    lat: float
    lng: float
    is_active: bool
    total_skus: int = 0


class MerchantInventoryItemResponse(BaseModel):
    """Store inventory SKU details."""

    id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_brand: str
    category: str
    sku: str
    price: Decimal
    mrp: Decimal
    stock_qty: int
    low_stock_threshold: int
    aisle: int
    bay: int
    shelf: int
    is_active: bool
    stock_status: str = Field(description="'healthy', 'low_stock', 'out_of_stock'")


class UpdateInventoryRequest(BaseModel):
    """Payload to update stock count or shelf placement."""

    stock_qty: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, gt=0)
    aisle: int | None = Field(default=None, ge=1)
    bay: int | None = Field(default=None, ge=1)
    shelf: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class CsvImportReport(BaseModel):
    """Summary of batch inventory CSV upload."""

    total_rows: int
    imported_count: int
    updated_count: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


class RestockTaskResponse(BaseModel):
    """Restock task representation."""

    id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    aisle: int
    bay: int
    shelf: int
    current_qty: int
    recommended_qty: int
    reason: str
    status: str
    source: str
    created_at: datetime


class UpdateRestockTaskRequest(BaseModel):
    """Payload to update task status."""

    status: str = Field(..., pattern="^(pending|approved|completed|dismissed)$")


class ShelfAuditRequest(BaseModel):
    """Payload to trigger visual shelf audit."""

    file_url: str = Field(description="URL of uploaded shelf photo")
    store_id: uuid.UUID
    aisle: int = Field(default=1, ge=1)
