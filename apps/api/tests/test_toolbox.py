"""Unit and integration tests for Google MCP Toolbox gateway and database views."""

import pytest

from omnimission.adapters.toolbox_gateway import ToolboxGateway
from omnimission.seed.data import STORE_BLR_INDIRANAGAR


@pytest.fixture
def gateway() -> ToolboxGateway:
    """Fixture providing ToolboxGateway instance connected to test DB."""
    return ToolboxGateway()


@pytest.mark.asyncio
async def test_search_store_inventory(gateway: ToolboxGateway) -> None:
    """Verify search_store_inventory returns in-stock products with aisle coordinates."""
    results = await gateway.search_store_inventory(
        store_id=STORE_BLR_INDIRANAGAR,
        query="strawberry",
        limit=5,
    )
    assert len(results) >= 1
    hit = results[0]
    assert "strawberr" in hit["product_name"].lower()
    assert hit["stock_qty"] > 0
    assert hit["price"] > 0
    assert hit["aisle"] is not None
    assert hit["bay"] is not None
    assert hit["shelf"] is not None


@pytest.mark.asyncio
async def test_search_store_inventory_limit_clamping(gateway: ToolboxGateway) -> None:
    """Verify limit parameter is clamped between 1 and 50."""
    results = await gateway.search_store_inventory(
        store_id=STORE_BLR_INDIRANAGAR,
        query="fresh",
        limit=2,
    )
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_get_product_location(gateway: ToolboxGateway) -> None:
    """Verify physical aisle and shelf lookup by SKU code."""
    # First find an item to get its SKU
    items = await gateway.search_store_inventory(
        store_id=STORE_BLR_INDIRANAGAR,
        query="milk",
        limit=1,
    )
    assert len(items) >= 1
    sku = items[0]["sku"]

    location = await gateway.get_product_location(
        store_id=STORE_BLR_INDIRANAGAR,
        sku=sku,
    )
    assert location is not None
    assert location["sku"] == sku
    assert location["aisle"] >= 1
    assert location["bay"] >= 1
    assert location["shelf"] >= 1


@pytest.mark.asyncio
async def test_check_stock_levels(gateway: ToolboxGateway) -> None:
    """Verify live stock quantity check for product ID."""
    items = await gateway.search_store_inventory(
        store_id=STORE_BLR_INDIRANAGAR,
        query="sugar",
        limit=1,
    )
    assert len(items) >= 1
    prod_id = items[0]["product_id"]

    stock_info = await gateway.check_stock_levels(
        store_id=STORE_BLR_INDIRANAGAR,
        product_id=prod_id,
    )
    assert stock_info is not None
    assert stock_info["product_id"] == prod_id
    assert stock_info["stock_qty"] >= 0
    assert stock_info["price"] > 0


@pytest.mark.asyncio
async def test_get_dietary_substitutes(gateway: ToolboxGateway) -> None:
    """Verify dietary substitutes query filters correctly by dietary_tag."""
    substitutes = await gateway.get_dietary_substitutes(
        store_id=STORE_BLR_INDIRANAGAR,
        category="Flours",
        dietary_tag="gluten_free",
        limit=5,
    )
    assert len(substitutes) >= 1
    for item in substitutes:
        assert "gluten_free" in item["dietary_tags"]
        assert item["stock_qty"] > 0


@pytest.mark.asyncio
async def test_get_store_details(gateway: ToolboxGateway) -> None:
    """Verify store metadata lookup returns address and active flag."""
    store = await gateway.get_store_details(STORE_BLR_INDIRANAGAR)
    assert store is not None
    assert "Indiranagar" in store["store_name"]
    assert store["city"] == "Bengaluru"
    assert store["is_active"] is True


@pytest.mark.asyncio
async def test_find_nearby_stores(gateway: ToolboxGateway) -> None:
    """Verify geographic proximity query returns closest store first."""
    # Near Indiranagar 100ft road
    stores = await gateway.find_nearby_stores(
        lat=12.9719,
        lng=77.6412,
        radius_km=25.0,
    )
    assert len(stores) >= 2
    assert "Indiranagar" in stores[0]["store_name"]
    assert stores[0]["distance_km"] < 1.0


@pytest.mark.asyncio
async def test_agno_tool_wrappers(gateway: ToolboxGateway) -> None:
    """Verify Agno agent tool functions are properly callable with string arguments."""
    tools = gateway.get_agno_tools()
    assert len(tools) == 4

    search_fn, locate_fn, verify_fn, sub_fn = tools

    # Test calling search_fn with string store UUID
    res = await search_fn(str(STORE_BLR_INDIRANAGAR), "chai", 3)
    assert isinstance(res, list)
    assert len(res) >= 1
    assert "sku" in res[0]
