"""Empirical RAG Ablation and Evaluation Suite for Knowledge Retrieval & Graph Expansion."""

import pytest

from omnimission.services.knowledge_service import KnowledgeService

BENCHMARK_CASES = [
    {
        "query": "I want everything needed to make an eggless strawberry cake for 8 people",
        "expected_title_contains": "Strawberry Cream Cake",
        "expected_dietary": "eggless",
        "expected_ingredients": ["Strawberries", "Flour", "Curd", "Sugar"],
    },
    {
        "query": "3-day travel to Mumbai for business meetings toiletries travel-size",
        "expected_title_contains": "Mumbai Business",
        "expected_dietary": None,
        "expected_ingredients": ["Toothpaste", "Shampoo", "Sanitizer"],
    },
    {
        "query": "gluten-free high protein dessert cake almond flour",
        "expected_title_contains": "Protein",
        "expected_dietary": "gluten_free",
        "expected_ingredients": ["Almond Flour"],
    },
    {
        "query": "vegan dairy replacer matrix swapping paneer and milk",
        "expected_title_contains": "Vegan Dairy Replacer",
        "expected_dietary": "vegan",
        "expected_ingredients": [],
    },
    {
        "query": "hosting a house party for 8 guests snacks and disposables",
        "expected_title_contains": "House Party",
        "expected_dietary": None,
        "expected_ingredients": ["Plates", "Cups"],
    },
]


@pytest.fixture
def knowledge_service() -> KnowledgeService:
    """Fixture providing initialized KnowledgeService."""
    return KnowledgeService()


@pytest.mark.asyncio
async def test_rag_ablation_hit_rate_and_mrr(knowledge_service: KnowledgeService) -> None:
    """Evaluate Hit Rate @ 5 and MRR @ 5 across benchmark knowledge queries."""
    hits_at_1 = 0
    hits_at_5 = 0
    reciprocal_ranks: list[float] = []

    for case in BENCHMARK_CASES:
        query = case["query"]
        expected_substr = case["expected_title_contains"].lower()

        plan = await knowledge_service.retrieve_and_plan(query, top_k=5)
        chunks = plan["retrieved_chunks"]

        rank = None
        for idx, chunk in enumerate(chunks, start=1):
            title = chunk.get("title", "").lower()
            text = chunk.get("chunk_text", "").lower()
            if expected_substr in title or expected_substr in text:
                rank = idx
                break

        if rank is not None:
            hits_at_5 += 1
            reciprocal_ranks.append(1.0 / rank)
            if rank == 1:
                hits_at_1 += 1
        else:
            reciprocal_ranks.append(0.0)

    total = len(BENCHMARK_CASES)
    hit_rate_at_1 = hits_at_1 / total
    hit_rate_at_5 = hits_at_5 / total
    mrr_at_5 = sum(reciprocal_ranks) / total

    print(f"\nRAG Benchmark Results (N={total}):")
    print(f"  Hit Rate @ 1: {hit_rate_at_1:.2f}")
    print(f"  Hit Rate @ 5: {hit_rate_at_5:.2f}")
    print(f"  MRR @ 5:      {mrr_at_5:.2f}")

    assert hit_rate_at_5 >= 0.8, f"Hit Rate @ 5 ({hit_rate_at_5}) below threshold 0.8"
    assert mrr_at_5 >= 0.7, f"MRR @ 5 ({mrr_at_5}) below threshold 0.7"


@pytest.mark.asyncio
async def test_query_decomposition(knowledge_service: KnowledgeService) -> None:
    """Verify compound query correctly extracts servings, dietary tags, and goal."""
    res = knowledge_service.decompose_query(
        "I want everything needed to make an eggless strawberry cake for 8 people"
    )
    assert res["servings"] == 8
    assert "eggless" in res["dietary_tags"]
    assert "strawberry cake" in res["goal"].lower()


@pytest.mark.asyncio
async def test_knowledge_graph_expansion(knowledge_service: KnowledgeService) -> None:
    """Verify Knowledge Graph expansion retrieves structured ingredients and dietary relations."""
    plan = await knowledge_service.retrieve_and_plan(
        "eggless strawberry cake for 8 people", top_k=3
    )

    graph_data = plan["graph_expansion"]
    assert len(graph_data["ingredients"]) >= 3
    # Check fresh strawberries or flour in ingredients
    ing_names = [i["name"].lower() for i in graph_data["ingredients"]]
    assert any("strawberr" in name or "flour" in name or "maida" in name for name in ing_names)
    assert "eggless" in graph_data["diets"]
