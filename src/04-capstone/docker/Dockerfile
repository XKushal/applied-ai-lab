# Multi-stage build using `uv` — fast, deterministic, no pip layer caching games.

FROM python:3.13-slim AS base

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# install deps first (cached layer) — only rebuilds when pyproject.toml/uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# now copy source
COPY . .

# pre-warm the embedding model so first request isn't slow
RUN uv run python -c "from chromadb.utils import embedding_functions; embedding_functions.DefaultEmbeddingFunction()"

# need the Chroma DB populated — run ingest at build time so the container is self-contained
RUN uv run python src/02-rag/01_ingest.py

ENV PYTHONUNBUFFERED=1
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
EXPOSE 8000

# Note: cd into 04-capstone so `app` is importable as a package
WORKDIR /app/src/04-capstone
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
