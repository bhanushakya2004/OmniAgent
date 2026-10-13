# OmniAgent — Team Quickstart & Testing Guide 🚀

Welcome to **OmniAgent**! This guide contains everything your team needs to spin up the full stack locally, access all portals, log in with pre-seeded demo credentials, and test the conversational commerce and merchant analytics features.

---

## 🐳 1. One-Command Local Startup

The entire stack (PostgreSQL with pgvector, automated migrations, seed catalog, FastAPI backend, and Next.js frontend) runs with **just one Docker command**:

```bash
docker compose up -d --build
```

### Checking Status & Logs
```bash
# View running containers
docker ps

# Stream backend API logs
docker logs -f omnimission-api

# Stream frontend Web UI logs
docker logs -f omnimission-web
```

### Stopping the Stack
```bash
docker compose down
```

---

## 🌐 2. Local Access URLs

| Portal / Service | URL | Description |
| :--- | :--- | :--- |
| **🛍️ Shopper Experience (Flagship)** | [http://localhost:3000/shop](http://localhost:3000/shop) | Conversational commerce: Catalog Search with dietary chips, "Ask AI" goal fulfillment, slide-over cart, and "Inspect AI" telemetry. |
| **📦 Express Checkout** | [http://localhost:3000/checkout](http://localhost:3000/checkout) | Unified checkout with simulated UPI, Card, NetBanking, and Cash on Delivery. |
| **🏪 Merchant Operations Portal** | [http://localhost:3000/merchant](http://localhost:3000/merchant) | Demand radar, shelf inventory, vision audits, restock tasks, and **Store Analyst AI**. |
| **⚡ Backend API Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger/OpenAPI documentation for all REST & SSE endpoints. |
| **❤️ Backend Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Returns `{"status":"ok"}`. |

---

## 🔑 3. Pre-Seeded Test Credentials

You can log in at [http://localhost:3000/login](http://localhost:3000/login) (or click the 1-click demo credential buttons on the login page):

### 🏪 Merchant Accounts (Store Operators)
| Field | Merchant 1 (Bengaluru) | Merchant 2 (Mumbai) |
| :--- | :--- | :--- |
| **Email** | `merchant@omnimission.ai` | `merchant2@omnimission.ai` |
| **Password** | `Merchant123!` | `Merchant123!` |
| **Role** | `merchant` | `merchant` |
| **Assigned Store** | OmniMart Indiranagar 100ft Road | OmniFresh Bandra West |

### 🛍️ Shopper Accounts (Registered Users)
| Field | Shopper 1 (English) | Shopper 2 (Hindi Voice) |
| :--- | :--- | :--- |
| **Email** | `shopper@omnimission.ai` | `shopper2@omnimission.ai` |
| **Password** | `Shopper123!` | `Shopper123!` |
| **Role** | `user` | `user` |
| **Location** | Bengaluru | Mumbai |

> 💡 **Guest Shopping:** You do **not** need to log in to test shopping! Opening [http://localhost:3000/shop](http://localhost:3000/shop) directly supports anonymous guest sessions with persistent carts that automatically merge if you log in later.

---

## 🧪 4. Key Features to Test

### A. Shopper "Ask AI" Conversational Missions ([/shop](http://localhost:3000/shop))
Switch the mode toggle to **"Ask AI"** and try these golden prompts:
1. **Culinary Goal (Recipe Decomposition):**
   > *"I want everything needed to make an eggless strawberry cake for 8 people"*
   - Watch the agent stream its reasoning, query the recipe knowledge base, match physical in-stock inventory in Indiranagar, and add all items to the cart.
2. **Travel Toiletries Kit:**
   > *"Travelling to Mumbai for 3 days, I need travel-size shampoo, toothpaste, and sanitizer"*
   - Resolves airline-compliant (≤100ml) travel SKUs with exact shelf coordinates.
3. **House Party Supplies:**
   > *"Hosting a house party for 8 guests, suggest chips, cold drinks, cookies and paper plates"*
   - Assembles food, beverages, and disposable tableware within store inventory.
4. **Glass-Box "Inspect AI" Modal:**
   - Click the **"Inspect AI"** button in the chat header to view the complete internal trajectory: retrieved RAG chunks, Knowledge Graph traversal, tool executions, and physical grounding checks.

### B. Slide-Over Cart & Express Checkout ([/checkout](http://localhost:3000/checkout))
- Click the cart icon in the top right to open the slide-over drawer.
- Adjust item quantities with steppers.
- Click **"Proceed to Checkout"** to test the payment flow (UPI, Credit Card, NetBanking, COD).
- View the order confirmation with in-store aisle maps.

### C. Merchant Store Analyst AI Console ([/merchant](http://localhost:3000/merchant))
Log in as `merchant@omnimission.ai` and navigate to the **"Store Analyst AI"** tab:
1. **Interactive Analytical Queries:**
   - Try: *"Which baking items are running critically low on stock?"*
   - Try: *"Show me daily revenue by department"*
   - The agent parses your request, validates it through the `SqlGuard` security engine, executes read-only SQL, and returns an interactive Recharts graph (Bar/Line/Pie) alongside audit-ready SQL.
2. **Daily Briefing & Action Proposals:**
   - Review the automated morning briefing.
   - Review and click **"Approve"** or **"Reject"** on pending Human-in-the-Loop (HITL) restock proposals.

---

## 🔬 5. Testing & Verification Commands

Run unit tests and benchmarks inside Docker without installing Python or Node locally:

```bash
# Run all 98 backend unit and integration tests
docker compose run --rm api pytest -v

# Run the automated empirical evaluation benchmarks (RAG, Grounding Invariant, SqlGuard)
docker compose run --rm api python -m omnimission.scripts.run_evals

# Run backend code linter and strict type checker
docker compose run --rm api ruff check .
docker compose run --rm api mypy src
```
