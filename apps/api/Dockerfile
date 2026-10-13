FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /bin/uv

COPY pyproject.toml README.md ./
RUN uv venv /opt/venv && uv pip install --no-cache -r pyproject.toml

FROM python:3.12-slim AS runner

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r omni && useradd -r -g omni omni && \
    mkdir -p /app/.data/uploads && chown -R omni:omni /app

COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini

USER omni

EXPOSE 8000

CMD ["uvicorn", "omnimission.main:app", "--host", "0.0.0.0", "--port", "8000"]
