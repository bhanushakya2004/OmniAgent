"""Guarded NL2SQL security validator using sqlglot AST analysis."""

import uuid
from typing import Any

import sqlglot
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlglot import exp

from omnimission.core.errors import ForbiddenError


class SqlGuardError(ForbiddenError):
    """Raised when an agent SQL query violates security, read-only, or scoping constraints."""


ALLOWED_TABLES: set[str] = {
    "stores",
    "products",
    "store_inventory",
    "aisles",
    "bays",
    "shelves",
    "orders",
    "order_items",
    "shelf_audits",
    "restock_tasks",
    "shopper_queries",
    "action_proposals",
    "v_store_stock_overview",
    "v_daily_demand_aggregates",
    "v_aisle_traffic",
    "v_shrinkage_summary",
}

BLOCKED_TABLES: set[str] = {
    "users",
    "guest_sessions",
    "refresh_tokens",
    "user_memories",
}

STORE_SCOPED_TABLES: set[str] = {
    "store_inventory",
    "orders",
    "order_items",
    "shelf_audits",
    "restock_tasks",
    "action_proposals",
}


class SqlGuard:
    """Security validator and executor for natural-language generated SQL queries."""

    def __init__(
        self,
        max_limit: int = 100,
        statement_timeout_ms: int = 3000,
    ) -> None:
        self.max_limit = max_limit
        self.statement_timeout_ms = statement_timeout_ms

    def validate_and_sanitize(
        self,
        raw_sql: str,
        allowed_store_ids: list[uuid.UUID] | None = None,
    ) -> str:
        """Parse SQL with sqlglot, verify read-only Select statements, and enforce limits."""
        cleaned_sql = raw_sql.strip().rstrip(";")
        if not cleaned_sql:
            raise SqlGuardError("Empty SQL query is not allowed")

        try:
            parsed = sqlglot.parse_one(cleaned_sql, read="postgres")
        except Exception as e:
            raise SqlGuardError(f"Malformed SQL query syntax: {e}") from e

        # 1. Strictly verify statement type is SELECT / UNION
        if not isinstance(parsed, (exp.Select, exp.Union)):
            raise SqlGuardError(
                f"Unauthorized query type: {type(parsed).__name__}. Only read-only SELECT statements are permitted."
            )

        # 2. Inspect all referenced tables in AST
        tables_found: set[str] = set()
        for table_expr in parsed.find_all(exp.Table):
            table_name = table_expr.name.lower()
            tables_found.add(table_name)

            if table_name in BLOCKED_TABLES:
                raise SqlGuardError(
                    f"Access to sensitive table '{table_name}' is strictly forbidden."
                )

            # Allow views or known tables
            if table_name not in ALLOWED_TABLES and not table_name.startswith("v_"):
                raise SqlGuardError(
                    f"Table '{table_name}' is not in the merchant analytics allowlist."
                )

        # 3. Store scoping verification
        if allowed_store_ids is not None:
            # Check if store-scoped tables are referenced
            touches_store_scoped = any(t in STORE_SCOPED_TABLES for t in tables_found)
            if touches_store_scoped:
                # Check for store_id in columns or where clause
                has_store_filter = False
                for column in parsed.find_all(exp.Column):
                    if column.name.lower() == "store_id":
                        has_store_filter = True
                        break

                if not has_store_filter:
                    # Enforce store filter by raising error or requiring merchant scoping
                    raise SqlGuardError(
                        "Query touches store-specific data but lacks a 'store_id' filter. "
                        "Queries must include WHERE store_id = :store_id."
                    )

        # 4. Enforce LIMIT <= max_limit
        limit_expr = parsed.args.get("limit")
        if limit_expr is None:
            parsed = parsed.limit(self.max_limit)
        else:
            try:
                current_limit = int(limit_expr.expression.this)
                if current_limit > self.max_limit:
                    parsed = parsed.limit(self.max_limit)
            except Exception:
                parsed = parsed.limit(self.max_limit)

        return parsed.sql(dialect="postgres")

    async def execute_guarded(
        self,
        session: AsyncSession,
        sql: str,
        allowed_store_ids: list[uuid.UUID] | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Validate, sanitize, and execute read-only query with local statement timeout."""
        sanitized_sql = self.validate_and_sanitize(sql, allowed_store_ids=allowed_store_ids)

        # Set local statement timeout for this transaction
        timeout_query = text(f"SET LOCAL statement_timeout = '{self.statement_timeout_ms}ms';")
        await session.execute(timeout_query)

        # Execute sanitized read-only query
        result = await session.execute(text(sanitized_sql), params or {})
        rows = result.mappings().all()
        return [dict(row) for row in rows]
