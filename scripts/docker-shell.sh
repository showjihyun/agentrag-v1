#!/bin/bash
# ============================================
# Docker Shell Access Script (Linux/Mac)
# Updated: 2026-01-16
# ============================================

if [ -z "$1" ]; then
    echo "Usage: ./docker-shell.sh [service]"
    echo ""
    echo "Available services:"
    echo "  backend    - Backend API container"
    echo "  postgres   - PostgreSQL database"
    echo "  redis      - Redis cache"
    echo "  milvus     - Milvus vector database"
    echo ""
    echo "Example: ./docker-shell.sh backend"
    exit 1
fi

echo "Connecting to $1 container..."
docker-compose exec "$1" sh
