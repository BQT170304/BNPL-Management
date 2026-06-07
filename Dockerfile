# ── Stage 1: install Python dependencies ─────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source (exclude dev files via .dockerignore)
COPY app/       ./app/
COPY alembic/   ./alembic/
COPY alembic.ini .
COPY data/      ./data/
COPY models/    ./models/
COPY pyproject.toml .

# SQLite DB lives in a named volume mounted at /data
ENV SQLITE_PATH=/data/bnpl.db \
    PERSISTENCE=sqlite \
    FORECAST_ENGINE=deterministic \
    AUTH_ENABLED=true

VOLUME ["/data"]

EXPOSE 8000

# Run alembic migrations then start uvicorn
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
