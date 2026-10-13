"""Unit and integration tests for store proximity and catalog discovery."""

import uuid

import pytest
from httpx import AsyncClient

from omnimission.seed.data import STORE_BLR_INDIRANAGAR


@pytest.mark.asyncio
async def test_get_nearby_stores_sorted_by_proximity(client: AsyncClient) -> None:
    """Test proximity query from Indiranagar coordinates returns closest stores in order."""
    # Near Indiranagar 100ft road
    resp = await client.get("/api/v1/stores/nearby?lat=12.9719&lng=77.6412&radius_km=30")
    assert resp.status_code == 200
    stores = resp.json()

    assert len(stores) >= 3
    # First store should be Indiranagar (closest)
    assert "Indiranagar" in stores[0]["name"]
    assert stores[0]["distance_km"] < 1.0
    assert len(stores[0]["categories"]) > 0

    # Distances must be strictly non-decreasing
    distances = [s["distance_km"] for s in stores]
    assert distances == sorted(distances)


@pytest.mark.asyncio
async def test_get_store_detail_by_id(client: AsyncClient) -> None:
    """Test store lookup by UUID returns inventory stats and aisle list."""
    resp = await client.get(f"/api/v1/stores/{STORE_BLR_INDIRANAGAR}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "OmniMart Indiranagar 100ft Road"
    assert data["city"] == "Bengaluru"
    assert data["total_skus"] >= 20
    assert len(data["available_aisles"]) >= 3


@pytest.mark.asyncio
async def test_get_store_not_found(client: AsyncClient) -> None:
    """Test invalid store UUID returns RFC 7807 404."""
    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/stores/{random_id}")
    assert resp.status_code == 404
    error = resp.json()
    assert error["code"] == "STORE_NOT_FOUND"
    assert error["status"] == 404


@pytest.mark.asyncio
async def test_search_stores_text_fallback(client: AsyncClient) -> None:
    """Test manual search fallback by locality or city name."""
    resp = await client.get("/api/v1/stores/search?q=Bandra")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert "Bandra" in results[0]["name"]
    assert results[0]["city"] == "Mumbai"
