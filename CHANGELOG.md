# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Monorepo structure with FastAPI backend (`apps/api`) and Next.js frontend (`apps/web`).
- Docker Compose configuration with PostgreSQL 16 and `pgvector`, `pg_trgm`, `cube`, and `earthdistance` extensions.
- Root Makefile, CI workflow, and environment configuration.
- Architecture Decision Record `docs/adr/0001-monorepo-and-technology-selection.md`.
