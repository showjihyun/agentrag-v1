#!/bin/bash
# Deployment script for Agentic RAG System

set -e

echo "🚀 Agentic RAG System Deployment Script"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production file not found${NC}"
    echo "Please copy .env.production.example to .env.production and configure it"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

echo -e "${GREEN}✅ Environment variables loaded${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
echo "🔨 Building custom images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

services=("postgres" "redis" "milvus" "backend" "frontend")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*healthy"; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  $service is not healthy yet${NC}"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not healthy yet. Check logs with:${NC}"
    echo "docker-compose -f docker-compose.prod.yml logs -f"
fi

echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🌐 Access URLs:"
echo "  - Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo "  - Backend API: http://localhost:${BACKEND_PORT:-8000}"
echo "  - API Docs: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  - Restart service: docker-compose -f docker-compose.prod.yml restart <service>"
echo ""
