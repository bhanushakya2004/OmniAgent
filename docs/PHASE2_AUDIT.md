# Phase 2 Technical Audit & Gap Analysis

**Date:** October 13, 2026  
**Auditor:** Senior AI/ML & Staff Engineer  
**Baseline Version:** `v0.1.0` (Git commit `eeb0ce4`)  
**Test Baseline:** 47 passing tests across unit, integration, and retrieval-eval suites.

---

## 1. What Exists in Phase 1 (v0.1.0)

### 1.1 Multi-Agent Engine
- **Framework:** `agno==3.1.3` pinned in `apps/api/pyproject.toml`.
- **Agents:**
  - `IntentAgentRunner`: Parses input into `MissionIntent` (category, headcount, budget ceiling, dietary restrictions, travel size tag).
  - `PlannerAgentRunner`: Decomposes goal into discrete ingredient/item categories (`NeededItemList`).
  - `SubstitutionEvaluator`: Resolves out-of-stock items with dietary and price sanity checks.
  - `GroundingValidator`: Strips all LLM hallucinations by looking up price and aisle coordinates from PostgreSQL authority.
  - `WayfindingService`: Computes monotonic aisle-by-aisle traversal sequence ($Aisle_1 \to \dots \to Aisle_N$).
  - `VisionAgentRunner`: Calls Gemini Vision to extract catalog search queries from user-submitted photos.
  - `ShelfAuditAgentRunner`: Calls Gemini Vision with expected inventory to detect shelf facing gaps and auto-draft replenishment tasks.
- **Workflow Pipeline:** `MissionWorkflow` orchestrates the pipeline and yields `TimelineEvent`s.
- **Fallback Architecture:** Resilient offline fallback algorithms when `GOOGLE_API_KEY` is omitted or network calls fail.

### 1.2 SSE Contract
- Endpoint: `GET /api/v1/missions/{id}/stream`.
- Protocol: FastAPI `StreamingResponse` over HTTP/1.1 yielding `data: <JSON TimelineEvent>\n\n`.
- Events: `intent_decomposed`, `plan_generated`, `items_grounded`, `substitutions_evaluated`, `route_calculated`, `mission_completed`.
- Client hook: `useMissionStream` consumes via native `EventSource`.

### 1.3 Retrieval & Search Adapters
- `SearchBackend` port implemented by `PgHybridSearch`:
  - Reciprocal Rank Fusion (RRF, $k=60$) combining:
    1. Dense cosine vector similarity (`pgvector` 768-dim embeddings).
    2. Full-Text Search (`tsvector` with English dictionary on `products.tsv`).
    3. Trigram fuzzy lexical similarity (`pg_trgm` on `name` and `brand`).
- Retrieval benchmark: 18 test queries in `tests/agent_eval/test_retrieval_eval.py`.

### 1.4 Data Models & Persistence
- SQLAlchemy 2.0 async ORM models:
  - `User`, `RefreshToken` (token family reuse revocation)
  - `Store`, `Product`, `StoreInventory`
  - `Mission`, `MissionItem`, `MissionRun`
  - `RestockTask`
- PostgreSQL 16 extensions: `uuid-ossp`, `vector`, `pg_trgm`, `cube`, `earthdistance`.
- 4 Alembic migrations (`0001` through `0004`).

### 1.5 Routes & Presentation Surface
- **FastAPI Endpoints:**
  - `/api/v1/auth`: `login`, `register`, `refresh`, `logout`, `me`
  - `/api/v1/stores`: `list`, `nearby`, `detail`
  - `/api/v1/catalog`: `search`
  - `/api/v1/missions`: `create`, `stream`, `detail`, `item quantity patch`, `history`
  - `/api/v1/uploads`, `/api/v1/voice/transcribe`, `/api/v1/vision/analyze`
  - `/api/v1/merchant`: `stores`, `inventory`, `inventory/import`, `analytics/overview`, `analytics/demand`, `shelf-audit`, `restock-tasks`
- **Next.js Web Routes:**
  - `/` (Landing page)
  - `/login`, `/register`
  - `/app` (Single Shopper Workspace containing store picker, composer, timeline, basket, route)
  - `/merchant` (Single Merchant Operations Portal with KPI cards, demand radar, inventory, audit, tasks)

---

## 2. Deviations from Target & Architectural Gaps

