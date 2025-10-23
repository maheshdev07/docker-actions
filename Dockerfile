# ============================================================
# STAGE 1: Builder - Install dependencies
# ============================================================
# Use official Python slim image as base
FROM python:3.11-slim AS builder

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements file
COPY requirements.txt .

# Create wheel files for all dependencies (reduces installation time in runtime stage)
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================================
# STAGE 2: Runtime - Minimal production image
# ============================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Set working directory
WORKDIR /app

# Create non-root user for security (don't run as root)
RUN groupadd -r scraper && useradd -r -g scraper scraper

# Copy pip wheels from builder stage
COPY --from=builder /app/wheels /wheels

# Copy requirements from builder stage
COPY --from=builder /app/requirements.txt .

# Install Python dependencies from wheels (faster than pip install)
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Copy application source code
COPY src/ ./src/
COPY .env.example ./.env

# Create volume mount points (for data persistence)
VOLUME ["/app/data", "/app/logs"]

# Switch to non-root user for security
USER scraper

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.scraper; print('healthy')" || exit 1

# Default command to run scraper
CMD ["python", "src/scraper.py"]
