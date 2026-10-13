# OmniMission AI: Frontend Architecture & Design Specification

## 1. Overview & Tech Stack

The OmniMission AI web application is built with **Next.js 15 (App Router)** in **TypeScript strict mode**, styled with **Tailwind CSS**, and architected with **Radix UI** primitives and **Lucide** icons.
- **Framework:** Next.js 15 (`apps/web`).
- **Server State Management:** TanStack React Query v5.
- **Client State Management:** Zustand v5 with LocalStorage persistence.
- **Streaming Ingestion:** Native browser `EventSource` with reconnect handling.
- **Component Design System:** Custom atomic UI (`Badge`, `Button`, `Card`, `Input`, `Textarea`).

---

## 2. Component Hierarchy Tree

```text
apps/web/src/
├── app/
│   ├── layout.tsx                     # Root HTML shell, font tokens, Providers wrapper
│   ├── page.tsx                       # High-impact Landing Page & Feature Showcase
│   ├── (auth)/
│   │   ├── login/page.tsx             # Split-screen role login with demo quick-fill credentials
│   │   └── register/page.tsx          # Account creation with role selection (Shopper vs Merchant)
│   ├── (shopper)/
│   │   └── app/page.tsx               # Unified Shopper Mission Workspace
│   └── (merchant)/
│       └── merchant/page.tsx          # Merchant Operations & Demand Radar Portal
├── components/
│   ├── shopper/
│   │   ├── store-picker.tsx           # GPS location button, city shortcuts, multi-store radius chips
│   │   ├── mission-composer.tsx       # Multimodal input (audio recording, photo upload, golden chips)
│   │   ├── reasoning-timeline.tsx     # Animated SSE multi-agent progress cards with latency badges
│   │   ├── basket-view.tsx            # Physical basket with aisle coordinates, budget meter, steppers
│   │   └── wayfinding-route.tsx       # Monotonic in-store walking checklist with picked progress
│   ├── merchant/
│   │   ├── store-header.tsx           # Store switcher, active store status, user session controls
│   │   ├── kpi-overview.tsx           # 4 Metric cards: Missions, Grounded GMV, Risk SKUs, Tasks
│   │   ├── demand-radar.tsx           # Real-time search query chips and substitution loss alerts
│   │   ├── inventory-table.tsx        # High-density inventory grid, inline stock steppers, CSV modal
│   │   ├── shelf-audit-panel.tsx      # Gemini Vision photo upload, aisle audit, gap findings
│   │   └── restock-tasks-kanban.tsx   # Work order cards with Approve & Mark Restocked actions
│   └── ui/                            # Accessible atomic design tokens (Button, Card, Badge, Input)
```

---

## 3. State Management Strategy

### Server State (TanStack Query v5)
- Manages asynchronous remote data, caching, background polling, and cache invalidation.
- Primary query keys:
  - `["stores", "nearby", lat, lng, radius]`
  - `["missions", missionId]`
  - `["missions", "history"]`
  - `["merchant", "stores"]`
  - `["merchant", "kpis", storeId]`
  - `["merchant", "demand", storeId]`
  - `["merchant", "inventory", storeId]`
  - `["merchant", "tasks", storeId]`

### Client State (Zustand v5)
- Manages local user preferences, selections, and session tokens across tab transitions:
  - `useAuthStore`: Current user profile, JWT access token, and logout synchronization.
  - `useLocationStore`: Current GPS latitude/longitude, active city preset, and permission state.
  - `useStoreSelectionStore`: Array of selected store UUIDs for mission fulfillment.

---

## 4. Route Map & Route Guard Protection

| Route | Route Group | Allowed Roles | Middleware Guard Behavior |
| :--- | :--- | :--- | :--- |
| `/` | Public | All | Accessible to all visitors. Direct access to demo portals. |
| `/login` | Public | Unauthenticated | Redirects authenticated shoppers to `/app` and merchants to `/merchant`. |
| `/register`| Public | Unauthenticated | Redirects authenticated users to their respective home dashboard. |
| `/app` | `(shopper)` | `user` | Unauthenticated redirected to `/login?redirect=/app`. Merchants redirected to `/merchant`. |
| `/merchant`| `(merchant)` | `merchant` | Unauthenticated redirected to `/login?redirect=/merchant`. Shoppers redirected to `/app`. |

---

## 5. Multimodal Input Processing

### 1. In-Browser Speech Recording (`MediaRecorder`)
- The `MissionComposer` uses the browser's `navigator.mediaDevices.getUserMedia({ audio: true })`.
- Records audio stream into `audio/webm` chunks.
- Upon recording completion, dispatches audio blob to `POST /api/v1/voice/transcribe`.
- Transcribed text (e.g. Hindi or English) is automatically populated into the input prompt.

### 2. Product & Shelf Photo Capture
- Shoppers can photograph an item or packaging label (`image/jpeg`, `image/png`).
- Sends file to `POST /api/v1/uploads` and analyzes through `POST /api/v1/vision/analyze`.
- Extracted retail search query (e.g., *"Belgian dark chocolate 55%"*) is injected into the mission input.
- Merchants use the same upload pipeline to submit full aisle photos for autonomous visual shelf auditing.

---

## 6. Design Tokens & Accessibility

- **Color Palette:**
  - Emerald (`emerald-600`): In-stock items, catalog authority, physical store markers.
  - Indigo (`indigo-600`): AI agent reasoning, multi-agent workflow orchestration.
  - Amber (`amber-600`): Smart substitutions, low stock warnings, pending review work orders.
  - Rose (`rose-600`): Out-of-stock items, critical shelf gaps, input validation errors.
- **Accessibility:**
  - Semantic HTML landmarks (`<header>`, `<nav>`, `<main>`, `<section>`).
  - Strict ARIA attributes on interactive steppers, modal dialogues, and tabs.
  - High contrast text conforming to WCAG AA specifications across both light and dark modes.
