"""Pydantic schemas for Cart, CartItem, Checkout, and Order responses."""

import uuid

from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    """Payload to add an item to the shopping cart."""

    store_id: uuid.UUID = Field(..., description="Target store UUID")
    product_id: uuid.UUID = Field(..., description="Product catalog item UUID")
    qty: int = Field(1, ge=1, le=99, description="Quantity to add")
    notes: str | None = Field(None, max_length=255, description="Dietary or substitute notes")


class UpdateCartItemRequest(BaseModel):
    """Payload to update cart item quantity."""

    qty: int = Field(..., ge=0, le=99, description="New quantity (0 deletes item)")


class MergeCartRequest(BaseModel):
    """Payload to merge an anonymous guest cart into user account."""

    guest_session_id: uuid.UUID = Field(..., description="Guest session UUID to merge")


class CartItemResponse(BaseModel):
    """Line item in shopping cart response."""

    id: str
    product_id: str
    store_id: str
    sku: str
    product_name: str
    qty: int
    unit_price: float
    subtotal: float
    aisle: int
    bay: int
    shelf: int
    notes: str | None = None


class CartResponse(BaseModel):
    """Shopping cart response payload."""

    id: str
    store_id: str | None = None
    status: str
    currency: str
    total_amount: float
    item_count: int
    items: list[CartItemResponse]


class CheckoutRequest(BaseModel):
    """Payload to convert cart into a placed order."""

    cart_id: uuid.UUID | None = Field(None, description="Optional specific cart ID to checkout")
    payment_method: str = Field(
        "simulated_upi", description="Payment method: simulated_upi, simulated_card"
    )
    pickup_time_slot: str | None = Field(None, description="Preferred in-store pickup time slot")


class OrderItemResponse(BaseModel):
    """Line item in placed order response."""

    id: str
    product_id: str
    sku: str
    product_name: str
    qty: int
    unit_price: float
    subtotal: float
    aisle: int
    bay: int
    shelf: int


class OrderResponse(BaseModel):
    """Placed order response payload."""

    id: str
    order_number: str
    store_id: str
    status: str
    total_amount: float
    currency: str
    pickup_time_slot: str | None = None
    payment_status: str
    payment_method: str
    created_at: str
    items: list[OrderItemResponse]
