# High-Level Architecture (HLD): OmniMission AI

This document outlines the system architecture and data flow for **OmniMission AI**, built entirely on the **Google Cloud Platform (GCP)**.

---

## 1. System Architecture Diagram

```mermaid
flowchart TB
    subgraph CLIENT_LAYER["1. Client Layer"]
        ShopperApp["📱 Shopper Web App (PWA)<br/>• YouTube Video / Short Player<br/>• Voice & Camera Uploads<br/>• In-Store Aisle Navigator"]
        MerchantPortal["💻 Merchant Command Portal<br/>• Store Floor Digital Twin<br/>• Shelf Audit Camera Feed<br/>• Replenishment Tasks"]
    end

    subgraph INGRESS["2. Ingress & Compute Layer"]
        CloudRun["🚀 Cloud Run (Application & API Services)<br/>• Mission Orchestration Engine<br/>• Multi-modal Payload Ingestion<br/>• In-Store Routing Service<br/>• REST / WebSocket Gateway"]
    end

    subgraph AI_SEARCH["3. GenAI & Discovery Layer"]
        Gemini["🧠 Gemini on Vertex AI<br/>• Multimodal Video & Audio Reasoning<br/>• Shelf Gap & Damage Detection<br/>• Dynamic Basket Optimization"]
        VertexSearch["🔍 Vertex AI Search / Agent Search<br/>• Semantic Catalog Discovery<br/>• SKU & Spec Grounding<br/>• Real-time Substitution Engine"]
    end

    subgraph STORAGE_OPERATIONAL["4. Operational & Storage Layer"]
        GCS["🗄️ Cloud Storage (GCS)<br/>• Video & Audio Blobs<br/>• Pantry & Shelf Audit Photos<br/>• Product Imagery"]
        CloudSQL["🗃️ AlloyDB / Cloud SQL<br/>• Live Store SKU Inventory<br/>• Physical Aisle / Shelf Coordinates<br/>• Active Orders & Sessions"]
    end

    subgraph ANALYTICS_BI["5. Analytics & Business Intelligence Layer"]
        BigQuery["📊 BigQuery<br/>• Telemetry & Query Stream Logs<br/>• Unmet Mission Intent History<br/>• Cross-Channel Basket Trends"]
        BigQueryAI["🤖 BigQuery AI (BQML)<br/>• Predictive Demand Forecasting<br/>• SKU Stockout Probability<br/>• Basket Affinity Clustering"]
        Looker["📈 Looker<br/>• Real-time Store Manager Dashboards<br/>• Aisle Heatmaps & Restock Telemetry<br/>• Social Trend Velocity Reports"]
    end

    %% Client to Ingress
    ShopperApp -->|HTTPS / WSS| CloudRun
    MerchantPortal -->|HTTPS / WSS| CloudRun

    %% Ingress to Storage & AI
    CloudRun -->|Store Media Files| GCS
    CloudRun -->|Multimodal Inference| Gemini
    CloudRun -->|Semantic Query| VertexSearch
    CloudRun -->|CRUD Inventory / Aisle Map| CloudSQL

    %% AI to Search & Storage
    Gemini -->|Grounding / Context Retrieval| VertexSearch
    Gemini -->|Read Media Assets| GCS

    %% Ingress to Analytics
    CloudRun -->|Streaming Event Logs| BigQuery

    %% Analytics Pipeline
    BigQuery -->|Batch & Stream Analytics| BigQueryAI
    BigQueryAI -->|Predictive Insights| BigQuery
    BigQuery -->|Visual Insights & Alerts| Looker
    Looker -->|Operational Alerts| MerchantPortal
```

---

## 2. Component Breakdown by Google Cloud Service

