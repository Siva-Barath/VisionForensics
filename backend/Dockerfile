# =============================================================================
# VisionForensics AI — Backend Pilot Container Dockerfile
# Multi-stage / Hardened Python 3.10 Slim Runtime
# =============================================================================

FROM python:3.10-slim AS base

# Prevent Python from writing .pyc files and force unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=pilot

# Install OS dependencies for OpenCV, Poppler (PDF rendering), and LibMagic
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user and group
RUN groupadd -g 10001 visionforensics && \
    useradd -u 10001 -g visionforensics -s /bin/bash -m visionforensics

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir argon2-cffi PyJWT fpdf2 scikit-learn==1.3.2 joblib pypdf pandas pypdfium2

# Copy application source and ML models
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Create persistent storage mount points with correct unprivileged ownership
RUN mkdir -p /app/uploads /app/processed /app/reports /app/heatmaps && \
    chown -R visionforensics:visionforensics /app

# Switch to unprivileged execution user
USER visionforensics

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production ASGI server with exactly 1 worker process for controlled pilot
# Narrowly scopes trusted proxy to exact Nginx container IP (172.28.0.10) and localhost (127.0.0.1)
# (Note: Multi-worker or multi-instance deployments require distributed rate limiting such as Redis)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "172.28.0.10,127.0.0.1"]
