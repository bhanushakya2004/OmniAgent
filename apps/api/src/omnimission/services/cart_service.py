"""Shopping cart business service with guest-to-user merging and stock price snapshots."""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from omnimission.core.errors import BadRequestError, NotFoundError
from omnimission.core.logging import get_logger
from omnimission.core.principal import Principal
from omnimission.models.commerce import Cart, CartItem, GuestSession
from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product


class CartService:
    """Manages active carts, item additions, quantity modifications, and guest session merges."""

    def __init__(self) -> None:
        self.logger = get_logger("cart_service")

    async def get_or_create_cart(
        self,
        session: AsyncSession,
        principal: Principal,
        store_id: uuid.UUID | None = None,
    ) -> Cart:
        """Retrieve existing active cart or initialize a new one for principal."""
        if principal.is_authenticated and principal.user_id:
            stmt = (
                select(Cart)
                .options(selectinload(Cart.items))
                .where(Cart.user_id == principal.user_id, Cart.status == "active")
                .order_by(Cart.created_at.desc())
            )
        else:
            stmt = (
                select(Cart)
                .options(selectinload(Cart.items))
                .where(Cart.guest_session_id == principal.guest_session_id, Cart.status == "active")
                .order_by(Cart.created_at.desc())
            )

        res = await session.execute(stmt)
        cart = res.scalars().first()

        if cart is None:
            cart = Cart(
                user_id=principal.user_id if principal.is_authenticated else None,
                guest_session_id=principal.guest_session_id if principal.is_guest else None,
                store_id=store_id,
                status="active",
                currency="INR",
            )
            session.add(cart)
            await session.flush()
            await session.refresh(cart, ["items"])
            self.logger.info("cart_created", cart_id=str(cart.id), is_guest=principal.is_guest)
        elif store_id and cart.store_id is None:
            cart.store_id = store_id
            await session.flush()

        return cart

    async def add_item(
        self,
        session: AsyncSession,
        cart: Cart,
        store_id: uuid.UUID,
        product_id: uuid.UUID,
        qty: int = 1,
        notes: str | None = None,
    ) -> CartItem:
        """Add item to cart or increment quantity with verified price and shelf coordinates."""
        if qty <= 0:
            raise BadRequestError("Item quantity must be at least 1")

        # 1. Verify in store inventory and get product details
        inv_stmt = (
            select(StoreInventory, Product)
            .join(Product, StoreInventory.product_id == Product.id)
            .where(
                StoreInventory.store_id == store_id,
                StoreInventory.product_id == product_id,
            )
        )
        inv_res = await session.execute(inv_stmt)
        row = inv_res.first()
        if not row:
            raise NotFoundError("Product is not available at the specified store")

        inventory, product = row
        if inventory.stock_qty <= 0:
            raise BadRequestError(f"'{product.name}' is currently out of stock at this store")

        # 2. Check if item already exists in cart
        item_stmt = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.store_id == store_id,
            CartItem.product_id == product_id,
        )
        item_res = await session.execute(item_stmt)
        item = item_res.scalar_one_or_none()

        if item:
            item.qty += qty
            if notes:
                item.notes = notes
            # Update price snapshot
            item.unit_price = inventory.price
        else:
            item = CartItem(
                cart_id=cart.id,
                store_id=store_id,
                product_id=product_id,
                sku=inventory.sku,
                product_name=product.name,
                qty=qty,
                unit_price=inventory.price,
                aisle=inventory.aisle,
                bay=inventory.bay,
                shelf=inventory.shelf,
                notes=notes,
            )
            session.add(item)

        if cart.store_id is None:
            cart.store_id = store_id

        await session.flush()
        await session.refresh(cart, ["items"])
        self.logger.info(
            "cart_item_added",
            cart_id=str(cart.id),
            product=product.name,
            qty=item.qty,
            price=float(item.unit_price),
        )
        return item

    async def update_item_qty(
        self,
        session: AsyncSession,
        cart: Cart,
        item_id: uuid.UUID,
        qty: int,
    ) -> CartItem | None:
        """Update item quantity or remove item if qty is zero."""
        item_stmt = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        item_res = await session.execute(item_stmt)
        item = item_res.scalar_one_or_none()
        if not item:
            raise NotFoundError("Cart item not found")

        if qty <= 0:
            await session.delete(item)
            await session.flush()
            await session.refresh(cart, ["items"])
            return None

        item.qty = qty
        await session.flush()
        await session.refresh(cart, ["items"])
        return item

    async def remove_item(
        self,
        session: AsyncSession,
        cart: Cart,
        item_id: uuid.UUID,
    ) -> None:
        """Remove a line item from cart."""
        item_stmt = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        item_res = await session.execute(item_stmt)
        item = item_res.scalar_one_or_none()
        if not item:
            raise NotFoundError("Cart item not found")

        await session.delete(item)
        await session.flush()
        await session.refresh(cart, ["items"])

    async def clear_cart(self, session: AsyncSession, cart: Cart) -> None:
        """Clear all items in cart."""
        await session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await session.flush()
        await session.refresh(cart, ["items"])

    async def merge_guest_cart_to_user(
        self,
        session: AsyncSession,
        guest_session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Cart:
        """Transfer all items from guest cart into user cart upon login/register."""
        # Find active guest cart
        guest_cart_stmt = (
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.guest_session_id == guest_session_id, Cart.status == "active")
        )
        guest_res = await session.execute(guest_cart_stmt)
        guest_cart = guest_res.scalars().first()

        # Find or create user cart
        user_cart_stmt = (
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.user_id == user_id, Cart.status == "active")
        )
        user_res = await session.execute(user_cart_stmt)
        user_cart = user_res.scalars().first()

        if not user_cart:
            user_cart = Cart(
                user_id=user_id,
                store_id=guest_cart.store_id if guest_cart else None,
                status="active",
                currency="INR",
            )
            session.add(user_cart)
            await session.flush()
            await session.refresh(user_cart, ["items"])

        if guest_cart and guest_cart.items:
            existing_user_items = {(it.store_id, it.product_id): it for it in user_cart.items}
            for g_item in guest_cart.items:
                key = (g_item.store_id, g_item.product_id)
                if key in existing_user_items:
                    existing_user_items[key].qty += g_item.qty
                    await session.delete(g_item)
                else:
                    g_item.cart_id = user_cart.id

            guest_cart.status = "merged"
            if user_cart.store_id is None and guest_cart.store_id:
                user_cart.store_id = guest_cart.store_id

        # Link guest session record to user
        gs_stmt = select(GuestSession).where(GuestSession.id == guest_session_id)
        gs_res = await session.execute(gs_stmt)
        gs = gs_res.scalar_one_or_none()
        if gs:
            gs.user_id = user_id

        await session.flush()
        await session.refresh(user_cart, ["items"])
        self.logger.info("guest_cart_merged", user_id=str(user_id), item_count=len(user_cart.items))
        return user_cart

    def format_cart_summary(self, cart: Cart) -> dict[str, Any]:
        """Produce JSON-serializable dictionary with subtotal, count, and items."""
        total = Decimal("0.00")
        items_payload: list[dict[str, Any]] = []

        for item in cart.items:
            subtotal = Decimal(str(item.unit_price)) * item.qty
            total += subtotal
            items_payload.append(
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "store_id": str(item.store_id),
                    "sku": item.sku,
                    "product_name": item.product_name,
                    "qty": item.qty,
                    "unit_price": float(item.unit_price),
                    "subtotal": float(subtotal),
                    "aisle": item.aisle,
                    "bay": item.bay,
                    "shelf": item.shelf,
                    "notes": item.notes,
                }
            )

        return {
            "id": str(cart.id),
            "store_id": str(cart.store_id) if cart.store_id else None,
            "status": cart.status,
            "currency": cart.currency,
            "total_amount": float(total),
            "item_count": sum(it.qty for it in cart.items),
            "items": items_payload,
        }