| Area | Current Phase 1 State | Target Phase 2 Requirement | Severity / Gap |
| :--- | :--- | :--- | :--- |
| **Catalog Depth** | ~28 SKUs in `seed/data.py` | 300–500 SKUs across Baking, Dairy, Staples, Snacks, Party, Travel-Size, Personal Care, Household | **Critical:** RAG recall and substitution diversity require realistic catalog density. |
| **Knowledge Base** | Zero authored RAG corpora; planner relies on generic LLM recipe prompts | 60–100 structured recipe, trip kit, dietary rule, and household guide documents in pgvector | **High:** RAG-first planning requires grounded recipe knowledge. |
| **Database Tools** | Direct SQLAlchemy queries executed by service methods | Google MCP Toolbox for Databases (`mcp-toolbox`) with read-only parameterised tools & views | **High:** Agent tool layer must be cloud-portable via Google's MCP Toolbox. |
| **Commerce Flow** | No guest shopping; requires login before creating a mission; no cart or checkout | Unauthenticated guest browsing & "Ask AI", persistent cart, guest-to-user merge, checkout gate | **Critical:** Core hackathon product outcome is guest conversational commerce. |
| **Streaming Protocol** | Bare `EventSource` over HTTP/1.1; no event persistence; no reconnect/replay | Typed, resumable SSE protocol over HTTP/2 with Caddy/Hypercorn TLS, `Last-Event-ID` resume | **High:** Streaming resilience without lost or duplicated events. |
| **Merchant Analytics** | Static SQL aggregation in `PgAnalytics` | Guarded NL2SQL Store Analyst with `sqlglot` AST validation, RLS tenant isolation, self-repair | **Critical:** Flagship AI feature for merchants. |
| **Agent Harness** | Fixed sequential workflow script | Governed Concierge Router, Tool Registry, Scoped parameter binding, budgets, guardrails | **High:** Real agent harness instead of prompt glue. |
| **Observability** | Standard JSON logging | Glass-box Agent Inspector UI displaying tool calls, retrieved chunks, SQL AST, and graph hops | **High:** Key differentiator for hackathon demo. |
| **Routing Granularity**| Monolithic `/app` and `/merchant` pages | Granular shopper (`/shop`, `/shop/mission/[id]`, `/cart`, `/checkout`, `/orders`) and merchant routes | **Medium:** Navigation and bookmarking UX. |
| **Model Config** | Hard-coded model strings in agent files | Environment-driven configuration defaulting to current Google Gemini models (`gemini-2.5-flash`) | **Medium:** Must conform to current Google model lineup. |

---

## 3. Plan of Action for Phase 2 (P0 - P11)

1. **P0 (Audit & Data Expansion):**
   - Author 300–500 realistic Indian retail SKUs in `omnimission.seed.data_expanded`.
   - Author 60–100 structured knowledge base docs (recipes, travel kits, dietary guidelines, substitution matrices).
   - Create baseline eval harness in `tests/agent_eval/`.
2. **P1 (Google MCP Toolbox Layer):**
   - Configure `infra/toolbox/tools.yaml` with parameterised read-only queries on PostgreSQL views.
   - Set up `toolbox_ro` database user and Docker Compose service.
   - Create `ToolboxGateway` in `adapters/` implementing `DataToolPort` with Agno `MCPTools`.
3. **P2 (Advanced RAG v2 & GraphRAG-Lite):**
   - Idempotent ingestion pipeline (`make ingest`).
   - Query decomposition, dense+sparse+trigram RRF, listwise LLM reranking port.
   - Postgres-native Knowledge Graph (`kg_nodes`, `kg_edges`) with recursive CTE traversals.
4. **P3 (Guest Sessions, Principal, Cart & Order Backend):**
   - `GuestSession`, `Cart`, `CartItem`, `Order`, `OrderItem`, `PaymentSimulated` models & Alembic migration.
   - Unified `Principal` FastAPI dependency (`guest`, `user`, `merchant`).
   - Guest cart creation, price snapshots, cart merge upon login, and transactional checkout with row locking.
5. **P4 (Governed Agent Harness):**
   - Concierge Router classifying intent (`browse`, `mission`, `cart_op`, `analyst`, `out_of_scope`).
   - Tool Registry with side-effect levels and immutable scope binding (`store_ids`, `principal_id`).
   - Upgraded `MissionPlanner` (Recipe-RAG first), `CartAgent` (typed cart operations), and `PersonalisationAgent`.
6. **P5 (Resumable Streaming over HTTP/2):**
   - Monotonic SSE event protocol persisted in `mission_events`.
   - Reconnect handling with `Last-Event-ID`.
   - Caddy reverse-proxy service in Docker Compose for local HTTP/2 TLS termination.
7. **P6 (Guest-First Web Experience):**
   - `/shop` with Search ⇄ Ask AI toggle.
   - Slide-over live cart drawer with aisle badges, substitutions, and graph suggestions.
   - `/checkout`, demo payment simulator, and `/orders/[id]` confirmation.
8. **P7 (Merchant Intelligence & Guarded NL2SQL):**
   - Curated `v_merchant_*` views with Postgres RLS (`SET LOCAL app.store_ids`).
   - `SqlGuard` AST parser with `sqlglot` (single SELECT, view allowlist, timeout, limit injection).
   - Store Analyst agent with metric-first resolution, NL2SQL generation, error self-repair, and chart output.
   - Demand forecasting tool, Merchandising Advisor, and Daily Briefing generation.
9. **P8 (Merchant Assistant Web):**
   - Dedicated `/merchant/assistant` chat with Recharts, SQL drawer, and assumptions.
   - Split routes: `/merchant/orders`, `/merchant/inventory`, `/merchant/shelf-audit`.
10. **P9 (Glass-Box Agent Inspector):**
    - Live inspector drawer displaying tool calls, retrieved chunks, RRF/reranker scores, SQL AST, and latency.
11. **P10 (Evals & Hardening):**
    - Quantitative evaluation suite: RAG Recall@5/10, NL2SQL accuracy, safety adversarial suite, 100% groundedness test.
12. **P11 (Release v0.2.0):**
    - Documentation deliverables, judge script, CHANGELOG update, git release tag `v0.2.0`.
