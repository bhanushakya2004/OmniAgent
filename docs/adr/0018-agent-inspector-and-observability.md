# ADR 0018: Glass-Box Agent Inspector and Observability Telemetry

## Status
Accepted

## Context
Black-box AI agents that hide their reasoning, internal tool selections, database queries, and knowledge lookups generate user and judge skepticism. In an AI hackathon, explaining *how* and *why* an agent made a decision is paramount:
1. **Explainability & Grounding Verification:** Did the agent invent an item or retrieve it from physical store inventory?
2. **Security & Scope Governance:** Did tool invocations adhere to strict read-only parameters and principal authorization scopes?
3. **Knowledge Retrieval Auditing:** How did the RAG pipeline rank candidates (RRF scores, vector distance, full-text match) and traverse the Knowledge Graph?
4. **Resilience & Replay Visibility:** How were stream events sequenced and replayed across intermittent network drops?

## Decision
1. **Backend Inspector Telemetry Endpoint (`GET /api/v1/missions/{id}/inspector`):**
   - Implemented in `MissionService.get_mission_inspector_telemetry` and mounted in `apps/api/src/omnimission/api/v1/missions.py`.
   - Compiles comprehensive telemetry: model used (`gemini-2.5-flash`), event count, tool invocation logs, grounding checks, and chronological monotonic event sequence.

2. **Frontend Glass-Box Inspector Modal (`AgentInspectorModal`):**
   - Built a comprehensive observability modal in `apps/web/src/components/shopper/agent-inspector-modal.tsx` accessible via a dedicated "Inspect AI" button on `/shop`.
   - Organizes telemetry into five structured views:
     - **Agent Trajectory & Routing:** Original user prompt, sub-agent transitions, and step-by-step thoughts.
     - **Governed Tool Registry:** Every tool call (`search_catalog`, `get_knowledge_plan`, `add_to_basket`) with inputs, execution latency, and scope permissions.
     - **RAG & Knowledge Graph Traversal:** Visual representation of graph edges and hybrid search rank fusion.
     - **Grounding Verification Audit:** SKU inventory verification records with exact physical aisle and shelf coordinates.
     - **Token & Latency Telemetry:** Execution statistics, total round-trip latency, and sequence ID replay log.

## Consequences
- **Complete Glass-Box Transparency:** Every calculation, decision, and tool invocation is fully auditable.
- **Judge & User Confidence:** Proves that the agentic harness is grounded in real store inventory and deterministic business logic rather than unconstrained prompt fabrication.
