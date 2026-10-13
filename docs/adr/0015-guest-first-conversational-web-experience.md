# ADR 0015: Guest-First Conversational Web Experience & Checkout Flow

## Status
Accepted

## Context
Traditional e-commerce architectures force prospective shoppers through an upfront registration or login gate before allowing them to search inventory or assemble a shopping basket. In a "phygital" retail setting where speed and goal-directed missions are paramount:
1. **Friction from Upfront Authentication:** Requiring user accounts prior to exploration leads to severe drop-off for casual shoppers looking to quickly find ingredients or physical aisle locations.
2. **Disconnected Search vs. AI Reasoning:** Users typically encounter either a standard search bar OR a chatbot widget in the corner that cannot interact with the store catalog or basket.
3. **Cart Volatility Across Sessions:** If an unauthenticated guest adds items via natural language missions or catalog clicks, transitions to checkout must preserve and seamlessly merge those items without duplicate line entries or lost inventory allocations.
4. **Physical Store Wayfinding:** Digital commerce orders traditionally show delivery tracking; physical in-store commerce requires structured aisle, bay, and shelf coordinates so customers and store pickers can navigate the store efficiently.

## Decision
1. **Guest-First Client Architecture (`api-client.ts`, `cart-store.ts`):**
   - Automatically provisions a persistent anonymous session ID via `getOrCreateGuestSessionId()`.
   - Injects `X-Guest-Session-ID` on all HTTP client calls.
   - Transparently integrates with backend `CartService` and `Principal`, ensuring anonymous guests have full access to physical inventory search, AI mission planning, and basket mutations.

2. **Unified Segmented Mode Interface (`/shop`):**
   - Delivers a dual-mode interface with instant toggle:
     - `[Search Catalog]`: Debounced hybrid search across 350+ products, faceted by dietary attributes (`eggless`, `vegetarian`, `vegan`, `gluten_free`), travel-size, and in-stock status, presenting live physical aisle coordinates (`Aisle 3 • Bay B • Shelf 2`).
     - `[Ask AI (Conversational Mission)]`: Multimodal mission harness (Web Speech API mic input, vision photo dropzone, golden prompt chips) streaming live multi-agent reasoning, tool invocations, SKU grounding checks, and wayfinding.

3. **Slide-Over Live Cart Drawer (`CartDrawer`):**
   - Universal slide-over drawer accessible from any view, grouped by physical retail store.
   - Automatically synchronizes in real time whenever streaming mission agents emit `basket_update` events.
   - Displays aisle location markers, unit prices, quantity controls, and subtotal.

4. **Frictionless Checkout Flow (`/checkout`):**
   - Postpones authentication until checkout initiation.
   - Provides inline dual-tab authentication: instant one-click guest registration or password login that binds and merges the active cart without page reloads.
   - Offers In-Store Express Pickup (with customizable time slots) or Express Delivery.
   - Simulated payment selector supporting UPI (Google Pay / PhonePe QR), Credit/Debit Card, Net Banking, and Store Counter Cash.

5. **Aisle-Mapped Order Confirmation (`/orders/[id]`):**
   - Displays real-time fulfillment timeline (`confirmed` -> `in_progress` -> `ready_for_pickup`).
   - Organizes placed order items in sequential physical aisle order, serving as a turn-by-turn navigation sheet for store pickup.

## Consequences
- **Zero Friction Onboarding:** First-time shoppers can complete full recipes or travel missions within seconds of landing on the site.
- **Flawless Cart Persistence:** Guest cart items seamlessly transition to permanent user accounts upon checkout.
- **Physical Retail Grounding:** Every item in the UI is tied to verified inventory, ensuring zero hallucinated products or prices.
