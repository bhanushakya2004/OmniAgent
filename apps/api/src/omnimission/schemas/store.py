"""Store request and response schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StoreBase(BaseModel):
    """Common store fields."""

    name: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=5, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    lat: float = Field(ge=-90.0, le=90.0)
    lng: float = Field(ge=-180.0, le=180.0)
    phone: str | None = None
    opening_hours: dict[str, Any] | None = None
    is_active: bool = True


class StoreResponse(StoreBase):
    """Store entity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID


class StoreNearbyResponse(StoreResponse):
    """Nearby store with computed distance."""

    distance_km: float = Field(description="Distance from requested coordinates in kilometers")
    open_now: bool = Field(default=True, description="Whether store is currently open")
    categories: list[str] = Field(
        default_factory=list, description="Primary departments/categories present"
    )


class StoreDetailResponse(StoreResponse):
    """Detailed store view including aisles and SKU summary."""

    total_skus: int = 0
    available_aisles: list[int] = Field(default_factory=list)
