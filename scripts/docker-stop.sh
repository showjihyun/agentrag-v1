#!/bin/bash
# ============================================
# Docker Stop Script (Linux/Mac)
# Updated: 2026-01-16
# ============================================

set -e

echo "========================================"
echo "Stopping Agentic RAG Docker Services"
echo "========================================"
echo ""

# Stop all services
docker-compose down

echo ""
echo "========================================"
echo "Services stopped successfully!"
echo "========================================"
