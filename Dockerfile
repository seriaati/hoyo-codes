# syntax=docker/dockerfile:1

# Build stage
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Install git (required for genshin.py git dependency)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy project and install
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Runtime stage
FROM python:3.12-slim-bookworm

# Install curl for health checks and libatomic1 for Prisma/Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application from builder
COPY --from=builder /app /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Default port (can be overridden via PORT env var)
ENV PORT=1078
EXPOSE $PORT

# Health check (uses PORT env var)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Startup script: generate prisma client, push schema, then run app
CMD ["sh", "-c", "prisma generate && prisma db push --skip-generate && python run.py"]
