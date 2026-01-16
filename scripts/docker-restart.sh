#!/bin/bash
# ============================================
# Docker Restart Script (Linux/Mac)
# Updated: 2026-01-16
# ============================================

set -e

echo "========================================"
echo "Restarting Agentic RAG Docker Services"
echo "========================================"
echo ""

if [ -z "$1" ]; then
    echo "Restarting all services..."
    docker-compose restart
else
    echo "Restarting $1..."
    docker-compose restart "$1"
fi

echo ""
echo "========================================"
echo "Services restarted successfully!"
echo "========================================"
