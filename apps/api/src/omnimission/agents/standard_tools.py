"""Standard Governed Tools registered for OmniMission AI agent system."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.pg_hybrid_search import PgHybridSearch
from omnimission.adapters.toolbox_gateway import ToolboxGateway
from omnimission.agents.tool_registry import (
    SideEffectLevel,
    ToolRegistry,
    ToolScope,
    default_tool_registry,
)
from omnimission.core.principal import Principal
from omnimission.services.cart_service import CartService
from omnimission.services.knowledge_service import KnowledgeService

_search_adapter = PgHybridSearch()
_toolbox_gateway = ToolboxGateway()
_cart_service = CartService()
_knowledge_service = KnowledgeService()


# ---------------------------------------------------------------------------
# Shopper Tools (Read Only)
# ---------------------------------------------------------------------------


async def search_catalog(
    query: str,
    limit: int = 5,
    session: AsyncSession | None = None,
    store_ids: list[uuid.UUID] | None = None,
) -> list[dict[str, Any]]:
    """Search catalog items in selected stores matching query keywords or category."""
    if not session:
        raise ValueError("Database session required for catalog search.")
    hits = await _search_adapter.search(
        session=session,
        query=query,
        store_ids=store_ids or [],
        limit=min(max(1, limit), 20),
    )
    return [
        {
            "product_id": str(h.product_id),
            "store_id": str(h.store_id),
            "name": h.name,
            "brand": h.brand,
            "category": h.category,
            "size_label": h.size_label,
            "price": float(h.price),
            "stock_qty": h.stock_qty,
            "aisle": h.aisle,
            "bay": h.bay,
            "shelf": h.shelf,
            "dietary_tags": h.dietary_tags,
            "is_travel_size": h.is_travel_size,
        }
        for h in hits
    ]


async def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Retrieve grounded knowledge articles, recipes, travel guides, or substitution rules."""
    _ = session
    hits = await _knowledge_service.hybrid_search_chunks(
        query=query,
        limit=min(max(1, top_k), 10),
    )
    return [
        {
            "title": h.get("title", ""),
            "category": h.get("type", "knowledge"),
            "section": h.get("section_title", ""),
            "content": h.get("chunk_text", ""),
            "rrf_score": round(float(h.get("rrf_score", 0.0)), 4),
        }
        for h in hits
    ]


async def check_inventory(
    store_id: str,
    product_id: str,
    session: AsyncSession | None = None,
) -> dict[str, Any] | None:
    """Verify live stock level, unit price, and shelf coordinates for a specific SKU."""
    _ = session
    return await _toolbox_gateway.check_stock_levels(
        store_id=uuid.UUID(store_id),
        product_id=uuid.UUID(product_id),
    )


