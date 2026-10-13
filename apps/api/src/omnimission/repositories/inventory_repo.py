"""Store inventory repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from omnimission.models.inventory import StoreInventory


class InventoryRepository:
    """Repository managing store inventory levels and aisle coordinates."""

    async def get_by_store_and_product(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> StoreInventory | None:
        """Fetch inventory item with loaded product relationship."""
        stmt = (
            select(StoreInventory)
            .options(selectinload(StoreInventory.product))
            .where(
                StoreInventory.store_id == store_id,
                StoreInventory.product_id == product_id,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_inventory_for_store(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StoreInventory]:
        """Fetch paginated inventory items for a store."""
        stmt = (
            select(StoreInventory)
            .options(selectinload(StoreInventory.product))
            .where(StoreInventory.store_id == store_id)
            .order_by(StoreInventory.aisle, StoreInventory.bay, StoreInventory.shelf)
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_distinct_aisles(self, session: AsyncSession, store_id: uuid.UUID) -> list[int]:
        """Fetch distinct aisle numbers in a store."""
        stmt = (
            select(StoreInventory.aisle)
            .where(StoreInventory.store_id == store_id)
            .distinct()
            .order_by(StoreInventory.aisle)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
