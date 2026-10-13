# OmniMission AI 🛒✨
**Multimodal Social-to-Shelf & Phygital Commerce Platform**  
*Built for the Google AI Hackathon — Phase 1 (Local-First, GCP-Ready)*

---

## Overview

OmniMission AI bridges digital inspiration (social media recipes, voice commands, pantry photos) with physical store reality. Shoppers formulate goal-driven missions, which are resolved against the real-time physical inventory of local stores—locating exact aisle and shelf coordinates, proposing dietary-aligned substitutions, and optimizing multi-store budgets. Store managers gain an operational command center providing real-time demand radar, predictive stockout alerts, and vision-assisted shelf audits.

---

## Tech Stack

- **Agents:** [Agno 3.1.3](https://agno.com) + Google Gemini (`gemini-2.5-flash`, `text-embedding-004`).
- **Backend:** FastAPI (Python 3.12+ async), SQLAlchemy 2.0, PostgreSQL 16 with `pgvector` & `pg_trgm`.
- **Search Engine:** Hybrid Reciprocal Rank Fusion (pgvector cosine + full-text search + trigram).
- **Frontend:** Next.js 15 (App Router, TypeScript strict), Tailwind CSS, Radix UI, TanStack Query v5, Zustand.
- **Architecture:** Layered Hexagonal (Router → Service → Repository → DB) with abstract ports for seamless Google Cloud (Vertex AI Search, Cloud Run, Cloud Storage, BigQuery) drop-in.

---

## 5-Minute Quickstart

### Prerequisites
- Docker & Docker Compose
- `uv` (Python 3.12 package manager)
- Node.js 22+

### 1. Clone & Configure
```bash
git clone <repo-url>
cd OmniAgent
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY if testing live Gemini models
```

### 2. Start PostgreSQL + pgvector
```bash
make db
```

### 3. Run Migrations & Load Deterministic Seed Data
```bash
make migrate
make seed
```

### 4. Start Development Servers
In terminal 1 (FastAPI backend):
```bash
make dev-api
# API available at http://localhost:8000 (OpenAPI docs at http://localhost:8000/docs)
```

In terminal 2 (Next.js frontend):
```bash
make dev-web
# Web UI available at http://localhost:3000
```

---

## Demo Credentials

| Role | Email | Password | Scope |
|---|---|---|---|
| Shopper | `shopper@omnimission.ai` | `Shopper123!` | Bangalore & Mumbai shoppers |
| Merchant | `merchant@omnimission.ai` | `Merchant123!` | Manages Bangalore stores |
| Merchant 2 | `merchant2@omnimission.ai` | `Merchant123!` | Manages Mumbai stores |

---

## Documentation Links

- [Architecture & Sequence Diagrams](docs/ARCHITECTURE.md)
- [Multi-Agent System & Grounding Design](docs/AGENTS.md)
- [REST API & SSE Event Contract](docs/API.md)
- [PostgreSQL Data Model & ERD](docs/DATA_MODEL.md)
- [Frontend State & Design Tokens](docs/FRONTEND.md)
- [Google Cloud Platform Migration Runbook](docs/GCP_MIGRATION.md)
- [3-Minute Demo Script & Golden Scenarios](docs/DEMO.md)
- [Architecture Decision Records (ADRs)](docs/adr/)
