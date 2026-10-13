# OmniMission AI: Hackathon Judge Demo Playbook

This document provides a scripted, zero-friction demonstration guide for judges evaluating OmniMission AI. Follow these exact steps to exercise both the Shopper and Merchant experiences end-to-end.

---

## 0. Demo Credentials & Pre-Seeded Accounts

The database is seeded with realistic Indian retail inventory across Bengaluru, Mumbai, Delhi, and Hyderabad:

| Persona | Email | Password | Role | Primary Store |
| :--- | :--- | :--- | :--- | :--- |
| **Shopper (Arjun)** | `shopper@omnimission.ai` | `Shopper123!` | `user` | Bengaluru (Indiranagar / Koramangala) |
| **Merchant (Rajesh)** | `merchant@omnimission.ai` | `Merchant123!` | `merchant` | OmniMart Indiranagar 100ft Rd |
| **Shopper 2 (Priya)** | `shopper2@omnimission.ai` | `Shopper123!` | `user` | Hindi Voice Shopper |
| **Merchant 2 (Pooja)** | `merchant2@omnimission.ai` | `Merchant123!` | `merchant` | OmniFresh Bandra West (Mumbai) |

---

## Golden Demo 1: High-Protein Eggless Cake (Dietary & Substitution)

### What this proves
Autonomous culinary decomposition, strict dietary enforcement (`eggless`, `high_protein`), automatic out-of-stock substitution, physical catalog price/aisle grounding, and monotonic walking routes.

### Steps
1. Navigate to `http://localhost:3000/login` and click **"Shopper Demo (Bengaluru)"** to auto-fill credentials, then click **Sign In**.
2. You will be redirected to the Shopper Mission Workspace at `/app`.
3. In the store selector, ensure **OmniMart Indiranagar 100ft Road** is selected.
4. Click the pre-configured prompt chip:
   > *"Eggless cake with good protein, suggest all ingredients"*
5. Click **"Launch Mission"**.
6. **Watch the live multi-agent reasoning timeline:**
   - `IntentAgent` decomposes the goal into intent `recipe`, headcount `4`, dietary tags `['eggless', 'high_protein']`.
   - `PlannerAgent` expands this into 6 essential ingredients: Flour, Protein powder, Leavening agent, Moisture/egg-replacer, Flavoring, Chocolate.
   - `PgHybridSearch` queries physical store inventory using Reciprocal Rank Fusion.
   - In Indiranagar store, `plant-protein-chocolate-500g` is intentionally seeded out-of-stock. `SubstitutionEvaluator` identifies `whey-protein-raw-1kg` as a grounded high-protein alternative with clear justification.
   - `GroundingValidator` locks exact physical aisle, bay, and shelf coordinates.
7. **Inspect the Physical Basket:**
   - Notice the exact shelf coordinates: Aisle 3 (Baking), Aisle 2 (Greek yogurt egg replacer), Aisle 8 (Protein).
   - Check the **Monotonic Walking Path**: In-store wayfinding orders items monotonically ($Aisle_2 \to Aisle_3 \to Aisle_8$) so the shopper walks the store in one continuous line.
   - Click the checkboxes to simulate in-store item picking.

---

## Golden Demo 2: Travel-Size Toiletries (Packaging Constraints)

### What this proves
Constraint reasoning for airline liquid compliance (≤100ml / mini packaging). Full-size items are strictly excluded even if cheaper.

### Steps
1. In the Shopper Workspace `/app`, click the chip or enter:
   > *"I'm travelling to Mumbai for 3 days, I need travel-size shampoo, toothpaste, etc."*
2. Click **"Launch Mission"**.
3. **Observe the result:**
   - All recommended items are travel-size compliant:
     - Pantene Mini Shampoo (50 ml)
     - Colgate Total Travel Toothpaste (30 g)
     - Nivea Pocket Roll-on (35 ml)
     - Dettol Pocket Sanitizer (50 ml)
     - Minimalist Travel Sunscreen (50 g)
     - Oral-B Foldable Toothbrush
   - All items are mapped to **Aisle 7 (Personal Care & Travel Toiletries)** with exact bay and shelf numbers.

---

## Golden Demo 3: Multilingual Voice Query (Hindi)

### What this proves
Multilingual speech transcription via Gemini Audio, normalizing non-English speech into retail catalog taxonomy.

### Steps
1. In the mission composer, click the **Microphone** icon.
2. Allow microphone access in your browser and speak in Hindi (e.g., *"mujhe 8 logon ke liye chai aur snacks chahiye"*), or use the test audio button.
3. The audio is transcribed by `POST /api/v1/voice/transcribe` into Hindi text and passed to `IntentAgent`.
4. The system decomposes the party/snack goal into tea, biscuits, potato chips, and cups grounded in the local store.

---

## Golden Demo 4: House Party for 8 Guests (Budget Fitting)

### What this proves
Scaling headcount to ingredient volumes, fitting disposable party items, and maintaining budget ceiling.

### Steps
1. Click the prompt chip:
   > *"I want to host a party for 8 people, chips drinks cups napkins"*
2. Set budget to ₹1,000.
3. **Observe the result:**
   - Multiplies potato chips and beverage quantities to accommodate 8 people.
   - Adds biodegradable paper cups (Aisle 10), party napkins (Aisle 10), and Haldiram bhujia snacks (Aisle 4).
   - The interactive Budget Meter reflects current basket total vs the ₹1,000 limit.

---

## Golden Demo 5: Merchant Operations, Demand Radar & Shelf Audit

### What this proves
Dual-sided loop: Shopper search behavior creates live merchant demand signals; merchants inspect shelves via Gemini Vision and resolve restock tasks.

### Steps
1. Log out or open an incognito window, navigate to `http://localhost:3000/login`, and click **"Merchant Demo (Rajesh)"**.
2. You will be redirected to the **Merchant Command Portal** (`/merchant`).
3. **Inspect the KPI Overview:**
   - Active Missions count, Grounded GMV captured, Stockout Risk SKUs, and Open Restock Tasks.
4. **Inspect the Demand Radar:**
   - Real-time customer intent search chips (e.g., *"eggless cake"*, *"travel toiletries"*).
   - Shows queries where substitutions were triggered, recommending stock additions to recapture lost revenue.
5. **Run an Autonomous AI Shelf Audit:**
   - Click the **"AI Shelf Audit"** tab.
   - Select **Aisle 3 (Baking & Cocoa Essentials)**.
   - Upload any pantry/shelf photograph (or use sample fixture from `apps/api/tests`).
   - Click **"Run AI Shelf Audit"**.
   - Gemini Vision analyzes the photo against the store's expected inventory, detects facing gaps, and automatically drafts new replenishment restock tasks!
6. **Execute Restock Tasks:**
   - Switch to the **"Restock Tasks"** tab.
   - Locate the newly drafted tasks. Click **"Approve Task"**.
   - When physical stock arrives, click **"Mark Restocked"**.
   - The task transitions to completed, and store inventory `stock_qty` is atomically incremented in the database!
