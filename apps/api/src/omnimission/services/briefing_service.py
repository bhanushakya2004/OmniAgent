"""Proactive Daily Briefing Service synthesizing physical store operational health."""

import datetime
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.action_proposal import ActionProposal
from omnimission.models.commerce import Order
from omnimission.models.inventory import StoreInventory
from omnimission.models.restock_task import RestockTask
from omnimission.models.store import Store


class DailyBriefingResponse(BaseModel):
    """Daily operational briefing for physical store managers."""

    store_id: str
    store_name: str
    date: str
    headline: str
    executive_summary: str
    kpis: dict[str, Any]
    urgent_alerts: list[str]
    pending_proposals_count: int


class DailyBriefingService:
    """Generates proactive intelligence briefings for store merchants."""

    async def generate_briefing(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
    ) -> DailyBriefingResponse:
        """Synthesize daily metrics and alerts for the store."""
        # 1. Fetch store info
        store_stmt = select(Store).where(Store.id == store_id)
        store_res = await session.execute(store_stmt)
        store = store_res.scalar_one_or_none()
        store_name = store.name if store else "Physical Store"

        # 2. Count low stock items & out of stock
        low_stock_stmt = select(func.count(StoreInventory.id)).where(
            StoreInventory.store_id == store_id,
            StoreInventory.stock_qty > 0,
            StoreInventory.stock_qty <= StoreInventory.low_stock_threshold,
        )
        low_stock_count = (await session.execute(low_stock_stmt)).scalar() or 0

        oos_stmt = select(func.count(StoreInventory.id)).where(
            StoreInventory.store_id == store_id,
            StoreInventory.stock_qty == 0,
        )
        oos_count = (await session.execute(oos_stmt)).scalar() or 0

        # 3. Count active restock tasks
        tasks_stmt = select(func.count(RestockTask.id)).where(
            RestockTask.store_id == store_id,
            RestockTask.status.in_(["pending", "in_progress"]),
        )
        pending_tasks_count = (await session.execute(tasks_stmt)).scalar() or 0

        # 4. Count pending action proposals
        prop_stmt = select(func.count(ActionProposal.id)).where(
            ActionProposal.store_id == store_id,
            ActionProposal.status == "pending_approval",
        )
        pending_proposals_count = (await session.execute(prop_stmt)).scalar() or 0

        # 5. Orders placed today
        today = datetime.datetime.now(datetime.UTC).date()
        orders_stmt = select(
            func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0)
        ).where(
            Order.store_id == store_id,
            func.date(Order.created_at) == today,
        )
        order_metrics = (await session.execute(orders_stmt)).first()
        today_orders_count = order_metrics[0] if order_metrics else 0
        today_revenue = float(order_metrics[1]) if order_metrics else 0.0

        # Formulate alerts and executive summary
        urgent_alerts: list[str] = []
        if oos_count > 0:
            urgent_alerts.append(
                f"CRITICAL: {oos_count} SKUs are completely out of stock on shelves."
            )
        if low_stock_count > 0:
            urgent_alerts.append(
                f"WARNING: {low_stock_count} SKUs have fallen below minimum reorder threshold."
            )
        if pending_proposals_count > 0:
            urgent_alerts.append(
                f"ACTION REQUIRED: {pending_proposals_count} agent restock proposals awaiting authorization."
            )

        headline = f"Store Health: {oos_count} Stockouts · {low_stock_count} Low Stock · {today_orders_count} Orders Today"
        executive_summary = (
            f"Good morning! Operations at {store_name} are tracking with ₹{today_revenue:,.2f} in sales today "
            f"across {today_orders_count} orders. {low_stock_count} SKUs require shelf replenishment. "
            f"The Store Analyst has prepared {pending_proposals_count} action proposals for your immediate sign-off."
        )

        return DailyBriefingResponse(
            store_id=str(store_id),
            store_name=store_name,
            date=today.isoformat(),
            headline=headline,
            executive_summary=executive_summary,
            kpis={
                "out_of_stock_skus": oos_count,
                "low_stock_skus": low_stock_count,
                "pending_restock_tasks": pending_tasks_count,
                "pending_proposals": pending_proposals_count,
                "today_orders": today_orders_count,
                "today_revenue_inr": today_revenue,
            },
            urgent_alerts=urgent_alerts,
            pending_proposals_count=pending_proposals_count,
        )
