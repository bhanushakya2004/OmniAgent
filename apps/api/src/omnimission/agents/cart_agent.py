"""Cart Action Agent executing grounded cart mutations for shoppers and guests.

Enforces the Grounding Invariant:
1. Every SKU added to cart must be physically verified in store inventory.
2. Unit prices and aisle coordinates are snapshotted directly from the database.
3. Supports single-turn additions, basket-level execution, removals, and cart clearing.
4. Returns structured CartActionResult with live cart totals and item summaries.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.schemas import (
    CartActionResult,
    CartItemSummary,
    OptimizedBasketItem,
)
from omnimission.core.logging import get_logger
from omnimission.core.principal import Principal
from omnimission.services.cart_service import CartService

logger = get_logger("cart_agent")


class CartAgent:
    """Action agent managing user and guest shopping cart operations."""

    def __init__(self, cart_service: CartService | None = None) -> None:
        self.cart_service = cart_service or CartService()

    async def add_basket_to_cart(
        self,
        session: AsyncSession,
        principal: Principal,
        basket_items: list[OptimizedBasketItem],
        auto_commit: bool = True,
    ) -> CartActionResult:
        """Add a planned, validated multi-item mission basket into caller's cart."""
        if not basket_items:
            cart = await self.cart_service.get_or_create_cart(session=session, principal=principal)
            return CartActionResult(
                success=True,
                cart_id=cart.id,
                added_items=[],
                skipped_items=[],
                total_amount=Decimal(str(cart.subtotal)),
                item_count=sum(it.qty for it in cart.items),
                message="No items provided in basket to add.",
            )

        # Primary store from first basket item
        primary_store_id = basket_items[0].store_id
        cart = await self.cart_service.get_or_create_cart(
            session=session,
            principal=principal,
            store_id=primary_store_id,
        )

        added: list[CartItemSummary] = []
        skipped: list[str] = []

        for item in basket_items:
            try:
                cart_item = await self.cart_service.add_item(
                    session=session,
                    cart=cart,
                    store_id=item.store_id,
                    product_id=item.product_id,
                    qty=max(1, item.quantity),
                    notes=item.match_explanation,
                )
                added.append(
                    CartItemSummary(
                        product_id=cart_item.product_id,
                        product_name=cart_item.product_name,
                        quantity=cart_item.qty,
                        unit_price=cart_item.unit_price,
                        subtotal=cart_item.subtotal,
                        aisle=cart_item.aisle,
                        store_id=cart_item.store_id,
                    )
                )
            except Exception as err:
                logger.warning(
                    "cart_agent_failed_adding_item",
                    product_id=str(item.product_id),
                    name=item.name,
                    error=str(err),
                )
                skipped.append(f"{item.name} ({str(err)})")

        if auto_commit:
            await session.commit()
            # Refresh cart state after commit
            cart = await self.cart_service.get_or_create_cart(session=session, principal=principal)

        total_amount = Decimal(str(cart.subtotal))
        item_count = sum(it.qty for it in cart.items)
        success = len(added) > 0 or len(basket_items) == 0

        msg = f"Successfully added {len(added)} items to your cart (Total: INR {total_amount:.2f})."
        if skipped:
            msg += f" {len(skipped)} item(s) could not be added due to stock limits."

        return CartActionResult(
            success=success,
            cart_id=cart.id,
            added_items=added,
            skipped_items=skipped,
            total_amount=total_amount,
            item_count=item_count,
            message=msg,
        )

    async def execute_cart_action(
        self,
        session: AsyncSession,
        principal: Principal,
        action: str,
        product_id: str | None = None,
        store_id: str | None = None,
        quantity: int = 1,
        item_id: str | None = None,
        auto_commit: bool = True,
    ) -> CartActionResult:
        """Execute atomic cart actions ('add', 'remove', 'clear', 'view')."""
        clean_action = action.lower().strip()
        cart = await self.cart_service.get_or_create_cart(
            session=session,
            principal=principal,
            store_id=uuid.UUID(store_id) if store_id else None,
        )

        if clean_action == "view":
            return CartActionResult(
                success=True,
                cart_id=cart.id,
                added_items=[
                    CartItemSummary(
                        product_id=it.product_id,
                        product_name=it.product_name,
                        quantity=it.qty,
                        unit_price=it.unit_price,
                        subtotal=it.subtotal,
                        aisle=it.aisle,
                        store_id=it.store_id,
                    )
                    for it in cart.items
                ],
                skipped_items=[],
                total_amount=Decimal(str(cart.subtotal)),
                item_count=sum(it.qty for it in cart.items),
                message=f"Cart has {sum(it.qty for it in cart.items)} items totaling INR {cart.subtotal:.2f}.",
            )

        if clean_action == "clear":
            await self.cart_service.clear_cart(session=session, cart=cart)
            if auto_commit:
                await session.commit()
            return CartActionResult(
                success=True,
                cart_id=cart.id,
                added_items=[],
                skipped_items=[],
                total_amount=Decimal("0.00"),
                item_count=0,
                message="Cart cleared successfully.",
            )

        if clean_action == "remove":
            if not item_id:
                raise ValueError("Item ID is required for remove action.")
            await self.cart_service.remove_item(
                session=session, cart=cart, item_id=uuid.UUID(item_id)
            )
            if auto_commit:
                await session.commit()
                cart = await self.cart_service.get_or_create_cart(
                    session=session, principal=principal
                )
            return CartActionResult(
                success=True,
                cart_id=cart.id,
                added_items=[],
                skipped_items=[],
                total_amount=Decimal(str(cart.subtotal)),
                item_count=sum(it.qty for it in cart.items),
                message="Item removed from cart.",
            )

        if clean_action == "add":
            if not product_id:
                raise ValueError("Product ID is required for add action.")
            target_store_id = uuid.UUID(store_id) if store_id else cart.store_id
            if not target_store_id:
                raise ValueError("Store ID is required to add product to cart.")

            cart_item = await self.cart_service.add_item(
                session=session,
                cart=cart,
                store_id=target_store_id,
                product_id=uuid.UUID(product_id),
                qty=max(1, quantity),
            )
            if auto_commit:
                await session.commit()
                cart = await self.cart_service.get_or_create_cart(
                    session=session, principal=principal
                )

            summary = CartItemSummary(
                product_id=cart_item.product_id,
                product_name=cart_item.product_name,
                quantity=cart_item.qty,
                unit_price=cart_item.unit_price,
                subtotal=cart_item.subtotal,
                aisle=cart_item.aisle,
                store_id=cart_item.store_id,
            )
            return CartActionResult(
                success=True,
                cart_id=cart.id,
                added_items=[summary],
                skipped_items=[],
                total_amount=Decimal(str(cart.subtotal)),
                item_count=sum(it.qty for it in cart.items),
                message=f"Added '{cart_item.product_name}' to cart.",
            )

        raise ValueError(f"Unsupported cart action '{action}'.")
