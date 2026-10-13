"""Order and checkout API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.deps import get_current_principal, get_current_user
from omnimission.core.errors import BadRequestError, NotFoundError
from omnimission.core.principal import Principal
from omnimission.db.session import get_db_session
from omnimission.models.user import User
from omnimission.schemas.commerce import CheckoutRequest, OrderResponse
from omnimission.services.cart_service import CartService
from omnimission.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service() -> OrderService:
    """Dependency provider for OrderService."""
    return OrderService()


def get_cart_service() -> CartService:
    """Dependency provider for CartService."""
    return CartService()


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout shopping cart and place order",
)
async def checkout(
    payload: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    """Convert active cart into placed order with simulated payment and in-store pickup coordinates."""
    cart = await cart_service.get_or_create_cart(session, principal)
    if not cart.items:
        raise BadRequestError("Cannot checkout an empty shopping cart")

    order = await order_service.checkout(
        session=session,
        user=current_user,
        cart=cart,
        payment_method=payload.payment_method,
        pickup_time_slot=payload.pickup_time_slot,
    )
    await session.commit()
    await session.refresh(order, ["items"])
    return OrderResponse(**order_service.format_order_summary(order))


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List past orders",
)
async def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> list[OrderResponse]:
    """Retrieve historical orders placed by the authenticated user."""
    orders = await order_service.list_user_orders(session, current_user.id)
    return [OrderResponse(**order_service.format_order_summary(o)) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
)
async def get_order_detail(
    order_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    """Retrieve detailed order information with aisle locations and payment status."""
    order = await order_service.get_order_by_id(
        session=session,
        order_id=order_id,
        user_id=current_user.id if current_user.role != "merchant" else None,
    )
    if not order:
        raise NotFoundError("Order not found")

    return OrderResponse(**order_service.format_order_summary(order))
