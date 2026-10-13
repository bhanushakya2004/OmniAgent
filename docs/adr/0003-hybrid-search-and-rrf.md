# ADR 0003: Hybrid Search and Reciprocal Rank Fusion (RRF) Architecture

## Status
Accepted

## Context
Goal-driven shopping missions require matching conversational, descriptive customer intents (*e.g., "high protein flour for eggless cake"*, *"pocket sanitizer"*, *"refreshing mixer for mocktails"*) against physical store inventory records. Pure lexical matching fails on semantic synonyms; pure vector search fails on exact brand names, SKUs, and short keywords; and neither alone can respect physical store stock and dietary constraints without hallucinations.

## Decision
1. **Three-Stream Candidate Retrieval:**
   - **Dense Semantic Stream:** Gemini dense embeddings (`text-embedding-004`, 768 dimensions) with cosine distance (`<=>`) via PostgreSQL `pgvector`.
   - **Full-Text Search (FTS) Stream:** PostgreSQL `tsvector` with `plainto_tsquery('english', ...)` and `ts_rank` scoring.
   - **Fuzzy Trigram Stream:** `pg_trgm` extension computing similarity against product name and brand for typo tolerance.
2. **Score Normalization via Reciprocal Rank Fusion (RRF):**
   Candidate ranks from each stream are merged using the RRF formula with smoothing constant $k = 60$:
   $$RRF\_Score(d) = \sum_{m \in \{dense, fts, trgm\}} \frac{1}{60 + rank_m(d)}$$
   This eliminates differences in score scales between cosine distance, BM25/ts_rank, and trigram percentages.
3. **Deterministic Hard Filters in SQL:**
   Crucially, store selection (`store_id IN (...)`), in-stock constraints (`stock_qty > 0`), dietary tags (`dietary_tags @> ...`), and travel-size specifications (`is_travel_size = ...`) are enforced strictly at the database layer, guaranteeing zero hallucinated items or out-of-store SKUs.
4. **Ports and Adapters Abstraction:**
   The search system exposes a `SearchBackend` port implemented locally by `PgHybridSearch`. In Phase 2, this can be swapped with a `VertexSearchBackend` connecting to Google Vertex AI Search with zero changes to caller services or agents.

## Consequences
- High precision on brand names and typos combined with semantic recall on conceptual queries.
- Strict grounding guarantee: products, prices, stock quantities, and aisle coordinates originate exclusively from physical inventory tables.
- Portable architecture ready for Google Cloud Vertex AI Search migration.
