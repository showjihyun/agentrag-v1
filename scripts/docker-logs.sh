#!/bin/bash
# ============================================
# Docker Logs Script (Linux/Mac)
# Updated: 2026-01-16
# ============================================

echo "========================================"
echo "Agentic RAG Docker Logs"
echo "========================================"
echo ""

if [ -z "$1" ]; then
    echo "Showing logs for all services..."
    docker-compose logs -f
else
    echo "Showing logs for $1..."
    docker-compose logs -f "$1"
fi
