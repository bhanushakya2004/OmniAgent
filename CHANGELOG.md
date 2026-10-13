# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-13

### Added
- **P0 (Expanded Catalog & Multi-Corpora Knowledge Base):**
  - Expanded catalog to 358 rich SKUs across 10 retail departments and 7 physical stores (2,506 inventory rows).
  - Curated 65-document knowledge corpus across Culinary Recipes, Curated Trip Kits, House Party Guides, and Dietary Replacement Matrices.
  - Knowledge graph models `KnowledgeDoc`, `KnowledgeChunk`, `KGNode`, `KGEdge` with migrations `0005` and `0006`.
- **P1 (Google MCP Toolbox for Databases Layer):**
  - `toolbox_ro` read-only Postgres role and curated analytical views `v_store_stock_overview`, `v_aisle_traffic`, `v_daily_demand_aggregates`, `v_shrinkage_summary` (migration `0007`).
  - Google MCP Toolbox specification `infra/toolbox/tools.yaml` and `ToolboxGateway` adapter (ADR `0010`).
- **P2 (Advanced RAG v2 & GraphRAG-Lite):**
  - Structure-aware chunking (Overview, Ingredients, Instructions, Dietary).
  - Dense semantic embeddings + sparse PostgreSQL tsvector search with Reciprocal Rank Fusion ($k=60$).
  - Recursive Knowledge Graph expansion traversing `requires`, `satisfies_diet`, and `substitutes_for` edges.
  - Listwise cross-scoring reranker (ADR `0011`).
- **P3 (Unified Principal, Guest Sessions, Cart & Order Backend):**
  - Unified `Principal` domain model handling authenticated users, merchants, and anonymous guests.
  - `GuestSession`, `Cart`, `CartItem`, `Order`, `OrderItem` models with migration `0008`.
  - `CartService` supporting anonymous carts via `X-Guest-Session-ID` and atomic cart merging on login.
  - `OrderService` supporting mock checkout with multi-method payment simulation.
  - REST endpoints `/api/v1/cart`, `/api/v1/orders` (ADR `0012`).
- **P4 (Governed Agent Harness & Cart Agent):**
  - `ConciergeRouter` with 8 intent routes (`recipe`, `travel`, `party`, `cart_action`, `order_status`, `merchant_analytics`, `general_faq`, `catalog_search`).
  - `CartAgent` manipulating carts while strictly enforcing the Physical Grounding Invariant.
  - `ToolRegistry` governing permissions, side-effect classification, and token budgets.
  - `PersonalisationAgent` and `MemoryService` with REST endpoints at `/api/v1/memories` (ADR `0013`).
- **P5 (Resumable SSE Protocol over HTTP/2):**
  - `MissionEvent` model with migration `0009`.
  - Monotonic sequence IDs guaranteeing zero dropped or duplicated events.
  - `EventPersistenceService` with `Last-Event-ID` historical replay on reconnect.
  - Caddy reverse proxy configured with `flush_interval -1` and native HTTP/2 streaming (ADR `0014`).
- **P6 (Guest-First Web Experience):**
  - Client-side guest session generator and cookie persistence in `api-client.ts`.
  - Flagship `/shop` route with segmented mode toggle (`Search Catalog` vs `Ask AI`).
  - Instant catalog search with dietary chips (`Vegan`, `Eggless`, `Gluten-Free`, `High-Protein`, `Organic`, `Keto`).
  - Slide-over `CartDrawer` with quantity steppers and real-time total calculations.
  - `/checkout` with inline authentication and simulated payments (UPI, Card, NetBanking, COD).
  - `/orders/[id]` with status timeline and physical in-store aisle maps (ADR `0015`).
- **P7 (Merchant Store Analyst & Guarded NL2SQL):**
  - `SqlGuard` AST security validator using `sqlglot` (enforcing read-only SELECT, table allowlist, store scoping, statement timeout, limit clamping).
  - `ActionProposal` model with migration `0010` and `ActionProposalService` for HITL approvals.
  - `StoreAnalystAgent` and `DailyBriefingService` with `/v1/merchant/analyst/query`, `/v1/merchant/analyst/briefing`, and `/v1/merchant/proposals` (ADR `0016`).
- **P8 (Merchant Store Analyst Web Portal with Recharts):**
  - `StoreAnalystConsole` in `apps/web/src/components/merchant/store-analyst-console.tsx` featuring Daily Briefing, Recharts graphs (Bar, Line, Pie, Table), collapsible SQL viewer, and HITL approve/reject buttons (ADR `0017`).
- **P9 (Glass-Box Agent Inspector & Observability UI):**
  - Backend telemetry endpoint `GET /api/v1/missions/{id}/inspector` compiling trajectory, tool calls, grounding checks, and sequence IDs.
  - `AgentInspectorModal` in `apps/web/src/components/shopper/agent-inspector-modal.tsx` with "Inspect AI" button on `/shop` (ADR `0018`).
- **P10 (Empirical Evaluation Suite & Automated Benchmarks):**
  - Automated evaluation harness in `apps/api/src/omnimission/scripts/run_evals.py` (`make eval`).
  - Verified Hit Rate @ 5 = 1.00, MRR @ 5 = 0.90 across RAG scenarios.
  - Verified 100% Grounding Invariant adherence, 100% price accuracy, and 0 hallucinations across 20 shopper missions.
  - Verified 100% attack blocking and 0% leaks across 30 SqlGuard test cases.
  - Automated report generation in `docs/EVALUATION.md` (ADR `0019`).

