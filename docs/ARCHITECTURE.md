# OmniMission AI: System Architecture

## 1. System Overview

**OmniMission AI** is a dual-sided "phygital" commerce platform that bridges conversational digital intent with physical in-store retail execution.
- **Shoppers** complete goal-driven missions (via natural language, multi-lingual voice, or product photographs), which are decomposed by autonomous AI agents, grounded strictly in the real physical inventory of nearby stores, resolved to physical aisle/bay/shelf coordinates, added to persistent carts, and navigated with a monotonic walking path.
- **Merchants** monitor real-time neighborhood demand signals, query their store performance using guarded natural-language-to-SQL (NL2SQL), review automated daily briefings, execute multimodal shelf audits via Gemini Vision, and approve Human-in-the-Loop (HITL) restocking action proposals.

```mermaid
flowchart TB
    subgraph ClientLayer["Frontend Layer (Next.js 15 + React 19 + TypeScript)"]
        ShopperShop["Conversational Commerce (/shop)"]
        CartSlideOver["Persistent Cart Drawer & State"]
        CheckoutPage["Guest-to-User Checkout (/checkout)"]
        OrdersPage["Order Status & Aisle Route (/orders/[id])"]
        MerchantPortal["Merchant Operations & Analyst (/merchant)"]
        InspectorModal["Glass-Box Agent Inspector Modal"]
    end

    subgraph APILayer["Backend API Service (FastAPI + Async Python 3.12)"]
        direction TB
        Routers["Routers (/v1/missions, /v1/cart, /v1/orders, /v1/merchant/...)"]
        Services["Domain Services (Mission, Cart, Order, Knowledge, Analyst)"]
        Agents["Governed Agno Agent Harness (agno==3.1.3 + Gemini)"]
        ToolRegistry["ToolRegistry (Scoped Permissions & Budgets)"]
        SqlGuard["SqlGuard AST Security Engine (sqlglot)"]
    end

    subgraph ToolboxAndData["Storage & Persistence Layer"]
        PG["PostgreSQL 16 + pgvector (358 SKUs, 2,506 Inventory Rows)"]
        MCPToolbox["Google MCP Toolbox for Databases (toolbox_ro)"]
        EventStore["MissionEvent Resumable Stream Store"]
        KnowledgeGraph["Knowledge Graph (65 Docs, 192 Chunks, 265 Nodes)"]
    end

    ShopperShop -->|"Resumable SSE (Last-Event-ID)"| Routers
    CartSlideOver -->|"REST /v1/cart"| Routers
    CheckoutPage -->|"REST /v1/orders"| Routers
    OrdersPage -->|"REST /v1/orders/{id}"| Routers
    MerchantPortal -->|"REST /v1/merchant/analyst"| Routers
    InspectorModal -->|"REST /v1/missions/{id}/inspector"| Routers

    Routers --> Services
    Services --> Agents
    Agents --> ToolRegistry
    ToolRegistry --> MCPToolbox
    MCPToolbox --> PG
    Services --> SqlGuard
    SqlGuard --> PG
    Services --> EventStore
    Services --> KnowledgeGraph
```

---

## 2. Layered Backend Architecture

OmniMission AI enforces strict architectural separation of concerns. Presentation layers never perform database queries, and database ORM sessions never leak upward:

$$\text{Router Layer} \longrightarrow \text{Domain Service Layer} \longrightarrow \text{Repository / Ports} \longrightarrow \text{Database Layer}$$

1. **Router Layer (`src/omnimission/api/v1/`):**
   - Pure HTTP ingress points validating schemas (Pydantic v2), extracting unified `Principal` tokens (`get_current_principal`), asserting role permissions (`require_merchant`), and mapping exceptions to RFC 7807 Problem Details.
2. **Domain Service Layer (`src/omnimission/services/`):**
   - Encapsulates core business logic: `MissionService`, `CartService`, `OrderService`, `KnowledgeService`, `StoreAnalystService`, `ActionProposalService`, and `EventPersistenceService`.
   - Never imports FastAPI or presentation constructs.
3. **Agent & Governance Layer (`src/omnimission/agents/`):**
   - Agno (`agno==3.1.3`) agent orchestration: `ConciergeRouter`, `CartAgent`, `PersonalisationAgent`, `StoreAnalystAgent`, `MissionWorkflow`.
   - `ToolRegistry` enforces fine-grained permission scopes (`catalog:read`, `cart:write`, `store:read`, `merchant:analytics`, `knowledge:read`) and token budgets.
4. **Ports & Adapters Layer (`src/omnimission/ports/` & `src/omnimission/adapters/`):**
   - Hexagonal Architecture (Ports and Adapters) isolating cloud-shaped dependencies. Local implementations swap into Google Cloud services with zero service-layer code modifications.