async def find_substitutes(
    store_id: str,
    category: str,
    dietary_tag: str,
    limit: int = 5,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Find valid in-stock dietary substitute products when an item is unavailable."""
    _ = session
    return await _toolbox_gateway.get_dietary_substitutes(
        store_id=uuid.UUID(store_id),
        category=category,
        dietary_tag=dietary_tag,
        limit=limit,
    )


async def get_cart(
    session: AsyncSession | None = None,
    principal: Principal | None = None,
    cart_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Retrieve current shopping cart contents, line item aisle coordinates, and total."""
    _ = cart_id
    if not session or not principal:
        raise ValueError("Session and Principal required for get_cart.")
    cart = await _cart_service.get_or_create_cart(
        session=session,
        principal=principal,
    )
    return {
        "cart_id": str(cart.id),
        "item_count": sum(it.qty for it in cart.items),
        "total_amount": float(cart.subtotal),
        "currency": cart.currency,
        "items": [
            {
                "item_id": str(it.id),
                "product_id": str(it.product_id),
                "product_name": it.product_name,
                "quantity": it.qty,
                "unit_price": float(it.unit_price),
                "subtotal": float(it.subtotal),
                "store_id": str(it.store_id),
                "aisle": it.aisle,
                "bay": it.bay,
                "shelf": it.shelf,
            }
            for it in cart.items
        ],
    }


# ---------------------------------------------------------------------------
# Shopper Tools (Action / Mutations)
# ---------------------------------------------------------------------------


async def add_to_cart(
    product_id: str,
    quantity: int = 1,
    store_id: str | None = None,
    session: AsyncSession | None = None,
    principal: Principal | None = None,
    cart_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Add a validated in-stock product into the caller's active shopping cart."""
    _ = cart_id
    if not session or not principal:
        raise ValueError("Session and Principal required for add_to_cart.")

    sid: uuid.UUID | None = uuid.UUID(store_id) if store_id else None
    cart = await _cart_service.get_or_create_cart(
        session=session,
        principal=principal,
        store_id=sid,
    )

    resolved_store_id = sid or cart.store_id
    if not resolved_store_id:
        raise ValueError("Store ID is required to add product to cart.")

    item = await _cart_service.add_item(
        session=session,
        cart=cart,
        store_id=resolved_store_id,
        product_id=uuid.UUID(product_id),
        qty=max(1, quantity),
    )
    await session.commit()
    return {
        "status": "added",
        "cart_id": str(cart.id),
        "added_item": {
            "product_id": str(item.product_id),
            "product_name": item.product_name,
            "quantity": item.qty,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
        },
        "total_amount": float(cart.subtotal),
        "item_count": sum(it.qty for it in cart.items),
    }


async def remove_from_cart(
    item_id: str,
    session: AsyncSession | None = None,
    principal: Principal | None = None,
    cart_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Remove a specific item line from the caller's shopping cart."""
    _ = cart_id
    if not session or not principal:
        raise ValueError("Session and Principal required for remove_from_cart.")

    cart = await _cart_service.get_or_create_cart(
        session=session,
        principal=principal,
    )
    await _cart_service.remove_item(
        session=session,
        cart=cart,
        item_id=uuid.UUID(item_id),
    )
    await session.commit()
    return {
        "status": "removed",
        "cart_id": str(cart.id),
        "total_amount": float(cart.subtotal),
        "item_count": sum(it.qty for it in cart.items),
    }


async def clear_cart(
    session: AsyncSession | None = None,
    principal: Principal | None = None,
    cart_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Remove all items from the caller's shopping cart."""
    _ = cart_id
    if not session or not principal:
        raise ValueError("Session and Principal required for clear_cart.")

    cart = await _cart_service.get_or_create_cart(
        session=session,
        principal=principal,
    )
    await _cart_service.clear_cart(session=session, cart=cart)
    await session.commit()
    return {
        "status": "cleared",
        "cart_id": str(cart.id),
        "total_amount": 0.0,
        "item_count": 0,
    }


# ---------------------------------------------------------------------------
# Merchant Tools (Gated by Role)
# ---------------------------------------------------------------------------


async def get_inventory_levels(
    store_id: str,
    department: str | None = None,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Merchant tool: inspect on-hand stock counts and low-stock SKUs across aisles."""
    if not session:
        raise ValueError("Database session required for get_inventory_levels.")

    query = """
        SELECT
            product_id,
            sku,
            product_name,
            category,
            stock_qty,
            price,
            aisle
        FROM v_store_inventory
        WHERE store_id = :store_id
    """
    params: dict[str, Any] = {"store_id": uuid.UUID(store_id)}
    if department:
        query += " AND category ILIKE :department"
        params["department"] = f"%{department}%"
    query += " ORDER BY stock_qty ASC LIMIT 50"

    result = await session.execute(text(query), params)
    return [dict(row) for row in result.mappings().all()]


async def get_stockout_risks(
    store_id: str,
    threshold: int = 5,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Merchant tool: list products with inventory below safety threshold."""
    if not session:
        raise ValueError("Database session required for get_stockout_risks.")

    query = """
        SELECT
            product_id,
            sku,
            product_name,
            category,
            stock_qty,
            aisle,
            bay
        FROM v_store_inventory
        WHERE store_id = :store_id
          AND stock_qty <= :threshold
        ORDER BY stock_qty ASC
        LIMIT 50
    """
    result = await session.execute(
        text(query),
        {"store_id": uuid.UUID(store_id), "threshold": threshold},
    )
    return [dict(row) for row in result.mappings().all()]


def register_standard_tools(registry: ToolRegistry = default_tool_registry) -> None:
    """Register all standard tools into the designated registry."""
    registry.register(
        name="search_catalog",
        description="Search for physical products in local stores with prices, aisles, and stock.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=search_catalog,
    )
    registry.register(
        name="retrieve_knowledge",
        description="Retrieve recipes, dietary guides, travel packing lists, or substitution rules.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=retrieve_knowledge,
    )
    registry.register(
        name="check_inventory",
        description="Verify current physical on-shelf stock and unit price for a store SKU.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=check_inventory,
    )
    registry.register(
        name="find_substitutes",
        description="Find in-stock dietary substitute products when an item is out of stock.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=find_substitutes,
    )
    registry.register(
        name="get_cart",
        description="Inspect caller's current cart items, total amount, and aisle coordinates.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=get_cart,
    )
    registry.register(
        name="add_to_cart",
        description="Add a verified in-stock physical product SKU to caller's active shopping cart.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.IDEMPOTENT_WRITE,
        func=add_to_cart,
    )
    registry.register(
        name="remove_from_cart",
        description="Remove a specific line item from caller's shopping cart.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.DESTRUCTIVE,
        func=remove_from_cart,
    )
    registry.register(
        name="clear_cart",
        description="Clear all items from the caller's active shopping cart.",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.DESTRUCTIVE,
        func=clear_cart,
    )
    registry.register(
        name="get_inventory_levels",
        description="Merchant operations: inspect store inventory levels and stock counts.",
        scope=ToolScope.MERCHANT,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=get_inventory_levels,
    )
    registry.register(
        name="get_stockout_risks",
        description="Merchant operations: identify products below critical safety stock threshold.",
        scope=ToolScope.MERCHANT,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=get_stockout_risks,
    )


# Automatically register on import
register_standard_tools()
