# OmniMission AI: Google Cloud Platform (GCP) Migration Architecture

## 1. Local-First to GCP Target Mapping

OmniMission AI was architected from Day 1 using Hexagonal Architecture (Ports and Adapters) specifically so Phase 1 local components can be swapped for native Google Cloud services in Phase 2 with zero refactoring of domain or agent code.

| Layer / Concern | Phase 1 Local Implementation | Phase 2 GCP Target Service | Integration Mechanism |
| :--- | :--- | :--- | :--- |
| **API Backend** | FastAPI in local process / Docker | **Cloud Run (Serverless Containers)** | Containerized Dockerfile deployed to Cloud Run with automatic scaling |
| **Web Frontend** | Next.js 15 local dev server | **Cloud Run** or **Firebase App Hosting** | Next.js SSR container deployed to Cloud Run behind Cloud CDN |
| **Relational Data** | PostgreSQL 16 (`pgvector/pgvector:pg16`) | **Cloud SQL for PostgreSQL** or **AlloyDB** | Managed PostgreSQL with pgvector extension enabled |
| **Catalog Search** | `PgHybridSearch` (pgvector + FTS + RRF) | **Vertex AI Search / Agent Search** | Adapter swap: `VertexAiSearchAdapter` implementing `SearchBackend` port |
| **AI Models** | Google Gemini (`gemini-2.0-flash` direct key) | **Gemini on Vertex AI** | `agno.models.google.Gemini(vertexai=True, project=..., location=...)` |
| **File Storage** | `LocalFsStorage` (local uploads directory) | **Google Cloud Storage (GCS)** | Adapter swap: `GcsStorageAdapter` implementing `StorageBackend` port |
| **Analytics Sink** | `PgAnalytics` (PostgreSQL aggregation queries) | **BigQuery + BigQuery AI** | Adapter swap: `BigQueryAnalyticsSink` implementing `AnalyticsSink` port |
| **BI Dashboards** | Merchant Web UI custom charts | **Looker / Looker Studio** | Direct Looker connector querying BigQuery analytics tables |
| **Secret Storage**| `.env` / Pydantic Settings | **Google Secret Manager** | FastAPI startup hook fetching DB credentials and API keys |

---

## 2. Step-by-Step Migration Guide

### Step 1: Deploy Relational Database to Cloud SQL
1. Provision a Cloud SQL PostgreSQL 16 instance:
   ```bash
   gcloud sql instances create omnimission-db \
     --database-version=POSTGRES_16 \
     --tier=db-custom-2-7680 \
     --region=asia-south1
   ```
2. Enable the `vector` and `pg_trgm` extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "vector";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   ```
3. Run Alembic migrations against the Cloud SQL connection string:
   ```bash
   DATABASE_URL=postgresql+psycopg://user:pass@/cloudsql/project:region:omnimission-db/omnimission uv run alembic upgrade head
   ```

### Step 2: Implement the Cloud Storage Adapter
Replace `LocalFsStorage` with `GoogleCloudStorageAdapter`:
```python
# src/omnimission/adapters/gcs_storage.py
from google.cloud import storage
from omnimission.ports.storage_backend import StorageBackend

class GcsStorageAdapter(StorageBackend):
    def __init__(self, bucket_name: str) -> None:
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    async def save(self, filename: str, content: bytes, content_type: str) -> str:
        blob = self.bucket.blob(f"uploads/{filename}")
        blob.upload_from_string(content, content_type=content_type)
        return blob.public_url
```

### Step 3: Implement the BigQuery Analytics Sink
Replace `PgAnalytics` with asynchronous BigQuery streaming writes for event telemetry and merchant demand forecasting:
```python
# src/omnimission/adapters/bigquery_analytics.py
from google.cloud import bigquery
from omnimission.ports.analytics_sink import AnalyticsSink

class BigQueryAnalyticsSink(AnalyticsSink):
    def __init__(self, dataset_id: str) -> None:
        self.client = bigquery.Client()
        self.dataset_id = dataset_id

    async def record_mission_trace(self, mission_data: dict) -> None:
        table_ref = f"{self.dataset_id}.mission_events"
        errors = self.client.insert_rows_json(table_ref, [mission_data])
        if errors:
            raise RuntimeError(f"BigQuery insert error: {errors}")
```

### Step 4: Deploy API & Web Containers to Cloud Run
Build and push images using Cloud Build, then deploy to Cloud Run:
```bash
# Build API Container
gcloud builds submit --tag gcr.io/$PROJECT_ID/omnimission-api ./apps/api

# Deploy API to Cloud Run
gcloud run deploy omnimission-api \
  --image gcr.io/$PROJECT_ID/omnimission-api \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:asia-south1:omnimission-db \
  --set-env-vars "ENVIRONMENT=production"
```

---

## 3. Terraform Infrastructure as Code (Sketch)

```hcl
# main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "asia-south1"
}

# 1. Cloud SQL for PostgreSQL 16
resource "google_sql_database_instance" "postgres" {
  name             = "omnimission-postgres-prod"
  database_version = "POSTGRES_16"
  region           = "asia-south1"

  settings {
    tier = "db-custom-2-7680"
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }
  }
}

# 2. Cloud Storage Bucket for Multimodal Uploads
resource "google_storage_bucket" "uploads" {
  name          = "omnimission-uploads-${var.project_id}"
  location      = "ASIA-SOUTH1"
  force_destroy = false

  uniform_bucket_level_access = true
}

# 3. BigQuery Dataset for Demand Telemetry
resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "omnimission_telemetry"
  friendly_name               = "OmniMission Demand Telemetry"
  location                    = "asia-south1"
  default_table_expiration_ms = 7776000000 # 90 days
}

# 4. Cloud Run Service for FastAPI API
resource "google_cloud_run_v2_service" "api" {
  name     = "omnimission-api"
  location = "asia-south1"

  template {
    containers {
      image = "gcr.io/${var.project_id}/omnimission-api:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
  }
}
```
