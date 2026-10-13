# ADR 0012: Guest-First Cart Architecture and Simulated Checkout

## Status
Accepted

## Context
High-friction checkout flows that demand upfront registration before carting degrade conversion and deter conversational discovery:
1. **Immediate Discovery:** Unauthenticated visitors must immediately explore products and utilize "Ask AI" mission planning without creating an account first.
2. **Cart Continuity:** When a guest decides to purchase and registers or logs in, their cart items must never be lost or cleared.
3. **Grounded Pricing & In-Store Coordinates:** Every item placed in the cart must snapshot live store inventory price and shelf coordinates (`aisle`, `bay`, `shelf`) to prevent pricing drift.
4. **Mock Payment Safety:** The hackathon requires realistic commerce workflows without real payment gateway credentials or recurring charges.

## Decision
1. **Unified Identity Principal (`Principal`):**
   - FastAPI dependency `get_current_principal` inspects JWT Bearer tokens first. If absent or invalid, it gracefully falls back to `X-Guest-Session-ID` header or `omni_guest_session` cookie.
   - Database model `GuestSession` tracks anonymous shopper sessions for 30 days.

2. **Cart State Machine & Line Item Snapshots:**
   - Database model `Cart` belongs to either an authenticated `user_id` or an anonymous `guest_session_id`.
   - `CartItem` records immutable snapshots of `unit_price`, `aisle`, `bay`, `shelf`, and special substitution notes at the instant of addition.
   - Deduplication constraint `uq_cart_store_product` prevents duplicate rows for the same SKU at a given branch.

3. **Atomic Cart Merging (`CartService.merge_guest_cart_to_user`):**
   - Upon registration or login, the client invokes `POST /api/v1/cart/merge`.
   - The service transfers all guest items into the user's permanent cart, summing duplicate item quantities and marking the guest cart as `"merged"`.

4. **Transactional Order Checkout & Simulated Payment:**
   - Checkout requires an authenticated `User`.
   - In a single database transaction:
     - Verifies sufficient stock across all cart items.
     - Decrements `store_inventory.stock_qty` atomically.
     - Automatically generates a pending `RestockTask` if a product falls to or below its `low_stock_threshold`.
     - Records `PaymentSimulated` with mock transaction references (`SIM_PAY_*`).
     - Marks the cart as `"converted"`.

## Consequences
- **Zero Friction:** Shoppers add items and plan meals immediately without premature authentication walls.
- **Data Integrity:** Pricing and shelf coordinates are locked at cart time; checkout atomically updates store stock.
- **Audit Ready:** Simulated payment transactions and restock tasks create a realistic, auditable enterprise commerce lifecycle.
