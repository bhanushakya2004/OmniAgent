"""Store data access repository."""

import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product
from omnimission.models.store import Store


class StoreRepository:
    """Repository managing store entities and geospatial proximity queries."""

    async def get_by_id(self, session: AsyncSession, store_id: uuid.UUID) -> Store | None:
        """Fetch store by UUID."""
        stmt = select(Store).where(Store.id == store_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_nearby(
        self,
        session: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float = 25.0,
        limit: int = 10,
    ) -> list[tuple[Store, float]]:
        """Find stores within radius_km using exact Haversine distance formula in SQL."""
        # Convert degrees to radians
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)

        # Haversine distance in kilometers (Earth radius ~ 6371.0 km)
        distance_expr = 6371.0 * func.acos(
            func.least(
                1.0,
                func.greatest(
                    -1.0,
                    func.cos(lat_rad)
                    * func.cos(func.radians(Store.lat))
                    * func.cos(func.radians(Store.lng) - lng_rad)
                    + func.sin(lat_rad) * func.sin(func.radians(Store.lat)),
                ),
            )
        )

        stmt = (
            select(Store, distance_expr.label("distance_km"))
            .where(Store.is_active.is_(True))
            .where(distance_expr <= radius_km)
            .order_by("distance_km")
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.all()
        return [(row[0], round(float(row[1]), 2)) for row in rows]

    async def search_by_text(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 10,
    ) -> list[Store]:
        """Search stores by city or name."""
        pattern = f"%{query.strip()}%"
        stmt = (
            select(Store)
            .where(Store.is_active.is_(True))
            .where(
                (Store.name.ilike(pattern))
                | (Store.city.ilike(pattern))
                | (Store.address.ilike(pattern))
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active(self, session: AsyncSession) -> list[Store]:
        """List all active stores."""
        stmt = select(Store).where(Store.is_active.is_(True)).order_by(Store.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_store_categories(self, session: AsyncSession, store_id: uuid.UUID) -> list[str]:
        """Retrieve distinct product categories available in a store."""
        stmt = (
            select(Product.category)
            .join(StoreInventory, StoreInventory.product_id == Product.id)
            .where(StoreInventory.store_id == store_id, StoreInventory.stock_qty > 0)
            .distinct()
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_store_skus(self, session: AsyncSession, store_id: uuid.UUID) -> int:
        """Count total SKUs stocked at a store."""
        stmt = select(func.count(StoreInventory.id)).where(StoreInventory.store_id == store_id)
        result = await session.execute(stmt)
        return int(result.scalar_one() or 0)
