#!/bin/bash
# ============================================
# Docker Migration Script (Linux/Mac)
# Updated: 2026-01-16
# ============================================

set -e

echo "========================================"
echo "Running Database Migrations"
echo "========================================"
echo ""

# Check if backend is running
if ! docker-compose ps backend | grep -q "Up"; then
    echo "ERROR: Backend container is not running!"
    echo "Please start services first: ./scripts/docker-start.sh"
    exit 1
fi

# Run migrations
echo "Running Alembic migrations..."
docker-compose exec backend alembic upgrade head

echo ""
echo "========================================"
echo "Migrations completed successfully!"
echo "========================================"
