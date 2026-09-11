# ==============================================================================
# CampusFlow Backend Dockerfile — Multi-Stage Build
# ==============================================================================

# Stage 1: Dependency Builder
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Minimal Production Runtime
FROM python:3.13-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group
RUN groupadd -g 10001 campusflow && \
    useradd -u 10001 -g campusflow -s /bin/bash -m campusflow

WORKDIR /app

# Copy isolated virtual environment from builder stage
COPY --from=builder --chown=campusflow:campusflow /opt/venv /opt/venv

# Copy application source code and migrations
COPY --chown=campusflow:campusflow alembic /app/alembic
COPY --chown=campusflow:campusflow alembic.ini /app/alembic.ini
COPY --chown=campusflow:campusflow app /app/app
COPY --chown=campusflow:campusflow scripts /app/scripts
COPY --chown=campusflow:campusflow entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER campusflow:campusflow

EXPOSE 8000

# Container healthcheck targeting the health API endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
