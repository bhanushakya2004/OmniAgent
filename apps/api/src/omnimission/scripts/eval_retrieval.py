"""Evaluation script benchmark for Knowledge Retrieval, Hybrid RRF, and Graph Expansion."""

import asyncio
import time
from typing import Any

from omnimission.services.knowledge_service import KnowledgeService

BENCHMARK_QUERIES = [
    {
        "query": "I want everything needed to make an eggless strawberry cake for 8 people",
        "expected_title_contains": "Strawberry Cream Cake",
    },
    {
        "query": "3-day travel to Mumbai for business meetings toiletries travel-size",
        "expected_title_contains": "Mumbai Business",
    },
    {
        "query": "gluten-free high protein dessert cake almond flour",
        "expected_title_contains": "Protein",
    },
    {
        "query": "vegan dairy replacer matrix swapping paneer and milk",
        "expected_title_contains": "Vegan Dairy Replacer",
    },
    {
        "query": "hosting a house party for 8 guests snacks and disposables",
        "expected_title_contains": "House Party",
    },
]


async def run_retrieval_benchmark() -> dict[str, Any]:
    """Execute knowledge retrieval evaluation across test scenarios."""
    knowledge_service = KnowledgeService()

    hit_at_1 = 0
    hit_at_5 = 0
    reciprocal_ranks = []
    latencies = []

    for item in BENCHMARK_QUERIES:
        t0 = time.perf_counter()
        plan = await knowledge_service.retrieve_and_plan(
            raw_query=item["query"],
            top_k=5,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        chunks = plan["retrieved_chunks"]
        expected_substr = item["expected_title_contains"].lower()
        rank = None
        for idx, chunk in enumerate(chunks, start=1):
            title = chunk.get("title", "").lower()
            text = chunk.get("chunk_text", "").lower()
            if expected_substr in title or expected_substr in text:
                rank = idx
                break

        if rank == 1:
            hit_at_1 += 1
        if rank and rank <= 5:
            hit_at_5 += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    n = len(BENCHMARK_QUERIES)
    results = {
        "benchmark_count": n,
        "hit_rate_at_1": round(hit_at_1 / n, 2),
        "hit_rate_at_5": round(hit_at_5 / n, 2),
        "mrr_at_5": round(sum(reciprocal_ranks) / n, 2),
        "mean_latency_ms": round(sum(latencies) / n, 1),
    }
    return results


if __name__ == "__main__":
    res = asyncio.run(run_retrieval_benchmark())
    print("=== RETRIEVAL BENCHMARK RESULTS ===")
    print(f"Hit Rate @ 1: {res['hit_rate_at_1']}")
    print(f"Hit Rate @ 5: {res['hit_rate_at_5']}")
    print(f"MRR @ 5:      {res['mrr_at_5']}")
    print(f"Latency:      {res['mean_latency_ms']} ms")
