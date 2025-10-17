#!/bin/bash
# Production startup script for 5-100 concurrent users

echo "Starting Agentic RAG System (Production Mode)"
echo "=============================================="

# Calculate optimal worker count
# Formula: (2 x CPU cores) + 1
CPU_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
WORKERS=$((2 * CPU_CORES + 1))

# Cap at 17 workers for stability
if [ $WORKERS -gt 17 ]; then
  WORKERS=17
fi

echo "Detected CPU cores: $CPU_CORES"
echo "Starting with $WORKERS workers (optimized for 5-100 concurrent users)"

# Create logs directory if not exists
mkdir -p backend/logs

cd backend

# Start with Gunicorn + Uvicorn workers
gunicorn main:app \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --worker-connections 1000 \
  --backlog 2048 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  --preload
