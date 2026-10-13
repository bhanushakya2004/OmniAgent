"""Adapter implementing DataToolPort using parameterized queries and Google MCP Toolbox."""

import logging
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from omnimission.core.config import get_settings
from omnimission.db.session import async_session_factory
from omnimission.ports.data_tool_port import DataToolPort

logger = logging.getLogger("omnimission.toolbox_gateway")


class ToolboxGateway(DataToolPort):
    """Gateway connecting Agno agents and services to Google MCP Toolbox & curated views.

    Guarantees the Grounding Invariant: read-only, parameterized queries against
    curated views (v_store_inventory, v_aisle_locations, v_product_details, v_store_details).
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        toolbox_url: str | None = None,
    ) -> None:
        self.session_factory = session_factory or async_session_factory
        settings = get_settings()
        self.toolbox_url = toolbox_url or settings.toolbox_url

    async def search_store_inventory(
        self, store_id: uuid.UUID, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search in-stock products in a specific physical store by partial query."""
        clamped_limit = min(max(1, limit), 50)
        clean_query = query.strip()
        search_pattern = f"%{clean_query}%"

        stmt = text(
            """
            SELECT
                product_id,
                sku,
                product_name,
                brand,
                category,
                subcategory,
                size_label,
                unit,
                dietary_tags,
                is_travel_size,
                stock_qty,
                price,
                mrp,
                currency,
                aisle,
                bay,
                shelf
            FROM v_store_inventory
            WHERE store_id = :store_id
              AND (
                  product_name ILIKE :pattern
                  OR brand ILIKE :pattern
                  OR category ILIKE :pattern
                  OR subcategory ILIKE :pattern
              )
            ORDER BY stock_qty DESC, product_name ASC
            LIMIT :limit;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(
                stmt,
                {"store_id": store_id, "pattern": search_pattern, "limit": clamped_limit},
            )
            rows = result.mappings().all()
            return [dict(r) for r in rows]

    async def get_product_location(
        self, store_id: uuid.UUID, sku: str
    ) -> dict[str, Any] | None:
        """Lookup physical aisle, bay, and shelf coordinates for a SKU in a store."""
        stmt = text(
            """
            SELECT
                store_id,
                store_name,
                product_id,
                sku,
                product_name,
                brand,
                aisle,
                bay,
                shelf,
                stock_qty,
                price
            FROM v_aisle_locations
            WHERE store_id = :store_id AND sku = :sku;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(stmt, {"store_id": store_id, "sku": sku.strip()})
            row = result.mappings().first()
            return dict(row) if row else None

    async def check_stock_levels(
        self, store_id: uuid.UUID, product_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get live on-shelf stock quantity and unit price for a product."""
        stmt = text(
            """
            SELECT
                store_id,
                product_id,
                sku,
                product_name,
                stock_qty,
                price,
                currency
            FROM v_store_inventory
            WHERE store_id = :store_id AND product_id = :product_id;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(
                stmt, {"store_id": store_id, "product_id": product_id}
            )
            row = result.mappings().first()
            return dict(row) if row else None

    async def get_dietary_substitutes(
        self, store_id: uuid.UUID, category: str, dietary_tag: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find in-stock substitutes matching a specific dietary requirement."""
        clamped_limit = min(max(1, limit), 20)
        cat_pattern = f"%{category.strip()}%"

        stmt = text(
            """
            SELECT
                product_id,
                sku,
                product_name,
                brand,
                category,
                subcategory,
                dietary_tags,
                stock_qty,
                price,
                aisle,
                bay,
                shelf
            FROM v_dietary_substitutes
            WHERE store_id = :store_id
              AND (category ILIKE :cat OR subcategory ILIKE :cat)
              AND :tag = ANY(dietary_tags)
            ORDER BY stock_qty DESC
            LIMIT :limit;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(
                stmt,
                {
                    "store_id": store_id,
                    "cat": cat_pattern,
                    "tag": dietary_tag.strip().lower(),
                    "limit": clamped_limit,
                },
            )
            rows = result.mappings().all()
            return [dict(r) for r in rows]

    async def get_store_details(
        self, store_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Retrieve store metadata, address, contact, and opening hours."""
        stmt = text(
            """
            SELECT
                store_id,
                merchant_id,
                store_name,
                address,
                city,
                lat,
                lng,
                phone,
                opening_hours,
                is_active
            FROM v_store_details
            WHERE store_id = :store_id;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(stmt, {"store_id": store_id})
            row = result.mappings().first()
            return dict(row) if row else None

    async def find_nearby_stores(
        self, lat: float, lng: float, radius_km: float = 10.0
    ) -> list[dict[str, Any]]:
        """Find active physical retail stores within a geographic radius."""
        stmt = text(
            """
            SELECT
                store_id,
                merchant_id,
                store_name,
                address,
                city,
                lat,
                lng,
                phone,
                (point(lng, lat) <@> point(:lng, :lat)) * 1.609344 AS distance_km
            FROM v_store_details
            WHERE is_active = true
              AND (point(lng, lat) <@> point(:lng, :lat)) * 1.609344 <= :radius_km
            ORDER BY distance_km ASC;
            """
        )

        async with self.session_factory() as session:
            result = await session.execute(
                stmt, {"lat": lat, "lng": lng, "radius_km": radius_km}
            )
            rows = result.mappings().all()
            return [dict(r) for r in rows]

    def get_agno_tools(self) -> list[Callable[..., Any]]:
        """Return Python functions typed and documented for Agno agent tool calls."""

        async def search_inventory(
            store_id_str: str, query: str, limit: int = 10
        ) -> list[dict[str, Any]]:
            """Search for products in a store by title, brand, or category.

            Args:
                store_id_str: UUID string of the store.
                query: Product search keyword.
                limit: Maximum items to return (1-50).
            """
            sid = uuid.UUID(store_id_str)
            return await self.search_store_inventory(sid, query, limit)

        async def locate_product(store_id_str: str, sku: str) -> dict[str, Any] | None:
            """Lookup aisle, bay, and shelf for a product SKU in a physical store.

            Args:
                store_id_str: UUID string of the store.
                sku: Product SKU code.
            """
            sid = uuid.UUID(store_id_str)
            return await self.get_product_location(sid, sku)

        async def verify_stock(
            store_id_str: str, product_id_str: str
        ) -> dict[str, Any] | None:
            """Verify current on-shelf stock level and price for a product.

            Args:
                store_id_str: UUID string of the store.
                product_id_str: UUID string of the product.
            """
            sid = uuid.UUID(store_id_str)
            pid = uuid.UUID(product_id_str)
            return await self.check_stock_levels(sid, pid)

        async def find_substitutes(
            store_id_str: str, category: str, dietary_tag: str, limit: int = 5
        ) -> list[dict[str, Any]]:
            """Find alternative products matching a dietary tag (e.g. gluten_free, eggless, vegan).

            Args:
                store_id_str: UUID string of the store.
                category: Category of the original item.
                dietary_tag: Dietary requirement tag.
                limit: Maximum substitutes to retrieve.
            """
            sid = uuid.UUID(store_id_str)
            return await self.get_dietary_substitutes(sid, category, dietary_tag, limit)

        return [search_inventory, locate_product, verify_stock, find_substitutes]
