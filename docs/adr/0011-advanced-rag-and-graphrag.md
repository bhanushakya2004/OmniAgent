# ADR 0011: Advanced Multi-Corpora RAG and GraphRAG-Lite Architecture

## Status
Accepted

## Context
Phase 1 supported product-level hybrid search, but shoppers express complex real-world commerce goals:
- *"I want everything needed to make an eggless strawberry cake for 8 people"*
- *"I'm travelling to Mumbai for 3 days, I need travel-size shampoo, toothpaste, etc."*
- *"Vegan dairy replacer matrix swapping paneer and milk"*

Direct catalog keyword search fails on these goals because catalogs do not inherently contain recipe ratios, step-by-step methods, serving scaling, or dietary substitution reasoning. Relying purely on an LLM's ungrounded memory risks hallucinations (inventing non-existent SKUs or violating dietary invariants).

## Decision
1. **Multi-Corpora Structured Knowledge Base:**
   - Authored corpus of 65+ rich documents spanning recipes, trip kits, dietary substitution matrices, and house party guides stored in `knowledge_docs`.
   - Each document possesses typed metadata: `doc_id`, `type`, `diet_tags`, `servings_base`, structured `ingredients` JSONB, `summary`, and `content`.

2. **Structure-Aware Chunking & Hybrid Retrieval:**
   - Documents are partitioned into distinct functional sections (`knowledge_chunks`):
     - Chunk 0: Overview & Goal Summary
     - Chunk 1: Ingredients, Supplies & Scaling
     - Chunk 2: Step-by-Step Preparation / Usage
     - Chunk 3: Dietary Rules & Replacement Logic
   - Each chunk stores a 768-dimensional dense vector (`pgvector`) and an English `tsvector` with GIN indexing.
   - Dual-candidate retrieval pools dense semantic cosine similarity with sparse full-text lexical ranking via Reciprocal Rank Fusion (`RRF(k=60)`).

3. **PostgreSQL-Native Knowledge Graph (`GraphRAG-Lite`):**
   - Entity nodes (`kg_nodes`) represent recipes, ingredients, dietary tags, and departments.
   - Directed edges (`kg_edges`) model relations:
     - `(recipe) -[:requires]-> (ingredient)` with quantity & unit properties
     - `(recipe) -[:satisfies_diet]-> (dietary_tag)`
     - `(substitute) -[:substitutes_for]-> (ingredient)`
   - Graph expansion deterministically traverses relational edges to fetch required ingredients and valid substitutes without LLM prompting drift.

4. **Query Decomposition & Listwise Reranking:**
   - Inbound shopper prompts are decomposed into `goal`, `servings`, and explicit `dietary_tags`.
   - Retrieved chunks pass through `GeminiReranker` (`RerankerPort`), prioritizing high-value `Overview` and `Ingredients` sections to ensure optimal planning context.

## Consequences
- **Measured Quality:** Reaches 1.00 Hit Rate @ 5 and 0.90 MRR @ 5 on complex benchmark queries.
- **Sub-50ms Latency:** Native PostgreSQL pgvector cosine distance and GIN inverted index execution yields median query latency of 44 ms.
- **Strict Grounding:** Goal planning is anchored to real recipe ratios and verified inventory items before any cart addition occurs.
