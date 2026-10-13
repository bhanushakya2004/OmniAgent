# ADR 0016: Merchant Store Analyst, Guarded NL2SQL (SqlGuard), and Human-in-the-Loop Action Proposals

## Status
Accepted

## Context
Physical retail store operators need real-time operational intelligence to manage fast-moving inventory, monitor sales trends, and respond to demand spikes. While Large Language Models can generate SQL queries from natural language questions, executing arbitrary LLM-generated SQL against operational relational databases introduces severe production vulnerabilities:
1. **Mutation and Destruction Risks:** LLMs can generate accidental or hallucinated `DROP`, `TRUNCATE`, `DELETE`, or `UPDATE` statements that corrupt live inventory and catalog state.
2. **Data Leakage & Cross-Tenant Snooping:** Queries might traverse unauthorized tables containing sensitive customer data (such as `users.password_hash`, `guest_sessions`, or `refresh_tokens`), or access other merchants' stores.
3. **Denial-of-Service & Resource Exhaustion:** Unbounded queries (`SELECT * ...` with no `LIMIT`) or missing indexes can tie up database connection pools and trigger memory exhaustion.
4. **Autonomous Side-Effects Without Human Oversight:** Automatically executing inventory replenishment orders without store manager verification risks ordering wrong quantities or creating unwanted purchase orders.

## Decision
1. **AST-Parsed SQL Guard (`SqlGuard`):**
   - Uses `sqlglot` to parse generated SQL queries into an Abstract Syntax Tree (AST).
   - Strictly enforces read-only statement types: rejects anything other than `exp.Select` or `exp.Union`.
   - Table Allowlist: Restricts queries to curated analytics views and physical inventory tables (`v_store_stock_overview`, `v_daily_demand_aggregates`, `v_aisle_traffic`, `v_shrinkage_summary`, `store_inventory`, `products`, `orders`, `order_items`, `restock_tasks`).
   - Table Blocklist: Strictly forbids queries referencing sensitive tables (`users`, `guest_sessions`, `refresh_tokens`, `user_memories`).
   - Physical Store Scoping: Verifies that queries touching store-scoped tables contain explicit `store_id` filter conditions.
   - Resource Constraints: Automatically clamps queries to `LIMIT 100` and executes them within transactions governed by `SET LOCAL statement_timeout = '3000ms'`.

2. **Store Analyst Agent (`StoreAnalystAgent`):**
   - Synthesizes executive commentary and business insights explaining trends in plain English.
   - Outputs a typed `ChartConfig` specification (`chart_type`: `"bar" | "line" | "pie" | "metric" | "table"`, `x_axis`, `y_axis`, `title`) ready for dynamic frontend rendering with Recharts.

3. **Human-in-the-Loop (HITL) Action Proposals (`ActionProposal`, `ActionProposalService`):**
   - When the Store Analyst detects critical anomalies (e.g. stockout of high-velocity SKUs), it drafts an `ActionProposal` with `status="pending_approval"`.
   - Consequential state changes (e.g. creating replenishment `RestockTask` records or adjusting safety stock thresholds) are strictly gated until an authorized merchant reviews and explicitly invokes `/approve` or `/reject`.

4. **Proactive Daily Briefing (`DailyBriefingService`):**
   - Summarizes morning operational health: stockouts, low stock counts, orders today, today's revenue, and actionable alerts.

## Consequences
- **Total Database Safety:** SQL injection and destructive queries are mathematically impossible at the AST validation layer.
- **Zero Hallucinated Metrics:** Every chart and metric presented to merchants is backed by verified PostgreSQL query executions.
- **Governed Autonomy:** Agents proactively identify problems and propose solutions, while human store managers retain complete authority over real-world inventory commitments.
