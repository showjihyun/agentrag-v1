# ============================================
# Backend Dockerfile for Agentic RAG System
# Updated: 2026-01-16
# Includes: Week 1-8 + Security Dependencies
# ============================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# Includes: build tools, OCR dependencies, SAML dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    make \
    cmake \
    # Network tools
    curl \
    wget \
    # Database clients
    postgresql-client \
    # OCR dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Image processing
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    # PDF processing
    poppler-utils \
    # SAML dependencies (xmlsec)
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    pkg-config \
    # Git (for some Python packages)
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements.txt requirements-prod.txt ./

# Install Python dependencies
# Use production requirements for smaller image
RUN pip install --no-cache-dir -r requirements-prod.txt

# Install additional security dependencies
RUN pip install --no-cache-dir \
    Authlib==1.6.6 \
    python3-saml==1.16.0 \
    xmlsec==1.3.17

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    logs \
    uploads \
    data \
    .hypothesis

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/simple || exit 1

# Run database migrations on startup (optional, can be done separately)
# CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
