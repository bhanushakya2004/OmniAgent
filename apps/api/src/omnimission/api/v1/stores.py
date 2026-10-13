"""Stores API router for shopper discovery and manual search fallback."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.db.session import get_db_session
from omnimission.schemas.store import StoreDetailResponse, StoreNearbyResponse, StoreResponse
from omnimission.services.store_service import StoreService

router = APIRouter(prefix="/stores", tags=["Stores"])


def get_store_service() -> StoreService:
    """Dependency provider for StoreService."""
    return StoreService()


@router.get(
    "/nearby",
    response_model=list[StoreNearbyResponse],
    summary="Find nearby physical stores",
)
async def get_nearby_stores(
    lat: Annotated[float, Query(ge=-90.0, le=90.0, description="Shopper latitude")],
    lng: Annotated[float, Query(ge=-180.0, le=180.0, description="Shopper longitude")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    store_service: Annotated[StoreService, Depends(get_store_service)],
    radius_km: Annotated[float, Query(gt=0, le=100.0)] = 25.0,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[StoreNearbyResponse]:
    """Retrieve nearby stores sorted by proximity for shopper mission selection."""
    return await store_service.find_nearby_stores(
        session=session,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
    )


@router.get(
    "/search",
    response_model=list[StoreResponse],
    summary="Search stores by city or name",
)
async def search_stores(
    q: Annotated[
        str, Query(min_length=1, description="Search term (city, locality, or store name)")
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    store_service: Annotated[StoreService, Depends(get_store_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[StoreResponse]:
    """Fallback store search when geolocation permission is denied."""
    return await store_service.search_stores(
        session=session,
        query=q,
        limit=limit,
    )


@router.get(
    "/{store_id}",
    response_model=StoreDetailResponse,
    summary="Get store details by UUID",
)
async def get_store(
    store_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    store_service: Annotated[StoreService, Depends(get_store_service)],
) -> StoreDetailResponse:
    """Retrieve comprehensive store metadata, aisles, and SKU counts."""
    return await store_service.get_store_detail(session=session, store_id=store_id)
