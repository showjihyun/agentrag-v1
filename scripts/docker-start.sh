#!/bin/bash
# ============================================
# Docker Start Script
# Updated: 2026-01-16
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Agentic RAG System...${NC}"

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your configuration${NC}"
fi

# Start services
echo -e "${BLUE}Starting Docker Compose services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}Checking service health...${NC}"
docker-compose ps

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker-compose exec backend alembic upgrade head || echo -e "${YELLOW}⚠️  Migrations failed or already up to date${NC}"

echo ""
echo -e "${GREEN}✅ Agentic RAG System started successfully!${NC}"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5433"
echo "  - Redis: localhost:6380"
echo "  - Milvus: localhost:19530"
echo "  - MinIO Console: http://localhost:9002"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f backend"
echo ""
echo "To stop:"
echo "  docker-compose down"
