"""Schemas for Mission requests, responses, traces, and wayfinding routes."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class CreateMissionRequest(BaseModel):
    """Payload to initiate a new mission."""

    prompt: str = Field(
        ..., min_length=1, max_length=2000, description="Natural language mission prompt"
    )
    store_ids: list[uuid.UUID] = Field(
        ..., min_length=1, description="List of physical store UUIDs"
    )
    language: str = Field("en", min_length=2, max_length=10, description="ISO language code")
    input_modalities: list[str] = Field(
        default_factory=lambda: ["text"], description="Modalities used (text, voice, image)"
    )
    constraints: dict[str, Any] | None = Field(
        default=None, description="Optional upfront constraints"
    )


class UpdateMissionItemRequest(BaseModel):
    """Payload to update an item's quantity in a mission basket."""

    quantity: int = Field(..., ge=0, description="Updated quantity (0 to remove)")


class MissionTraceResponse(BaseModel):
    """Agent trace step response."""

    id: uuid.UUID
    step: str
    agent: str
    input_summary: str
    output_summary: str
    latency_ms: int
    created_at: datetime


class MissionItemResponse(BaseModel):
    """Item in a mission basket grounded in real inventory."""

    id: uuid.UUID
    mission_id: uuid.UUID
    product_id: uuid.UUID | None = None
    product_name: str | None = None
    product_brand: str | None = None
    requested_label: str
    quantity: int
    unit_price: Decimal | None = None
    subtotal: Decimal | None = None
    store_id: uuid.UUID | None = None
    store_name: str | None = None
    status: str
    reason: str | None = None
    aisle: int | None = None
    bay: int | None = None
    shelf: int | None = None


class MissionResponse(BaseModel):
    """Comprehensive mission detail."""

    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    status: str
    language: str
    input_modalities: list[str]
    constraints: dict[str, Any] | None = None
    selected_store_ids: list[uuid.UUID]
    total_cost: Decimal | None = None
    created_at: datetime
    items: list[MissionItemResponse] = Field(default_factory=list)
    traces: list[MissionTraceResponse] = Field(default_factory=list)


class MissionListItemResponse(BaseModel):
    """Compact summary of a mission for listing."""

    id: uuid.UUID
    raw_text: str
    status: str
    total_cost: Decimal | None = None
    item_count: int
    created_at: datetime


class MissionListResponse(BaseModel):
    """Paginated list of missions."""

    missions: list[MissionListItemResponse]
    total: int


class RouteWaypointResponse(BaseModel):
    """Wayfinding stop in store."""

    step_number: int
    store_id: uuid.UUID
    store_name: str
    aisle: int
    bay: int
    shelf: int
    product_name: str
    quantity: int
    action: str


class MissionRouteResponse(BaseModel):
    """Monotonic store walking route."""

    mission_id: uuid.UUID
    total_stops: int
    waypoints: list[RouteWaypointResponse]
