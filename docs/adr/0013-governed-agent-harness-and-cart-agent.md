# ADR 0013: Governed Agent Harness, Concierge Router, and Cart Agent

## Status
Accepted

## Context
In conversational commerce systems, unrestricted LLM access to database mutations or sensitive endpoints introduces severe risks:
1. **Unbounded Agent Scope:** Allowing an unauthenticated guest or consumer shopper agent to invoke merchant-only operations (e.g. inventory restock, shrinkage audits, sales margins) creates severe authorization and privilege escalation risks.
2. **Ungrounded Hallucinations:** Generative agents might fabricate product names, prices, or aisles that do not exist in the physical store.
3. **Intent Ambiguity:** User prompts range from cooking recipes to travel packing, party supplies, simple catalog lookups, and explicit cart additions. A single prompt cannot cleanly handle all domains without specialized sub-agent decomposition.
4. **Lack of Personalization Transparency:** Users expect agents to remember dietary restrictions (e.g. eggless, gluten-free) and household sizes without having to re-specify them in every prompt, but black-box AI memory causes user distrust.

## Decision
1. **Governed Tool Registry & Scope Binder (`ToolRegistry`, `BoundToolRegistry`):**
   - Tools are categorized with explicit `ToolScope` (`shopper`, `merchant`, `admin`, `system`) and `SideEffectLevel` (`read_only`, `idempotent_write`, `destructive`).
   - Every execution binds the caller's verified `Principal`, active database `AsyncSession`, `cart_id`, and selected `store_ids`.
   - Shopper roles invoking merchant tools receive immediate `ForbiddenError` exceptions.
   - All tool executions are metered and audited with `ToolExecutionAudit` records capturing duration, success, inputs, and outputs.

2. **Concierge Router Agent (`ConciergeRouter`):**
   - Classifies user intent into 8 distinct route categories: `recipe_mission`, `travel_mission`, `party_mission`, `catalog_search`, `cart_action`, `order_status`, `merchant_analytics`, and `general_qa`.
   - Vends a structured `RoutingDecision` with confidence scores and extracted entities (servings, duration, dietary tags).
   - Uses Agno Gemini Agent with deterministic, regex-validated rule fallback ensuring 100% offline test reliability.

3. **Recipe-RAG Planner Agent (`PlannerAgentRunner`):**
   - Integrates `KnowledgeService.retrieve_and_plan` to ground recipe generation in 65 structured documents and Knowledge Graph nodes.
   - Enforces dietary constraints (e.g. eggless replacements using condensed milk or Greek yogurt).
   - Proportinally scales quantities based on `servings_or_people`.

4. **Cart Action Agent (`CartAgent`):**
   - The authoritative action agent interfacing between multi-agent mission outputs and `CartService`.
   - Enforces the Grounding Invariant: every added SKU must be physically verified against `store_inventory`.
   - Supports atomic basket additions, line item removals, cart clearing, and cart viewing.

5. **Transparent User Memory (`MemoryService`, `PersonalisationAgent`):**
   - Backed by PostgreSQL `user_memories` table (migration `0008_user_memories`).
   - PersonalisationAgent automatically enriches `MissionIntent` with active dietary preferences, household sizes, and allergen exclusions.
   - Captures explicit statements (e.g. "Remember that I am vegetarian") directly from chat conversations.
   - Exposed via transparent REST endpoints at `/api/v1/memories` so users can inspect, edit, and delete their saved profile at any time.

## Consequences
- **Strict Least-Privilege Security:** Shoppers and guests cannot execute merchant actions or access unauthorized stores.
- **Measurable Grounding:** Hallucinated prices, aisles, or SKUs are strictly blocked before cart insertion.
- **Glass-Box Personalization:** Shoppers retain full ownership over what the AI remembers about them.
