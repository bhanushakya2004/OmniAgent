"""Product catalog schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    """Product details schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    brand: str
    description: str
    category: str
    subcategory: str | None = None
    size_label: str | None = None
    is_travel_size: bool = False
    unit: str | None = None
    dietary_tags: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] | None = None
    image_url: str | None = None