## [0.1.0] - 2026-10-13

### Added
- **M0 (Monorepo & Tooling):**
  - Turborepo / monorepo structure with FastAPI async backend (`apps/api`) and Next.js 15 App Router frontend (`apps/web`).
  - Docker Compose configuration with PostgreSQL 16 and `pgvector`, `pg_trgm`, `cube`, and `earthdistance` extensions.
  - Root `Makefile`, GitHub Actions CI pipeline, and ADR `0001-monorepo-and-technology-selection.md`.
- **M1 (Backend Core & Security):**
  - Pydantic v2 settings management, structured JSON logging (`structlog`), and RFC 7807 Problem Details error handling.
  - Cryptographic user authentication with Argon2id password hashing.
  - Dual-token family system: short-lived JWT access tokens and long-lived refresh tokens stored in HttpOnly cookies with automatic reuse revocation.
  - Role-based authorization (`user` for Shoppers, `merchant` for Store Operators) and ADR `0002-jwt-and-refresh-token-strategy.md`.
- **M2 (Stores, Catalog & Proximity):**
  - SQLAlchemy 2.0 ORM models for `Store`, `Product`, and `StoreInventory`.
  - Haversine spherical distance calculation for physical store proximity searches.
  - Deterministic and idempotent seed loader seeding 4 demo accounts, 7 stores across 4 Indian metros, and 28 rich retail items.
- **M3 (Hybrid Search with Reciprocal Rank Fusion):**
  - Hexagonal `SearchBackend` port interface.
  - `PgHybridSearch` adapter fusing `pgvector` cosine similarity, PostgreSQL Full-Text Search (`tsvector`), and trigram fuzzy matching with $k=60$.
  - Comprehensive retrieval evaluation suite across 18 retail benchmark queries and ADR `0003-hybrid-search-and-rrf.md`.
- **M4 (Web Foundation & Design System):**
  - Exported OpenAPI 3.1 specification and generated strict TypeScript definitions.
  - TanStack React Query v5 client with automatic JWT token attachment and single-flight refresh queueing.
  - Zustand stores (`useAuthStore`, `useLocationStore`, `useStoreSelectionStore`).
  - Responsive landing page, split-screen `/login` with 1-click demo credential filling, and registration flows with Next.js route protection middleware (ADR `0004-openapi-types-and-middleware-auth.md`).
- **M5 (Agno Multi-Agent Orchestration & SSE):**
  - Pinned `agno==3.1.3` framework with Google Gemini models.
  - `IntentAgentRunner`, `PlannerAgentRunner`, and `SubstitutionEvaluator`.
  - Strict catalog grounding guarantee (`GroundingValidator`) enforcing 100% price and aisle authority.
  - `WayfindingService` generating monotonic in-store walking paths ($Aisle_1 \to \dots \to Aisle_N$).
  - Server-Sent Events (`/api/v1/missions/{id}/stream`) broadcasting real-time `TimelineEvent`s (ADR `0005-agno-workflow-and-grounding.md`).
- **M6 (Storage, Multimodal Vision & Voice):**
  - `StorageBackend` port and `LocalFsStorage` adapter with magic-byte validation and 10MB limits.
  - `TranscriptionProvider` port and `GeminiTranscriptionProvider` adapter supporting Hindi and English speech audio.
  - `VisionAgentRunner` extracting catalog queries from pantry item photographs (ADR `0006-storage-voice-and-vision.md`).
- **M7 (Shopper Frontend Experience):**
  - `useMissionStream` custom React hook consuming live SSE timeline traces.
  - Interactive store proximity picker with GPS locator and city shortcuts.
  - Multimodal mission composer with golden prompt chips, in-browser audio recording, and photo uploads.
  - Real-time reasoning timeline, physical grounded basket view with interactive quantity steppers and budget meter, and in-store monotonic walking checklist (ADR `0007-shopper-experience-and-sse-streaming.md`).
- **M8 (Merchant Operations Backend):**
  - `RestockTask` model with Alembic migration `0004_restock_tasks`.
  - `AnalyticsSink` port and `PgAnalytics` adapter querying active missions, grounded GMV, and neighborhood demand signals.
  - `ShelfAuditAgentRunner` using Gemini Vision to detect empty facing gaps against expected catalog inventory.
  - CSV batch inventory import with row validation and atomic error reporting (ADR `0008-merchant-operations-and-shelf-audits.md`).
- **M9 (Merchant Command Portal):**
  - Multi-store switcher with active SKU counts.
  - Interactive KPI cards for missions, grounded GMV, at-risk SKUs, and open replenishment tasks.
  - Neighborhood Demand Radar highlighting trending customer queries and substitution revenue losses.
  - High-density shelf inventory table with inline stock steppers and batch CSV modal.
  - Visual shelf audit panel and replenishment Kanban board with 1-click approval and automatic stock reconciliation upon completion (ADR `0009-merchant-portal-and-demand-radar.md`).
- **M10 & M11 (Documentation, Release & Release Tag):**
  - Production-grade architectural documentation (`ARCHITECTURE.md`, `AGENTS.md`, `DATA_MODEL.md`, `API.md`, `FRONTEND.md`, `GCP_MIGRATION.md`, `DEMO.md`).
  - Full end-to-end test verification and clean Next.js production compilation.
  - Initial stable release tagged `v0.1.0`.
