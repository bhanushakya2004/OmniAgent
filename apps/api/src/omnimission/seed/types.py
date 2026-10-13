"""Type definitions for deterministic seed datasets."""

import uuid
from typing import Any, TypedDict


class DemoUserDict(TypedDict):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    password: str
    preferred_language: str


class DemoStoreDict(TypedDict):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    address: str
    city: str
    lat: float
    lng: float
    phone: str | None
    opening_hours: dict[str, Any]
    is_active: bool


class CatalogItemDict(TypedDict):
    slug: str
    name: str
    brand: str
    description: str
    category: str
    subcategory: str | None
    size_label: str | None
    unit: str | None
    is_travel_size: bool
    dietary_tags: list[str]
    price: float
    mrp: float
    aisle: int
    bay: int
    shelf: int
