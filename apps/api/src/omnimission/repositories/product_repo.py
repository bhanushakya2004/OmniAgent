"""Product catalog repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.product import Product


class ProductRepository:
    """Repository managing Product catalog access."""

    async def get_by_id(self, session: AsyncSession, product_id: uuid.UUID) -> Product | None:
        """Fetch product by UUID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, session: AsyncSession, product_ids: list[uuid.UUID]
    ) -> list[Product]:
        """Fetch multiple products by list of UUIDs."""
        if not product_ids:
            return []
        stmt = select(Product).where(Product.id.in_(product_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        session: AsyncSession,
        category: str,
        limit: int = 50,
    ) -> list[Product]:
        """Fetch products in category."""
        stmt = select(Product).where(Product.category == category).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
