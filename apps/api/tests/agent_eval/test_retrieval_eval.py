"""Retrieval evaluation set with 15 golden retail queries and top-k assertions."""

import pytest
from httpx import AsyncClient

from omnimission.seed.data import (
    STORE_BLR_INDIRANAGAR,
    STORE_BLR_KORAMANGALA,
)

EVAL_BENCHMARK = [
    {"query": "eggless cake flour", "expected_substr": "Maida", "k": 3},
    {"query": "whey protein", "expected_substr": "Whey", "k": 3},
    {"query": "vegan protein", "expected_substr": "Cosmix", "k": 3},
    {"query": "travel shampoo", "expected_substr": "Pantene", "k": 3},
    {"query": "travel toothpaste", "expected_substr": "Colgate", "k": 3},
    {"query": "pocket sanitizer", "expected_substr": "Dettol", "k": 3},
    {"query": "spicy snacks", "expected_substr": "Haldiram", "k": 3},
    {"query": "party cups", "expected_substr": "Paper", "k": 3},
    {"query": "paper plates", "expected_substr": "Plates", "k": 3},
    {"query": "greek yogurt", "expected_substr": "Epigamia", "k": 3},
    {"query": "dark chocolate chips", "expected_substr": "Morde", "k": 3},
    {"query": "madagascar vanilla", "expected_substr": "Vanilla", "k": 3},
    {"query": "baking powder", "expected_substr": "Baking Powder", "k": 3},
    {"query": "condensed milk", "expected_substr": "Milkmaid", "k": 3},
    {"query": "sunscreen 50ml", "expected_substr": "Minimalist", "k": 3},
]


@pytest.mark.asyncio
@pytest.mark.parametrize("benchmark", EVAL_BENCHMARK, ids=lambda b: b["query"])
async def test_golden_retrieval_query_top_k(
    client: AsyncClient, benchmark: dict[str, str | int]
) -> None:
    """Evaluate that representative queries return expected retail SKU within top-k."""
    query = str(benchmark["query"])
    expected = str(benchmark["expected_substr"])
    k = int(benchmark["k"])

    # Search across both Indiranagar and Koramangala
    store_param = f"store_ids={STORE_BLR_INDIRANAGAR}&store_ids={STORE_BLR_KORAMANGALA}"
    resp = await client.get(
        f"/api/v1/catalog/search?q={query}&{store_param}&in_stock_only=false&limit=10"
    )
    assert resp.status_code == 200
    hits = resp.json()

    assert len(hits) > 0, f"Query '{query}' returned no results"

    top_k_names = [h["name"] for h in hits[:k]]
    matched = any(expected.lower() in name.lower() for name in top_k_names)

    assert matched, (
        f"Query '{query}' failed: expected substring '{expected}' not found in top-{k} results: {top_k_names}"
    )


@pytest.mark.asyncio
async def test_travel_size_hard_filter(client: AsyncClient) -> None:
    """Verify that is_travel_size filter strictly returns travel-sized SKUs."""
    store_param = f"store_ids={STORE_BLR_INDIRANAGAR}"
    resp = await client.get(
        f"/api/v1/catalog/search?q=toothpaste&{store_param}&is_travel_size=true"
    )
    assert resp.status_code == 200
    hits = resp.json()

    assert len(hits) >= 1
    for hit in hits:
        assert hit["is_travel_size"] is True


@pytest.mark.asyncio
async def test_dietary_tag_hard_filter(client: AsyncClient) -> None:
    """Verify that dietary_tags filter strictly restricts hits to tagged items."""
    store_param = f"store_ids={STORE_BLR_INDIRANAGAR}"
    resp = await client.get(
        f"/api/v1/catalog/search?q=flour&{store_param}&dietary_tags=gluten_free"
    )
    assert resp.status_code == 200
    hits = resp.json()

    assert len(hits) >= 1
    # Almond flour is gluten_free, maida is not
    assert "Almond" in hits[0]["name"]
    for hit in hits:
        assert "gluten_free" in hit["dietary_tags"]


@pytest.mark.asyncio
async def test_store_inventory_isolation(client: AsyncClient) -> None:
    """Verify that search only returns items belonging to selected stores."""
    resp = await client.get(f"/api/v1/catalog/search?q=butter&store_ids={STORE_BLR_INDIRANAGAR}")
    assert resp.status_code == 200
    hits = resp.json()

    assert len(hits) >= 1
    for hit in hits:
        assert hit["store_id"] == str(STORE_BLR_INDIRANAGAR)