| Layer | Google Cloud Technology | Role & Architecture Responsibility |
| :--- | :--- | :--- |
| **Compute & APIs** | **Cloud Run** | • Serverless containerized microservices running the API gateway and agent orchestrator.<br/>• Auto-scales to zero; handles low-latency WebSocket connections for live video timestamp syncing and voice processing. |
| **Multimodal Core** | **Gemini on Vertex AI** | • **Video Understanding:** Ingests YouTube video streams and extracts featured products with exact second-level timestamps.<br/>• **Voice & Vision:** Parses conversational constraints (budget, guest count) and analyzes user pantry photos.<br/>• **Visual Shelf Audit:** Evaluates store shelf photos to detect empty slots, displaced products, and damaged labels. |
| **Discovery & Search** | **Vertex AI Search / Agent Search** | • Semantic vector search over product catalogs and ingredient indexes.<br/>• Implements automated RAG (Retrieval-Augmented Generation) with grounding against available inventory.<br/>• Finds high-affinity, in-stock substitutions when items are missing. |
| **Asset Storage** | **Cloud Storage (GCS)** | • Secure bucket storage for user-uploaded pantry pictures, camera shelf snapshots, video frames, and product catalog media.<br/>• Signed URLs for low-latency client-side asset rendering. |
| **Operational Database** | **AlloyDB / Cloud SQL** | • High-performance relational database managing transactional data: store catalog, live SKU stock counts, physical store floorplan coordinates (Aisle, Bay, Shelf), and shopper carts. |
| **Data Warehouse** | **BigQuery** | • Central data lakehouse ingesting real-time mission telemetry: what shoppers are searching for, what YouTube videos are trending, which substitutions were accepted, and checkout events. |
| **Predictive AI** | **BigQuery AI** | • Executes machine learning models directly in SQL to predict localized inventory depletion.<br/>• Identifies unmet demand patterns across geographical clusters before stock runs out. |
| **Business Intelligence** | **Looker** | • Interactive visualization suite for store managers and corporate buyers.<br/>• Displays real-time social trend velocity, foot-traffic aisle heatmaps, and restock prioritization queues. |

---

## 3. End-to-End Data Flow

### Flow 1: Shopper Mission Lifecycle (Inspiration ➔ Aisle)
1. **Ingestion:** Shopper sends a YouTube URL, spoken audio prompt, and a pantry photo to **Cloud Run**.
2. **Media Storage:** Assets are stored in **Cloud Storage**, generating reference URIs.
3. **Multimodal Analysis:** **Gemini on Vertex AI** processes the video frames, audio transcript, and pantry photo:
   * Extracts target products with video timestamps.
   * Subtracts items already owned (from pantry image).
   * Identifies constraints (e.g., budget: $50, dietary: gluten-free).
4. **Catalog Grounding & Filtering:** **Vertex AI Search** queries the store's product catalog and matches candidates.
5. **Inventory & Aisle Resolution:** **Cloud Run** queries **AlloyDB / Cloud SQL** for real-time in-store stock and physical aisle coordinates. If an item is out of stock, the substitution agent selects a suitable in-stock alternative.
6. **Delivery to Client:** **Cloud Run** delivers a synchronized shoppable video timeline and an optimized in-store walking path back to the **Shopper PWA**.

### Flow 2: Merchant Telemetry & Shelf Audit Lifecycle
1. **Telemetry Streaming:** Every customer mission and substitution decision is logged asynchronously from **Cloud Run** into **BigQuery**.
2. **Predictive Analytics:** **BigQuery AI** runs scheduled jobs identifying high-velocity items and predicting upcoming stockouts for the local branch.
3. **Operational Alert:** **Looker** highlights an at-risk inventory cluster on the store manager's dashboard.
4. **Visual Audit:** The store manager uploads a photo of the corresponding aisle shelf.
5. **Vision Verification:** **Gemini on Vertex AI** inspects the shelf photo, validates the missing SKU, and generates a restock task in **AlloyDB** for the store inventory team.

---

## 4. Key Architectural Attributes

* **Serverless & Elastic:** Cloud Run and Vertex AI scale dynamically with traffic bursts (e.g., viral social video spikes) without managing server clusters.
* **Low-Latency Retrieval:** Vertex AI Search and AlloyDB ensure catalog lookups and aisle coordinate resolutions return in under 200ms.
* **Strict Grounding:** Gemini utilizes Vertex AI Search grounding and structured function calling to eliminate hallucinations in pricing and SKU stock levels.
* **Enterprise Security:** Identity and Access Management (IAM), Cloud KMS for data encryption at rest and in transit, and private VPC connectors between Cloud Run and databases.
