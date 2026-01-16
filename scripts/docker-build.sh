#!/bin/bash
# ============================================
# Docker Build Script
# Updated: 2026-01-16
# ============================================

set -e

echo "🐳 Building Docker images..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Build backend image
echo -e "${BLUE}Building backend image...${NC}"
docker build -t agenticrag-backend:latest ./backend

# Build optimized backend image
echo -e "${BLUE}Building optimized backend image...${NC}"
docker build -f ./backend/Dockerfile.optimized -t agenticrag-backend:optimized ./backend

echo -e "${GREEN}✅ Docker images built successfully!${NC}"
echo ""
echo "Available images:"
docker images | grep agenticrag-backend
