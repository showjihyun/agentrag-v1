#!/bin/bash
# ============================================
# Docker Clean Script (Linux/Mac)
# Updated: 2026-01-16
# WARNING: This will delete all data!
# ============================================

set -e

echo "========================================"
echo "Docker Clean - WARNING!"
echo "========================================"
echo ""
echo "This will:"
echo "- Stop all containers"
echo "- Remove all containers"
echo "- Remove all volumes (DATA WILL BE LOST!)"
echo "- Remove all networks"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo ""
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Stopping and removing everything..."
docker-compose down -v

echo ""
echo "Removing unused images..."
docker image prune -f

echo ""
echo "========================================"
echo "Cleanup completed!"
echo "========================================"
