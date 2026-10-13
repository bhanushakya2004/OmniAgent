# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