5. **Database Models & Alembic (`src/omnimission/models/` & `migrations/`):**
   - Declarative SQLAlchemy 2.0 async models with strict UUID primary keys and foreign key constraints across 10 Alembic migrations.

---

## 3. Core Protocol Sequence Diagrams

### 3.1 Resumable SSE Protocol over HTTP/2

Guarantees zero lost or duplicated events across intermittent network disconnections using monotonic sequence IDs and the standard `Last-Event-ID` header.

```mermaid
sequenceDiagram
    autonumber
    actor Shopper as Client (Next.js EventSource)
    participant Caddy as Caddy Reverse Proxy (HTTP/2)
    participant API as FastAPI Backend (/missions/{id}/stream)
    participant EvSvc as EventPersistenceService
    participant PG as PostgreSQL (mission_events)

    Shopper->>Caddy: GET /api/v1/missions/{id}/stream (Accept: text/event-stream)
    Caddy->>API: Forward stream request
    API->>EvSvc: Fetch historical events (after_seq = 0)
    EvSvc->>PG: SELECT * FROM mission_events WHERE mission_id = :id ORDER BY sequence_id ASC
    PG-->>EvSvc: [Event seq:1, Event seq:2]
    API-->>Shopper: id: 1\nevent: agent_thought\ndata: {...}\n\n
    API-->>Shopper: id: 2\nevent: items_planned\ndata: {...}\n\n

    Note over Shopper, API: Network Drop / Connection Reset (Seq 2 received)

    Shopper->>Caddy: GET /api/v1/missions/{id}/stream (Header: Last-Event-ID: 2)
    Caddy->>API: Forward stream request with Last-Event-ID: 2
    API->>EvSvc: get_events_after(mission_id, after_seq=2)
    EvSvc->>PG: SELECT * FROM mission_events WHERE mission_id = :id AND sequence_id > 2 ORDER BY sequence_id ASC
    PG-->>EvSvc: [Event seq:3, Event seq:4]
    API-->>Shopper: id: 3\nevent: tool_call\ndata: {...}\n\n
    API-->>Shopper: id: 4\nevent: mission_complete\ndata: {...}\n\n
```

---

### 3.2 Governed Cart Agent & Grounding Invariant

Guarantees that every item placed in a cart is grounded in verified, in-stock physical inventory.

```mermaid
sequenceDiagram
    autonumber
    actor Shopper as Anonymous Shopper (Guest Session)
    participant Router as ConciergeRouter
    participant CartAgent as CartAgent (Agno + Gemini)
    participant Registry as ToolRegistry (Governance)
    participant Search as PgHybridSearch (RRF k=60)
    participant CartSvc as CartService
    participant PG as PostgreSQL (carts & cart_items)

    Shopper->>Router: "Add 2 packets of almond flour to my cart"
    Router->>CartAgent: Route: cart_action (Principal: Guest)
    CartAgent->>Registry: Call tool: search_store_inventory(query="almond flour")
    Registry->>Registry: Validate Permission: catalog:read (ALLOWED)
    Registry->>Search: Execute hybrid search in selected store
    Search-->>Registry: SKU: 6ab40fbc (Almond Flour, Price: ₹240, Stock: 18, Aisle: 4)
    Registry-->>CartAgent: Grounded Inventory Result

    CartAgent->>Registry: Call tool: add_to_basket(product_id="6ab40fbc", qty=2)
    Registry->>Registry: Validate Permission: cart:write (ALLOWED)
    Registry->>CartSvc: add_item(guest_session_id, product_id, quantity=2)
    CartSvc->>PG: Verify in-stock & Insert into cart_items
    PG-->>CartSvc: CartItem Persisted (Subtotal: ₹480)
    CartSvc-->>Registry: Updated Cart
    Registry-->>CartAgent: Success Response
    CartAgent-->>Shopper: "Added 2 packets of Almond Flour to your cart (Aisle 4, ₹480 total)."
```

---

### 3.3 Merchant Store Analyst & Guarded NL2SQL

Guarantees 100% defense against SQL injection, data exfiltration, and cross-store leakage, with HITL approvals for consequential store operations.

