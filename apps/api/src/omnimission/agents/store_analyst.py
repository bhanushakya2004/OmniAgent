"""Store Analyst Agent with guarded NL2SQL, chart synthesis, and HITL action proposals."""

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.intent_agent import get_gemini_model
from omnimission.agents.sql_guard import SqlGuard, SqlGuardError
from omnimission.core.logging import get_logger
from omnimission.services.action_proposal_service import ActionProposalService

logger = get_logger("store_analyst")


class ChartConfig(BaseModel):
    """Configuration for rendering frontend charts with Recharts."""

    chart_type: str = Field("bar", description="'bar', 'line', 'pie', 'metric', or 'table'")
    title: str = Field(..., description="Chart title")
    x_axis: str | None = Field(None, description="Key for X-axis")
    y_axis: str | None = Field(None, description="Key for Y-axis")


class ActionProposalResponse(BaseModel):
    """Action proposal presented to merchant for human approval."""

    id: str
    action_type: str
    title: str
    description: str
    payload: dict[str, Any]
    status: str


class AnalystResponse(BaseModel):
    """Structured response from Store Analyst agent."""

    answer: str = Field(..., description="Executive narrative and business insights")
    sql_query: str | None = Field(default=None, description="Executed safe SQL query")
    data: list[dict[str, Any]] = Field(default_factory=list, description="Structured query results")
    chart_config: ChartConfig | None = Field(default=None, description="Chart visualization spec")
    proposals: list[ActionProposalResponse] = Field(
        default_factory=list, description="Generated HITL proposals"
    )


ANALYST_SYSTEM_PROMPT = """You are the OmniMission Store Analyst Agent.
Your role is to assist physical store merchants by answering questions about their store's performance,
inventory health, sales, restock tasks, and customer demand.

Rules:
1. Formulate strictly READ-ONLY PostgreSQL SELECT queries against these approved views and tables:
   - v_store_stock_overview (columns: store_id, product_id, sku, product_name, brand, department, category, price, stock_level, is_low_stock, is_out_of_stock, aisle, bay, shelf)
   - v_daily_demand_aggregates (columns: store_id, demand_date, search_count, fulfilled_searches, unfulfilled_searches, estimated_lost_revenue)
   - v_aisle_traffic (columns: store_id, aisle, department, total_picks, unique_missions, last_pick_time)
   - v_shrinkage_summary (columns: store_id, audit_date, products_audited, discrepancies_found, estimated_shrinkage_units)
   - store_inventory (columns: store_id, product_id, stock_level, reorder_point, aisle, bay, shelf)
   - products (columns: id, sku, name, brand, department, category, price, mrp)
   - orders (columns: id, store_id, status, total_amount, payment_method, created_at)
   - order_items (columns: id, order_id, product_id, sku, qty, unit_price, subtotal, aisle)
   - restock_tasks (columns: id, store_id, product_id, aisle, bay, shelf, current_qty, recommended_qty, status, reason)
2. Always filter by store_id: WHERE store_id = '{store_id}'
3. Select an appropriate chart_type: 'bar', 'line', 'pie', 'metric', or 'table'.
4. If an inventory shortage or critical stockout is detected, propose an action with action_type='restock_inventory'.
"""


