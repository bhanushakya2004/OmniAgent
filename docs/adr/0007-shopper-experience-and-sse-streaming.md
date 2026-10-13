# ADR 0007: Shopper Experience: Proximity Selection, Multimodal Composer, and Live Wayfinding

## Status
Accepted

## Context
Shoppers need a modern, intuitive, responsive interface for executing goal-driven missions across physical retail locations. Traditional ecommerce displays static catalogs; OmniMission AI requires:
1. Real-time store proximity filtering and multi-store mission execution.
2. Multimodal goal capture (typing, speaking, or photographing items).
3. Live streaming transparency into agent decomposition and planning steps.
4. Grounded basket breakdown with explicit aisle/bay/shelf coordinates and substitution rationale.
5. In-store monotonic wayfinding with picked progress tracking.

## Decision
1. **Next.js 15 App Router & Strict TypeScript Architecture:**
   - Unified shopper mission route at `/app` within the `(shopper)` route group.
   - TanStack React Query v5 for caching and server state synchronization (`stores.nearby`, `missions.detail`, `missions.history`).
   - Zustand stores (`useAuthStore`, `useLocationStore`, `useStoreSelectionStore`) for persistent client state with local storage synchronization.
2. **Unified Multimodal Composer:**
   - Golden retail prompt chips covering party planning, dietary constraints, travel toiletries, and multilingual queries.
   - Integrated speech recording via `MediaRecorder` submitting audio blobs to `/api/v1/voice/transcribe`.
   - Camera/photo upload submitting images to `/api/v1/uploads` and running `/api/v1/vision/analyze` for instant query extraction.
3. **Live SSE Progress Timeline (`useMissionStream`):**
   - Direct EventSource stream consuming `/api/v1/missions/{id}/stream`.
   - Fine-grained progress cards with live latency badges, step status, and agent attribution tags.
4. **Physical Grounding & Monotonic Wayfinding:**
   - Grouped store baskets displaying exact Aisle, Bay, and Shelf coordinates.
   - Interactive quantity stepper calling `PATCH /api/v1/missions/{id}/items/{item_id}`.
   - Step-by-step in-store walking checklist with percentage picked tracking and printable layout.

## Consequences
- Fast, resilient client experience that works smoothly on mobile and desktop.
- 100% catalog authority visibly communicated to the shopper through physical shelf markers.
- Transparent multi-agent reasoning creates user delight and trust in substitution proposals.
