# ADR 0009: Merchant Command Portal: Store Control, Demand Radar, and Shelf Audits

## Status
Accepted

## Context
Physical retail store operators require a dedicated, high-performance web console to oversee store inventory, understand neighborhood customer demand velocity, and autonomously manage physical shelf replenishment:
1. **Multi-Store Management:** Seamless store switcher across registered physical branches with immediate overview of active SKUs.
2. **Operational KPIs:** At-a-glance visibility into active conversational missions, grounded GMV conversions, stockout risk SKUs, and open restock work orders.
3. **Neighborhood Demand Radar:** Direct telemetry showing real-time customer search queries, trending velocity scores, and out-of-stock substitution frequencies.
4. **Interactive Inventory Control:** Live SKU table with fast search, aisle/bay/shelf coordinates, status badges (`In Stock`, `Low Stock`, `Out of Stock`), inline `+` / `-` stock adjustments, and batch CSV upload with atomic row-level validation.
5. **AI Vision Shelf Audit & Restock Workflows:** Photo dropzone triggering Gemini Vision audits on physical aisles, visualizing facing discrepancies, and managing the restock task lifecycle with automatic inventory replenishment on completion.

## Decision
1. **Next.js 15 App Router & Strict TypeScript Architecture:**
   - Dedicated merchant route at `/merchant` enclosed within the `(merchant)` route group.
   - Protected by Next.js middleware enforcing `omni_role === "merchant"` and unauthenticated login redirects.
   - TanStack React Query v5 with query invalidation for synchronized real-time state (`["merchant", "stores"]`, `["merchant", "kpis", storeId]`, `["merchant", "demand", storeId]`, `["merchant", "inventory", storeId]`, `["merchant", "tasks", storeId]`).
2. **Merchant Operations Component Architecture:**
   - `StoreHeader`: Sticky top navigation with store switcher, active store badges, sync controls, and session logout.
   - `KpiOverview`: 4 interactive KPI metric cards with direct navigation triggers into filtered inventory and restock tasks.
   - `DemandRadar`: Real-time neighborhood intent chips highlighting trending searches and merchandising recommendations for missing items.
   - `InventoryTable`: High-density data grid featuring physical shelf locations, inline quantity steppers calling `PATCH /api/v1/merchant/inventory/{id}`, and an integrated CSV batch upload modal.
   - `ShelfAuditPanel`: Multimodal photo upload interface running Gemini Vision audits with detailed gap cards and automated task generation.
   - `RestockTasksKanban`: Replenishment task lifecycle board allowing managers to approve tasks and mark them restocked (triggering backend inventory auto-increments).

## Consequences
- Complete end-to-end loop: Shoppers generate mission traces and substitutions; merchants observe demand signals, run shelf vision audits, and replenish shelves before stockouts impact sales.
- Zero untyped code or TypeScript `any` types; all API responses strictly conform to OpenAPI schemas.
- Clean Next.js production build compiling all 8 static pages and middleware.
