"""Pydantic schemas for multi-agent I/O, grounding, and streaming timeline events."""

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MissionIntent(BaseModel):
    """Structured mission goal and constraints extracted from free text, voice, or image."""

    goal_type: str = Field(
        description="Goal category: recipe, party, travel_kit, replacement, or general"
    )
    description: str = Field(
        description="Clean, concise summary of what the shopper is trying to accomplish"
    )
    servings_or_people: int | None = Field(
        default=None, description="Number of people or servings if specified"
    )
    duration_days: int | None = Field(
        default=None, description="Trip or usage duration in days if specified"
    )
    budget_inr: float | None = Field(
        default=None, description="Target budget limit in INR if specified"
    )
    dietary_tags: list[str] = Field(
        default_factory=list,
        description="Strict dietary/allergy constraints, e.g. eggless, vegetarian, vegan, gluten_free, high_protein",
    )
    is_travel_size: bool | None = Field(
        default=None,
        description="Whether toiletries/items must be compact travel-size (<= 100ml)",
    )
    detected_language: str = Field(
        default="en", description="Detected language code, e.g. en, hi, kn, ta"
    )
    excluded_items: list[str] = Field(
        default_factory=list,
        description="Items the user already has in pantry or explicitly requested to exclude",
    )


class NeededItem(BaseModel):
    """An ingredient or supply item needed to fulfill the mission goal."""

    label: str = Field(
        description="Generic or specific name of item needed (e.g. 'All-Purpose Flour' or 'Cocoa Powder')"
    )
    category: str = Field(
        description="Department: Baking, Dairy, Personal Care, Party, Snacks, Staples"
    )
    quantity: int = Field(default=1, ge=1, description="Quantity or pack count needed")
    unit: str | None = Field(default=None, description="Unit measurement (g, ml, pcs, pack)")
    importance: str = Field(default="essential", description="'essential' or 'optional'")
    dietary_notes: str | None = Field(
        default=None, description="Notes on dietary constraints for this specific item"
    )


class NeededItemList(BaseModel):
    """Expanded list of needed items required to fulfill the mission."""

    items: list[NeededItem] = Field(default_factory=list)
    rationale: str = Field(description="Explanation of why these items and quantities were planned")


class SubstitutionProposal(BaseModel):
    """Proposal for substituting an unavailable or over-budget item."""

    original_needed: str
    substitute_product_id: uuid.UUID
    substitute_name: str
    unit_price: Decimal
    reason: str
    trade_off: str


class OptimizedBasketItem(BaseModel):
    """Final grounded item in the shopper's basket with real store and aisle locations."""

    product_id: uuid.UUID
    requested_label: str
    name: str
    brand: str
    quantity: int = 1
    unit_price: Decimal
    subtotal: Decimal
    store_id: uuid.UUID
    store_name: str
    aisle: int
    bay: int
    shelf: int
    status: str = Field(default="matched", description="'matched' or 'substituted'")
    substitution_reason: str | None = None
    match_explanation: str = Field(
        default="Matched in inventory", description="Why this item was selected"
    )


class WayfindingStop(BaseModel):
    """A physical stop along the customer's optimal aisle walking route."""

    stop_order: int
    store_id: uuid.UUID
    store_name: str
    aisle: int
    bay: int
    shelf: int
    items: list[str]
    instruction: str


class MissionResult(BaseModel):
    """Complete mission output returned to the shopper."""

    mission_id: uuid.UUID
    intent: MissionIntent
    items: list[OptimizedBasketItem]
    total_cost: Decimal
    budget_fit: bool
    budget_difference: Decimal | None = None
    stores_used: list[dict[str, Any]]
    route: list[WayfindingStop]
    summary: str


class TimelineEvent(BaseModel):
    """Real-time Server-Sent Event (SSE) emitted during multi-agent execution."""

    step: str
    status: str = "in_progress"  # in_progress, completed, warning, failed
    agent: str
    title: str
    description: str
    latency_ms: int = 0
    data: dict[str, Any] | None = None
