# ADR 0014: Resumable SSE Protocol over HTTP/2 and Event Persistence

## Status
Accepted

## Context
Conversational AI shopping missions stream complex, multi-second agent workflows (intent routing, recipe RAG planning, tool invocations, SKU grounding checks, basket updates, wayfinding calculations, and completion). 

In physical or mobile shopping environments, mobile connectivity is frequently interrupted (cell tower handoffs, elevator transitions, browser tab suspensions). Traditional streaming architectures present severe shortcomings:
1. **Lost Event Chunks:** When a client drops connection mid-stream, standard ephemeral generators drop in-flight events, causing UI state divergence and missing items in the client's rendered cart.
2. **Duplicated Side-Effects:** Naive reconnection that triggers the agent execution from scratch can duplicate tool invocations (such as repeated cart additions or duplicate mission creations).
3. **Buffering Latency:** Standard reverse proxies buffer HTTP/1.1 chunked responses until buffer size thresholds are met, breaking real-time token and step streaming to the client.
4. **Head-of-Line Blocking:** HTTP/1.1 limits concurrent open connections per host to 6, starving application network requests while a long-lived SSE connection is open.

## Decision
1. **Database-Backed Event Persistence (`mission_events` Table):**
   - Implemented `MissionEvent` model (`apps/api/src/omnimission/models/mission.py`) backed by migration `0009_mission_events.py`.
   - Every event emitted during agent orchestration is atomically persisted with a strictly monotonic `sequence_id` scoped per `mission_id` (`uq_mission_sequence` unique constraint).
   - Events store typed payload JSONB, event timestamp, and category (`agent_thought`, `tool_call`, `tool_result`, `basket_update`, `grounding_check`, `wayfinding_route`, `mission_complete`, `error`).

2. **W3C Resumable SSE Protocol with `Last-Event-ID`:**
   - Adheres to the W3C EventSource standard: each message frame includes `id: <sequence_id>\nevent: <event_type>\ndata: <json>\n\n`.
   - Client automatically transmits `Last-Event-ID: <n>` header upon reconnecting.
   - `MissionService.stream_mission_execution` reads `Last-Event-ID`. If `after_seq > 0`, it replays all historical events with `sequence_id > after_seq` directly from Postgres before streaming active live events.
   - If the mission already finished while the client was disconnected, all remaining events through `mission_complete` are replayed immediately, allowing instantaneous state recovery without re-running agent logic.

3. **HTTP/2 and Zero-Buffer TLS Proxy via Caddy:**
   - Configured Caddy in `infra/caddy/Caddyfile` and `docker-compose.yml`.
   - Caddy enables HTTP/2 multiplexing out-of-the-box with automatic local HTTPS certificates, eliminating connection pool starvation.
   - Configured `flush_interval -1` on the reverse proxy upstream: forces immediate frame flushing to the socket, preventing OS or proxy buffer delays during incremental streaming.
   - Passes standard SSE headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`.

4. **Multi-Tenant Guest & Principal Isolation:**
   - Updated `missions` table to include `guest_session_id` referencing `guest_sessions.id`.
   - `stream_mission_execution` verifies caller `Principal` (user ID or guest session token) matches the mission creator before returning stream events, preventing cross-tenant stream sniffing.

## Consequences
- **Resilient Mobile UX:** Shoppers can reload tabs or navigate networks without losing agent thoughts or cart item additions.
- **Zero Redundant LLM Invocations:** Agent execution state is persisted once; clients simply catch up with unacknowledged sequence IDs.
- **Auditable Agent Logs:** Every thought and tool decision made during a mission is permanently recorded in Postgres for evaluation, inspector visualization, and compliance auditing.
