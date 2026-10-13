"""Store business service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.errors import NotFoundError
from omnimission.repositories.inventory_repo import InventoryRepository
from omnimission.repositories.store_repo import StoreRepository
from omnimission.schemas.store import StoreDetailResponse, StoreNearbyResponse, StoreResponse


class StoreService:
    """Service handling store discovery, geolocation matching, and metadata."""

    def __init__(
        self,
        store_repo: StoreRepository | None = None,
        inventory_repo: InventoryRepository | None = None,
    ) -> None:
        self.store_repo = store_repo or StoreRepository()
        self.inventory_repo = inventory_repo or InventoryRepository()

    async def find_nearby_stores(
        self,
        session: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float = 25.0,
        limit: int = 10,
    ) -> list[StoreNearbyResponse]:
        """Find nearby stores sorted by proximity, enriched with categories."""
        stores_with_distance = await self.store_repo.find_nearby(
            session=session,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            limit=limit,
        )

        results: list[StoreNearbyResponse] = []
        for store, dist in stores_with_distance:
            categories = await self.store_repo.get_store_categories(session, store.id)
            results.append(
                StoreNearbyResponse(
                    id=store.id,
                    merchant_id=store.merchant_id,
                    name=store.name,
                    address=store.address,
                    city=store.city,
                    lat=store.lat,
                    lng=store.lng,
                    phone=store.phone,
                    opening_hours=store.opening_hours,
                    is_active=store.is_active,
                    distance_km=dist,
                    open_now=True,
                    categories=categories,
                )
            )

        return results

    async def get_store_detail(
        self, session: AsyncSession, store_id: uuid.UUID
    ) -> StoreDetailResponse:
        """Fetch store by UUID and populate inventory summary."""
        store = await self.store_repo.get_by_id(session, store_id)
        if store is None or not store.is_active:
            raise NotFoundError(
                detail=f"Store with id '{store_id}' not found",
                code="STORE_NOT_FOUND",
            )

        total_skus = await self.store_repo.count_store_skus(session, store.id)
        available_aisles = await self.inventory_repo.get_distinct_aisles(session, store.id)

        return StoreDetailResponse(
            id=store.id,
            merchant_id=store.merchant_id,
            name=store.name,
            address=store.address,
            city=store.city,
            lat=store.lat,
            lng=store.lng,
            phone=store.phone,
            opening_hours=store.opening_hours,
            is_active=store.is_active,
            total_skus=total_skus,
            available_aisles=available_aisles,
        )

    async def search_stores(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 10,
    ) -> list[StoreResponse]:
        """Search stores by city or name for manual location fallback."""
        stores = await self.store_repo.search_by_text(session, query, limit)
        return [StoreResponse.model_validate(store) for store in stores]
