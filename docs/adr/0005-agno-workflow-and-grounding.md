# ADR 0005: Agno Multi-Agent Workflow, SSE Streaming, and Catalog Grounding

## Status
Accepted

## Context
Goal-driven retail missions require complex multi-step reasoning:
1. Deconstructing ambiguous or multilingual shopper queries into discrete constraints (dietary, travel-size, budget, headcount).
2. Expanding abstract objectives into concrete grocery and retail shopping lists.
3. Grounding candidate items against real physical store inventory.
4. Evaluating intelligent substitutions when primary SKUs are out of stock.
5. Emitting real-time progress events to the shopper UI without freezing during long-running reasoning.
6. Generating monotonic walking paths through store aisles.

Standard LLM solutions suffer from two fatal failure modes in retail:
- **Hallucinations:** Inventing fictional products, out-of-stock items, fabricated prices, or non-existent aisle locations.
- **Black-box latency:** Users waiting 5–15 seconds with no feedback or transparency into reasoning.

## Decision
1. **Agno Framework Orchestration:**
   We adopted the Agno multi-agent framework (pinned strictly to version `3.1.3`) paired with Google Gemini models (`gemini-2.0-flash`). Agno provides structured output enforcement via Pydantic schemas (`output_schema`), explicit role decomposition, and modular agent execution.
2. **Decomposed Agent Graph:**
   - **Intent & Constraint Agent:** Extracts mission goal type, budget limit, dietary tags, travel-size requirements, and target headcount.
   - **Mission Planner Agent:** Expands intent into concrete item labels, categories, and estimated quantities.
   - **Catalog Search Integration:** Queries physical inventory across the shopper's selected stores using the hybrid RRF engine (`PgHybridSearch`).
   - **Substitution Evaluator:** When primary candidates are out of stock, evaluates in-stock alternatives adhering to dietary constraints and brand tier.
   - **Grounding Validator:** A non-negotiable deterministic post-processing layer that cross-references all candidate basket items against verified SQL tool results. Hallucinated product IDs or prices are rejected, and official database unit prices, aisle, bay, and shelf coordinates are enforced as the single source of truth.
   - **Wayfinding Service:** Sorts basket items by store, aisle ascending, bay ascending, and shelf ascending, consolidating multi-item picks into monotonic walking waypoints.
3. **SSE Real-Time Event Streaming:**
   The workflow streams fine-grained timeline events (`parsing_intent`, `intent_parsed`, `planning_items`, `items_planned`, `searching_catalog`, `catalog_searched`, `optimizing_basket`, `complete`) over HTTP Server-Sent Events (`text/event-stream` using `sse-starlette`).
4. **Execution Traces in PostgreSQL:**
   Each reasoning step, along with agent name, prompt inputs, structured outputs, and latency in milliseconds, is persisted to `mission_runs` in PostgreSQL.

## Consequences
- 100% catalog authority: Zero price, SKU, or aisle hallucinations.
- Responsive, engaging shopper experience with animated agent reasoning timeline.
- Complete auditability and replayability of agent decisions for merchants and judges.
