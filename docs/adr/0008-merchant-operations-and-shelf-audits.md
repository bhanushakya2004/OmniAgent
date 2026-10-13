# ADR 0008: Merchant Operations: Real-Time Inventory Control, Demand Telemetry, and Visual Shelf Audits

## Status
Accepted

## Context
Physical retail store operators and merchants require an autonomous operational bridge connecting physical shelf states with digital demand signals:
1. **Real-time Inventory Management:** Direct visibility and update capabilities for stock counts, pricing, and physical coordinates (Aisle, Bay, Shelf).
2. **Bulk Inventory Synchronization:** Rapid batch updating via CSV file uploads with robust row-level validation and error reporting.
3. **Demand Velocity & Unmet Intent Radar:** Operational telemetry aggregating mission frequency, grounded gross merchandise value (GMV), at-risk SKUs, and trending customer intents (including unmet search terms and out-of-stock substitutions).
4. **Autonomous Visual Shelf Audits:** Multimodal vision agent evaluating shelf photographs against ground-truth store inventory, detecting empty facing gaps, and auto-drafting replenishment tasks.
5. **Restock Task Lifecycle:** Task management pipeline allowing store managers to review, approve, and complete restock tasks with automatic inventory reconciliation upon completion.

## Decision
1. **Layered Service & Ports Architecture:**
   - Introduced `RestockTask` SQLAlchemy model with indexed status (`pending`, `approved`, `completed`, `dismissed`) and foreign keys to `Store` and `Product`.
   - Defined `AnalyticsSink` interface port (`StoreOverviewKpis`, `DemandSignal`) and implemented `PgAnalytics` adapter executing high-performance aggregate SQL across `missions`, `mission_items`, and `store_inventory`.
   - Created `MerchantService` encapsulating store ownership verification, inventory updates, CSV parsing, analytics queries, and restock task management.
2. **Batch CSV Import Pipeline:**
   - Accepts CSV streams with either `sku_slug`, `sku`, or `product_name` alongside `stock_qty`, `aisle`, `bay`, and `shelf`.
   - Uses multi-strategy product resolution: deterministic UUID lookup -> exact name match -> tokenized word search -> existing SKU lookup.
   - Atomic transaction with structured error reporting (`total_rows`, `imported_count`, `updated_count`, `errors`).
3. **Shelf Audit Vision Agent (`ShelfAuditAgentRunner`):**
   - Grounded shelf inspection combining live Gemini Vision (`gemini-2.5-flash`) with physical store inventory context.
   - Dual-mode architecture: analyzes shelf images against expected aisle inventory, detects missing SKUs and facing gaps, and auto-drafts `RestockTask` records in the database.
   - Offline fallback guarantees continuous operational telemetry even in air-gapped or network-constrained retail environments.
4. **Restock Task Execution & Inventory Reconciliation:**
   - `PATCH /api/v1/merchant/restock-tasks/{task_id}` transitions tasks through `approved` and `completed`.
   - When a restock task is marked `completed`, store inventory `stock_qty` is atomically incremented by `recommended_qty`.

## Consequences
- Complete dual-sided loop: Shoppers generate demand and mission traces; merchants see aggregate demand signals and replenish stock before stockouts impact revenue.
- Clean separation of concerns with ports and adapters, ensuring `PgAnalytics` can be swapped for a BigQuery sink in GCP Phase 2 without modifying merchant service logic.
- Robust role-based security ensures merchants can only view and mutate stores and restock tasks they own.
