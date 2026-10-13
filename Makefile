.PHONY: help db dev migrate seed lint test types eval clean

help:
	@echo "OmniMission AI Development Commands:"
	@echo "  make db        Start PostgreSQL + pgvector container"
	@echo "  make migrate   Run database migrations"
	@echo "  make seed      Load deterministic retail seed data"
	@echo "  make dev-api   Run FastAPI development server"
	@echo "  make dev-web   Run Next.js development server"
	@echo "  make lint      Run code linters across api and web"
	@echo "  make test      Run test suites across api and web"
	@echo "  make eval      Run automated evaluation harness (RAG, Grounding, NL2SQL)"
	@echo "  make types     Generate TypeScript client types from OpenAPI schema"

db:
	docker compose up -d db

migrate:
	cd apps/api && uv run alembic upgrade head

seed:
	cd apps/api && uv run python -m omnimission.seed.loader

dev-api:
	cd apps/api && uv run uvicorn omnimission.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && npm run dev

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy src
	cd apps/web && npm run lint

test:
	cd apps/api && uv run pytest -v
	cd apps/web && npm test

types:
	cd apps/api && uv run python -m omnimission.scripts.export_openapi
	cd apps/web && npm run generate-types

eval:
	cd apps/api && uv run python -m omnimission.scripts.run_evals

clean:
	docker compose down -v