```mermaid
sequenceDiagram
    autonumber
    actor Merchant as Store Manager (Role: merchant)
    participant API as Merchant Analyst API (/v1/merchant/analyst/query)
    participant Analyst as StoreAnalystAgent (Agno + Gemini)
    participant SqlGuard as SqlGuard Security Engine (sqlglot)
    participant PG as PostgreSQL (toolbox_ro Views)
    participant PropSvc as ActionProposalService

    Merchant->>API: "Which baking items are running critically low on stock?"
    API->>Analyst: Generate analytical query for store_id: STORE_BLR_01
    Analyst-->>SqlGuard: Raw SQL: SELECT product_name, stock_level FROM v_store_stock_overview WHERE is_low_stock = true
    
    SqlGuard->>SqlGuard: 1. AST Parse (Postgres Dialect)
    SqlGuard->>SqlGuard: 2. Verify Statement == SELECT (Read-Only)
    SqlGuard->>SqlGuard: 3. Verify Table Allowlist (v_store_stock_overview: ALLOWED)
    SqlGuard->>SqlGuard: 4. Inject Store Scoping: store_id = 'STORE_BLR_01'
    SqlGuard->>SqlGuard: 5. Clamp LIMIT 100 & Timeout 3000ms
    
    SqlGuard->>PG: Execute Sanitized SQL (Role: toolbox_ro)
    PG-->>SqlGuard: Low stock rows (Almond Flour: 2 units left)
    SqlGuard-->>Analyst: Structured Query Results
    
    Analyst->>PropSvc: create_proposal(title="Restock Almond Flour", qty=25)
    PropSvc-->>Analyst: Proposal #48 created (Status: pending_approval)
    Analyst-->>Merchant: Returns analytical answer + Recharts chart + HITL Action Proposal Card
    
    Merchant->>API: POST /v1/merchant/proposals/48/approve
    API->>PropSvc: approve_proposal(id=48, principal=Merchant)
    PropSvc-->>Merchant: Restock task dispatched to store staff
```

---

### 3.4 Advanced RAG v2: Hybrid RRF & Recursive Knowledge Graph Expansion

Combines dense semantic vector retrieval with lexical keyword search and recursive Knowledge Graph traversal to guarantee complete ingredient and substitution recall.

```mermaid
sequenceDiagram
    autonumber
    actor Shopper as Shopper Query
    participant KSvc as KnowledgeService
    participant Decomp as Query Decomposition
    participant Hybrid as Hybrid Search (RRF k=60)
    participant KG as Knowledge Graph (kg_nodes & kg_edges)
    participant Rerank as Listwise Reranker

    Shopper->>KSvc: "Eggless strawberry cake for 8 people"
    KSvc->>Decomp: Extract goal ("strawberry cake"), servings (8), diet ("eggless")
    Decomp-->>KSvc: Cleaned Query Specification

    par Dense Vector Search
        KSvc->>Hybrid: pgvector cosine distance on knowledge_chunks
    and Sparse Lexical Search
        KSvc->>Hybrid: ts_rank on knowledge_chunks.tsv
    end

    Hybrid->>Hybrid: Reciprocal Rank Fusion: score = 1/(60 + r_dense) + 1/(60 + r_sparse)
    Hybrid-->>KSvc: Candidate Chunks (RRF Top 10)

    KSvc->>KG: Expand Knowledge Graph for matched recipe: "Fresh Strawberry Cake"
    KG->>KG: Traverse 'requires' edges -> [Strawberries, Flour, Curd, Baking Powder]
    KG->>KG: Traverse 'substitutes_for' edges -> [Curd replaces Egg for 'eggless' diet]
    KG-->>KSvc: Deterministic Graph Expansion Payload

    KSvc->>Rerank: Cross-score candidates with graph entities & section weighting
    Rerank-->>Shopper: Structured Plan (Hit Rate @ 5 = 1.00, MRR @ 5 = 0.90)
```

---

## 4. Hexagonal Architecture (Ports and Adapters)

To guarantee that OmniMission AI is **100% GCP-Ready**, every infrastructure concern is decoupled behind typed Python `Protocol` interfaces:

| Port Protocol | Local Adapter | GCP Target Adapter | Purpose |
| :--- | :--- | :--- | :--- |
| `SearchBackend` | `PgHybridSearch` (pgvector + FTS + RRF) | `VertexAiSearchAdapter` | Hybrid semantic vector + lexical catalog retrieval |
| `StorageBackend` | `LocalFsStorage` (magic-byte validation) | `GoogleCloudStorageAdapter` (Cloud Storage Bucket) | Multi-modal uploads (shelf images, voice audio blobs) |
| `AnalyticsSink` | `PgAnalytics` (indexed PostgreSQL aggregation) | `BigQueryAnalyticsSink` (BigQuery + Looker) | Real-time demand telemetry, GMV metrics, unmet signals |
| `TranscriptionProvider`| `GeminiTranscriptionProvider` | `GoogleCloudSpeechToTextAdapter` / Gemini Audio | Multilingual voice query transcription |
| `EmbeddingProvider` | `SentenceTransformer` / Hash Embeddings | `VertexAiTextEmbeddingAdapter` (`text-embedding-005`) | Catalog description dense vector generation |
| `DatabaseToolProvider` | `ToolboxGateway` (Local Postgres Views) | `GoogleMcpToolboxAdapter` (AlloyDB / Cloud SQL) | Parameterised, read-only database tools |
