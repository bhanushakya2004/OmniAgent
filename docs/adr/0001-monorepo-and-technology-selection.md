# ADR 0001: Monorepo Architecture and Technology Selection

## Status
Accepted

## Context
OmniMission AI requires both an asynchronous backend service capable of running complex multi-agent workflows with low-latency catalog retrieval, and a responsive web application tailored for two distinct personas: mobile-first shoppers and desktop-first retail store operators. We need strong type-safety, rapid local development without cloud lock-in for Phase 1, and a zero-drift contract between the backend API and frontend clients.

## Decision
1. **Monorepo Structure:** We adopt a single Git repository containing `apps/api` (FastAPI), `apps/web` (Next.js), `infra/` (Docker assets), and `docs/`.
2. **Backend Runtime & Tooling:** Python 3.12+ managed by `uv`. `uv` delivers deterministic virtual environments, sub-second dependency resolution, and native lockfile support.
3. **Backend Framework:** FastAPI with SQLAlchemy 2.0 (async engine using `psycopg` 3) and Pydantic v2. This combination provides native async I/O, automatic OpenAPI 3.1 specification generation, and high serialization throughput.
4. **Agent Framework:** Agno pinned to `3.1.3` integrating Google Gemini. Agno provides native support for structured output (`output_schema`), agent workflows, tool calling, and PostgreSQL session persistence.
5. **Database & Search:** PostgreSQL 16 with `pgvector` and `pg_trgm`. In Phase 1, candidate search combines vector cosine similarity with full-text search and trigram matching via Reciprocal Rank Fusion (RRF).
6. **Frontend Framework:** Next.js 15 (App Router) with TypeScript strict mode, Tailwind CSS, Radix UI primitives, TanStack Query v5 for server state, and Zustand for client state.
7. **Type Contract:** TypeScript types are generated directly from the FastAPI OpenAPI schema via `openapi-typescript`, ensuring frontend and backend contracts never drift.

## Consequences
- Single commit history spans both frontend and backend changes.
- Eliminates cloud dependency during local Phase 1 development while preserving clean drop-in interfaces (Ports & Adapters) for Phase 2 GCP deployment.
- High developer ergonomics with `uv` and `docker-compose`.
