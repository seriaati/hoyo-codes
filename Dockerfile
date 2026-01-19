# syntax=docker/dockerfile:1

# Build stage
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

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

# Create non-root user
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home app

WORKDIR /app

# Copy application from builder
COPY --from=builder --chown=app:app /app /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 1078

# Switch to non-root user
USER app

# Startup script: generate prisma client, push schema, then run app
CMD ["sh", "-c", "prisma generate && prisma db push --skip-generate && python run.py"]
