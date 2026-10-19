# ==============================================================================
# Production Dockerfile for AI Knowledge Base FastAPI Backend
# ==============================================================================
FROM python:3.12-slim

# System dependencies: curl for container health checks, sqlite3 for database ops
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Optimize Python execution and configure default container paths
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    APP_PORT=8000 \
    APP_HOST=0.0.0.0 \
    DATA_DIR=/app/data \
    RAW_DOCUMENTS_DIR=/app/data/raw_documents \
    VECTOR_STORE_DIR=/app/data/vector_store \
    EVAL_DATASETS_DIR=/app/data/eval_datasets \
    METADATA_DB_PATH=/app/data/metadata.db

# Create unprivileged application user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 -m -s /bin/bash appuser

WORKDIR /app

# Install Python requirements before copying application code for Docker layer caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend codebase and configuration
COPY backend/ ./backend/
COPY pytest.ini ./

# Ensure storage directories exist and assign ownership to appuser
RUN mkdir -p /app/data/raw_documents /app/data/vector_store /app/data/eval_datasets && \
    chown -R appuser:appuser /app

# Switch to unprivileged runtime user
USER appuser

# Expose container network port
EXPOSE 8000

# Container liveness & readiness check using application /ready probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ready || exit 1

# Start ASGI server binding to 0.0.0.0 and dynamically resolving platform $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
