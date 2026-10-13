"""Pydantic schemas for transparent user memory and personalization management."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """Payload to create or update a transparent memory preference."""

    key: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Preference key (e.g. diet, household_size, allergens)",
    )
    value: Any = Field(..., description="Preference value (string, integer, list, or object)")
    memory_type: str = Field(
        default="preference", max_length=50, description="Category of preference"
    )


class UserMemoryItem(BaseModel):
    """Transparent representation of a saved user memory."""

    id: uuid.UUID
    key: str
    value: dict[str, Any]
    memory_type: str
    source: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MemoryListResponse(BaseModel):
    """Transparent list of all active user memories alongside the compiled profile."""

    memories: list[UserMemoryItem]
    compiled_profile: dict[str, Any]
