"""Order placement and simulated checkout service."""

import datetime
import random
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from omnimission.core.errors import BadRequestError, NotFoundError
from omnimission.core.logging import get_logger
from omnimission.models.commerce import Cart, Order, OrderItem, PaymentSimulated
from omnimission.models.inventory import StoreInventory
from omnimission.models.restock_task import RestockTask
from omnimission.models.user import User


class OrderService:
    """Handles checkout execution, atomic inventory decrements, and mock simulated payments."""

    def __init__(self) -> None:
        self.logger = get_logger("order_service")

    async def checkout(
        self,
        session: AsyncSession,
        user: User,
        cart: Cart,
        payment_method: str = "simulated_upi",
        pickup_time_slot: str | None = None,
    ) -> Order:
        """Execute transactional checkout converting active cart into placed order."""
        if not cart.items:
            raise BadRequestError("Cannot checkout an empty shopping cart")

        if cart.status != "active":
            raise BadRequestError(f"Cart is already {cart.status}")

        target_store_id = cart.store_id or cart.items[0].store_id

        # 1. Validate live stock and calculate total
        total = Decimal("0.00")
        stock_updates: list[tuple[StoreInventory, int]] = []

        for item in cart.items:
            inv_stmt = select(StoreInventory).where(
                StoreInventory.store_id == item.store_id,
                StoreInventory.product_id == item.product_id,
            )
            inv_res = await session.execute(inv_stmt)
            inv = inv_res.scalar_one_or_none()
            if not inv:
                raise NotFoundError(f"SKU {item.sku} no longer found in store inventory")

            if inv.stock_qty < item.qty:
                raise BadRequestError(
                    f"Insufficient stock for '{item.product_name}'. Requested {item.qty}, only {inv.stock_qty} available"
                )

            line_total = Decimal(str(item.unit_price)) * item.qty
            total += line_total
            stock_updates.append((inv, item.qty))

        # 2. Create Order
        now_utc = datetime.datetime.now(datetime.UTC)
        order_num = f"OMNI-{now_utc.strftime('%Y%m%d')}-{random.randint(100000, 999999)}"

        order = Order(
            user_id=user.id,
            store_id=target_store_id,
            cart_id=cart.id,
            order_number=order_num,
            status="placed",
            total_amount=total,
            currency=cart.currency,
            pickup_time_slot=pickup_time_slot or "Ready for pickup in 2 hours",
            payment_status="simulated_paid",
            payment_method=payment_method,
        )
        session.add(order)
        await session.flush()

        # 3. Create OrderItems & decrement stock
        for item, (inv, qty) in zip(cart.items, stock_updates, strict=True):
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                sku=item.sku,
                product_name=item.product_name,
                qty=qty,
                unit_price=item.unit_price,
                subtotal=Decimal(str(item.unit_price)) * qty,
                aisle=item.aisle,
                bay=item.bay,
                shelf=item.shelf,
            )
            session.add(order_item)

            # Atomic stock reduction
            inv.stock_qty = max(0, inv.stock_qty - qty)

            # Proactive Restock Task if stock dropped to or below threshold
            if inv.stock_qty <= inv.low_stock_threshold:
                restock_task = RestockTask(
                    store_id=inv.store_id,
                    product_id=inv.product_id,
                    aisle=inv.aisle,
                    bay=inv.bay,
                    shelf=inv.shelf,
                    current_qty=inv.stock_qty,
                    recommended_qty=inv.low_stock_threshold * 3,
                    reason="checkout_stock_depletion",
                    status="pending",
                    source="customer_order",
                )
                session.add(restock_task)
                self.logger.info(
                    "restock_task_generated",
                    store_id=str(inv.store_id),
                    sku=inv.sku,
                    remaining_stock=inv.stock_qty,
                )

        # 4. Create Simulated Payment
        payment = PaymentSimulated(
            order_id=order.id,
            amount=total,
            method=payment_method,
            status="succeeded",
            reference=f"SIM_PAY_{uuid.uuid4().hex[:12].upper()}",
        )
        session.add(payment)

        # 5. Mark Cart as Converted
        cart.status = "converted"

        await session.flush()
        await session.refresh(order, ["items"])
        self.logger.info(
            "order_placed_successfully",
            order_id=str(order.id),
            order_number=order.order_number,
            total=float(total),
        )
        return order

    async def get_order_by_id(
        self,
        session: AsyncSession,
        order_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> Order | None:
        """Retrieve order by ID with line items and optional user authorization check."""
        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)

        res = await session.execute(stmt)
        return res.scalars().first()

    async def list_user_orders(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[Order]:
        """List past orders placed by the user."""
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    def format_order_summary(self, order: Order) -> dict[str, Any]:
        """Format order into clean JSON-serializable structure."""
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "store_id": str(order.store_id),
            "status": order.status,
            "total_amount": float(order.total_amount),
            "currency": order.currency,
            "pickup_time_slot": order.pickup_time_slot,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "id": str(it.id),
                    "product_id": str(it.product_id),
                    "sku": it.sku,
                    "product_name": it.product_name,
                    "qty": it.qty,
                    "unit_price": float(it.unit_price),
                    "subtotal": float(it.subtotal),
                    "aisle": it.aisle,
                    "bay": it.bay,
                    "shelf": it.shelf,
                }
                for it in order.items
            ],
        }
