FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /bin/uv

RUN uv venv /opt/venv

COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --no-cache .

FROM python:3.12-slim AS runner

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV=/opt/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r omni && useradd -r -g omni omni && \
    mkdir -p /app/.data/uploads && chown -R omni:omni /app

COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh && chown omni:omni ./entrypoint.sh

USER omni

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
