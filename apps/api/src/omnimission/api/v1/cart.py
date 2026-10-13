"""Cart API endpoints supporting guest-to-user shopping workflows."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.deps import get_current_principal
from omnimission.core.errors import BadRequestError
from omnimission.core.principal import Principal
from omnimission.db.session import get_db_session
from omnimission.schemas.commerce import (
    AddCartItemRequest,
    CartResponse,
    MergeCartRequest,
    UpdateCartItemRequest,
)
from omnimission.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_service() -> CartService:
    """Dependency provider for CartService."""
    return CartService()


@router.get(
    "",
    response_model=CartResponse,
    summary="Get active shopping cart",
)
async def get_cart(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Retrieve the current active shopping cart for authenticated user or guest."""
    cart = await cart_service.get_or_create_cart(session, principal)
    return CartResponse(**cart_service.format_cart_summary(cart))


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to shopping cart",
)
async def add_cart_item(
    payload: AddCartItemRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Add a verified product to the cart with live price and shelf coordinates snapshot."""
    cart = await cart_service.get_or_create_cart(session, principal, store_id=payload.store_id)
    await cart_service.add_item(
        session=session,
        cart=cart,
        store_id=payload.store_id,
        product_id=payload.product_id,
        qty=payload.qty,
        notes=payload.notes,
    )
    await session.commit()
    await session.refresh(cart, ["items"])
    return CartResponse(**cart_service.format_cart_summary(cart))


@router.patch(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
)
async def update_cart_item(
    item_id: uuid.UUID,
    payload: UpdateCartItemRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Update line item quantity (setting to 0 removes the item)."""
    cart = await cart_service.get_or_create_cart(session, principal)
    await cart_service.update_item_qty(session, cart, item_id, payload.qty)
    await session.commit()
    await session.refresh(cart, ["items"])
    return CartResponse(**cart_service.format_cart_summary(cart))


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove item from cart",
)
async def remove_cart_item(
    item_id: uuid.UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Remove a line item from the active cart."""
    cart = await cart_service.get_or_create_cart(session, principal)
    await cart_service.remove_item(session, cart, item_id)
    await session.commit()
    await session.refresh(cart, ["items"])
    return CartResponse(**cart_service.format_cart_summary(cart))


@router.delete(
    "",
    response_model=CartResponse,
    summary="Clear active cart",
)
async def clear_cart(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Remove all items from active cart."""
    cart = await cart_service.get_or_create_cart(session, principal)
    await cart_service.clear_cart(session, cart)
    await session.commit()
    await session.refresh(cart, ["items"])
    return CartResponse(**cart_service.format_cart_summary(cart))


@router.post(
    "/merge",
    response_model=CartResponse,
    summary="Merge guest cart into authenticated user cart",
)
async def merge_cart(
    payload: MergeCartRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    """Merge an anonymous guest shopping cart into the user's permanent account upon login."""
    if not principal.is_authenticated or not principal.user_id:
        raise BadRequestError("Must be logged in to merge guest cart")

    merged_cart = await cart_service.merge_guest_cart_to_user(
        session=session,
        guest_session_id=payload.guest_session_id,
        user_id=principal.user_id,
    )
    await session.commit()
    await session.refresh(merged_cart, ["items"])
    return CartResponse(**cart_service.format_cart_summary(merged_cart))