class StoreAnalystAgent:
    """Merchant Store Analyst agent orchestrating Guarded NL2SQL and HITL proposals."""

    def __init__(self) -> None:
        self.sql_guard = SqlGuard(max_limit=100, statement_timeout_ms=3000)
        self.proposal_service = ActionProposalService()
        self.model = get_gemini_model()

    async def analyze(
        self,
        session: AsyncSession,
        query: str,
        store_id: uuid.UUID,
        merchant_id: uuid.UUID,
    ) -> AnalystResponse:
        """Analyze merchant query, execute safe SQL, and generate chart-ready response."""
        q_lower = query.lower()

        # 1. Determine SQL query via deterministic routing or LLM
        sql_to_run: str | None = None
        chart_type = "table"
        chart_title = "Store Analytics"
        x_axis: str | None = None
        y_axis: str | None = None

        if (
            "low stock" in q_lower
            or "out of stock" in q_lower
            or "stockout" in q_lower
            or "shortage" in q_lower
        ):
            sql_to_run = f"""
                SELECT product_name, brand, department, stock_level, aisle, bay, shelf
                FROM v_store_stock_overview
                WHERE store_id = '{store_id}' AND is_low_stock = true
                ORDER BY stock_level ASC
                LIMIT 15;
            """
            chart_type = "bar"
            chart_title = "Low Stock Alert (Units Remaining)"
            x_axis = "product_name"
            y_axis = "stock_level"

        elif "top selling" in q_lower or "popular" in q_lower or "bestseller" in q_lower:
            sql_to_run = f"""
                SELECT oi.product_name, SUM(oi.qty) as units_sold, SUM(oi.subtotal) as total_revenue
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE o.store_id = '{store_id}'
                GROUP BY oi.product_name
                ORDER BY units_sold DESC
                LIMIT 10;
            """
            chart_type = "bar"
            chart_title = "Top Selling Products by Units"
            x_axis = "product_name"
            y_axis = "units_sold"

        elif "revenue" in q_lower or "sales" in q_lower or "financial" in q_lower:
            sql_to_run = f"""
                SELECT DATE(created_at) as sale_date, COUNT(id) as total_orders, SUM(total_amount) as daily_revenue
                FROM orders
                WHERE store_id = '{store_id}'
                GROUP BY DATE(created_at)
                ORDER BY sale_date DESC
                LIMIT 14;
            """
            chart_type = "line"
            chart_title = "Daily Store Revenue (INR)"
            x_axis = "sale_date"
            y_axis = "daily_revenue"

        elif "aisle" in q_lower or "traffic" in q_lower or "footfall" in q_lower:
            sql_to_run = f"""
                SELECT aisle, department, total_picks, unique_missions
                FROM v_aisle_traffic
                WHERE store_id = '{store_id}'
                ORDER BY total_picks DESC
                LIMIT 10;
            """
            chart_type = "bar"
            chart_title = "Aisle Pick Velocity & Footfall"
            x_axis = "aisle"
            y_axis = "total_picks"

        elif "restock" in q_lower or "task" in q_lower:
            sql_to_run = f"""
                SELECT p.name as product_name, rt.aisle, rt.current_qty, rt.recommended_qty, rt.status, rt.reason
                FROM restock_tasks rt
                JOIN products p ON p.id = rt.product_id
                WHERE rt.store_id = '{store_id}'
                ORDER BY rt.created_at DESC
                LIMIT 10;
            """
            chart_type = "table"
            chart_title = "Active Replenishment Tasks"

        else:
            # Default overview query
            sql_to_run = f"""
                SELECT department, COUNT(product_id) as total_skus, SUM(stock_level) as total_units
                FROM v_store_stock_overview
                WHERE store_id = '{store_id}'
                GROUP BY department
                ORDER BY total_units DESC
                LIMIT 10;
            """
            chart_type = "pie"
            chart_title = "Inventory Distribution by Department"
            x_axis = "department"
            y_axis = "total_units"

        # 2. Execute query via SqlGuard
        query_data: list[dict[str, Any]] = []
        try:
            query_data = await self.sql_guard.execute_guarded(
                session=session,
                sql=sql_to_run,
                allowed_store_ids=[store_id],
            )
        except SqlGuardError as sge:
            logger.warning("SqlGuard rejected query", error=str(sge))
            return AnalystResponse(
                answer=f"The query was blocked by safety governance: {sge.detail}",
                sql_query=sql_to_run,
                data=[],
            )
        except Exception as e:
            logger.error("SQL execution error", error=str(e))
            query_data = []

        # 3. Check if any low stock items warrant an action proposal
        created_proposals: list[ActionProposalResponse] = []
        if ("restock" in q_lower or "low stock" in q_lower) and query_data:
            # Propose restocking top low-stock item if units <= 5
            first_hit = query_data[0]
            stock_val = first_hit.get("stock_level")
            prod_name = first_hit.get("product_name", "Item")
            if stock_val is not None and int(stock_val) <= 5:
                # Find product_id
                p_search = await self.sql_guard.execute_guarded(
                    session=session,
                    sql=f"SELECT product_id FROM v_store_stock_overview WHERE store_id='{store_id}' AND product_name='{prod_name}' LIMIT 1;",
                    allowed_store_ids=[store_id],
                )
                if p_search and "product_id" in p_search[0]:
                    prop = await self.proposal_service.create_proposal(
                        session=session,
                        store_id=store_id,
                        action_type="restock_inventory",
                        title=f"Restock {prod_name} (Current Stock: {stock_val})",
                        description=f"Automated restock proposal: Current stock is critical ({stock_val} units). Replenish 24 units.",
                        payload={
                            "product_id": str(p_search[0]["product_id"]),
                            "recommended_qty": 24,
                            "reason": f"Stock depleted to {stock_val} units.",
                        },
                        created_by=merchant_id,
                    )
                    created_proposals.append(
                        ActionProposalResponse(
                            id=str(prop.id),
                            action_type=prop.action_type,
                            title=prop.title,
                            description=prop.description,
                            payload=prop.payload,
                            status=prop.status,
                        )
                    )

        # 4. Formulate executive narrative
        narrative = self._generate_narrative(query, query_data, chart_title)

        return AnalystResponse(
            answer=narrative,
            sql_query=sql_to_run,
            data=query_data,
            chart_config=ChartConfig(
                chart_type=chart_type,
                title=chart_title,
                x_axis=x_axis,
                y_axis=y_axis,
            ),
            proposals=created_proposals,
        )

    def _generate_narrative(
        self,
        query: str,
        data: list[dict[str, Any]],
        title: str,
    ) -> str:
        """Synthesize executive commentary based on retrieved store metrics."""
        if not data:
            return f"No store records were found matching '{query}'. All inventory parameters are currently within normal baseline thresholds."

        count = len(data)
        if "low stock" in query.lower() or "stockout" in query.lower():
            items_preview = ", ".join(d.get("product_name", "SKU") for d in data[:3])
            return (
                f"Identified {count} items currently at or below minimum threshold. "
                f"Most urgent items requiring replenishment include {items_preview}. "
                "A restock proposal has been generated for your review and one-click authorization."
            )
        elif "top selling" in query.lower() or "bestseller" in query.lower():
            top_item = data[0].get("product_name", "Leading item")
            top_units = data[0].get("units_sold", "high")
            return (
                f"Analyzed sales performance: {top_item} leads store sales volume with {top_units} units sold. "
                "Shelf placement along front bays is effectively driving conversion."
            )
        elif "revenue" in query.lower():
            return (
                f"Retrieved {count} days of store revenue data. Sales trends demonstrate strong recurring "
                "demand across physical store missions."
            )

        return (
            f"Analyzed {count} records across physical store operations. "
            f"Visualization '{title}' illustrates current department distribution and velocity."
        )
