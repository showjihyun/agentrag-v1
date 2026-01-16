# Docker Deployment Guide 🐳

**Updated:** January 16, 2026  
**Version:** 2.0 (Week 1-8 + Security)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Quick Start](#quick-start)
4. [Service Configuration](#service-configuration)
5. [Environment Variables](#environment-variables)
6. [Production Deployment](#production-deployment)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Docker-based deployment guide for the Agentic RAG system.

### Included Services

- **Backend API** - FastAPI application
- **PostgreSQL** - Main database
- **Redis** - Cache & session store
- **Milvus** - Vector database
- **Etcd** - Milvus metadata
- **MinIO** - Milvus object storage

### Optional Services

- **Jaeger** - Distributed tracing
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Nginx** - Reverse proxy (production)

---

## System Requirements

### Minimum Specifications (Development)
- **CPU:** 4 cores
- **RAM:** 8GB
- **Disk:** 20GB
- **Docker:** 20.10+
- **Docker Compose:** 2.0+

### Recommended Specifications (Production)
- **CPU:** 8+ cores
- **RAM:** 16GB+
- **Disk:** 100GB+ SSD
- **Docker:** 24.0+
- **Docker Compose:** 2.20+

---

## Quick Start

### 1. Environment Setup

```bash
# Create .env file
cp backend/.env.example backend/.env

# Edit .env file
nano backend/.env
```

### 2. Build Docker Images

```bash
# Linux/Mac
./scripts/docker-build.sh

# Windows
scripts\docker-build.bat
```

### 3. Start Services

```bash
# Linux/Mac
./scripts/docker-start.sh

# Windows
scripts\docker-start.bat

# Or run directly
docker-compose up -d
```

### 4. Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Verify Access

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## Service Configuration

### Backend API

```yaml
ports:
  - "8000:8000"
resources:
  cpus: 4
  memory: 8G
healthcheck:
  interval: 30s
  timeout: 10s
  retries: 3
```

**Key Features:**
- FastAPI application
- 4 workers (Uvicorn)
- Auto-restart
- Health check included

### PostgreSQL

```yaml
ports:
  - "5433:5432"
resources:
  cpus: 2
  memory: 4G
```

**Configuration:**
- Max connections: 200 (dev) / 500 (prod)
- Shared buffers: 512MB (dev) / 1GB (prod)
- Effective cache: 2GB (dev) / 4GB (prod)

### Redis

```yaml
ports:
  - "6380:6379"
resources:
  cpus: 2
  memory: 4G
```

**Configuration:**
- Max memory: 4GB (dev) / 8GB (prod)
- Eviction policy: allkeys-lru
- Persistence: AOF enabled

### Milvus

```yaml
ports:
  - "19530:19530"  # gRPC
  - "9092:9091"    # HTTP
resources:
  cpus: 4
  memory: 8G
```

**Configuration:**
- Max connections: 500 (dev) / 1000 (prod)
- Cache size: 4GB (dev) / 8GB (prod)

---

## Environment Variables

### Required Variables

```bash
# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/agenticrag
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### OAuth (Week 9-10)

```bash
# Google
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# GitHub
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# Microsoft
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
```

### Payment (Week 3-4)

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### LLM Providers

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=...
```

---

## Production Deployment

### 1. Build Production Image

```bash
docker build -f backend/Dockerfile.optimized -t agenticrag-backend:prod ./backend
```

### 2. Use Production Compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Configure Environment Variables

```bash
# Create .env.production file
cp backend/.env.example backend/.env.production

# Edit with production values
nano backend/.env.production
```

### 4. SSL/TLS Setup

```bash
# Nginx configuration
mkdir -p nginx/ssl
# Copy SSL certificates
cp your-cert.crt nginx/ssl/
cp your-key.key nginx/ssl/
```

### 5. Backup Setup

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres agenticrag > backup.sql

# Redis backup
docker-compose exec redis redis-cli SAVE
```

---

## Monitoring

### Start Monitoring Services

```bash
# Include monitoring profile
docker-compose --profile monitoring up -d
```

### Access URLs

- **Jaeger UI:** http://localhost:16686
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001
  - Username: admin
  - Password: admin

### Check Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/api/health
```

---

## Docker Commands

### Service Management

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Service status
docker-compose ps
```

### Container Access

```bash
# Backend shell
docker-compose exec backend bash

# PostgreSQL shell
docker-compose exec postgres psql -U postgres -d agenticrag

# Redis CLI
docker-compose exec redis redis-cli
```

### Data Management

```bash
# List volumes
docker volume ls

# Remove volumes (caution!)
docker-compose down -v

# Remove specific volume
docker volume rm agenticrag_postgres_data
```

### Image Management

```bash
# List images
docker images

# Remove image
docker rmi agenticrag-backend:latest

# Clean unused images
docker image prune -a
```

---

## Troubleshooting

### 1. Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Check health check
docker inspect agenticrag-backend | grep -A 10 Health
```

### 2. Database Connection Failed

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Test connection
docker-compose exec backend python -c "from backend.db.database import engine; print(engine.connect())"
```

### 3. Milvus Connection Failed

```bash
# Milvus health check
curl http://localhost:9092/healthz

# Check Etcd status
docker-compose exec etcd etcdctl endpoint health

# Check MinIO status
curl http://localhost:9003/minio/health/live
```

### 4. Out of Memory

```bash
# Check resource usage
docker stats

# Adjust memory limit (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 16G
```

### 5. Port Conflict

```bash
# Check port usage
netstat -tulpn | grep 8000

# Change port (docker-compose.yml)
ports:
  - "8001:8000"  # host:container
```

### 6. Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes
```

---

## Performance Optimization

### 1. Backend Optimization

```yaml
# Adjust worker count
CMD ["uvicorn", "main:app", "--workers", "8"]

# Or use Gunicorn
CMD ["gunicorn", "main:app", "--workers", "8", "--worker-class", "uvicorn.workers.UvicornWorker"]
```

### 2. PostgreSQL Optimization

```sql
-- Connection pool settings
max_connections = 500
shared_buffers = 2GB
effective_cache_size = 8GB
work_mem = 128MB
```

### 3. Redis Optimization

```bash
# Memory policy
maxmemory 16gb
maxmemory-policy allkeys-lru

# Connection count
maxclients 10000
```

### 4. Milvus Optimization

```yaml
environment:
  MILVUS_PROXY_MAX_CONNECTIONS: 2000
  MILVUS_QUERY_NODE_CACHE_SIZE: 16384
```

---

## Backup & Recovery

### PostgreSQL Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres agenticrag > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260116.sql | docker-compose exec -T postgres psql -U postgres agenticrag
```

### Redis Backup

```bash
# Backup
docker-compose exec redis redis-cli SAVE
docker cp agenticrag-redis:/data/dump.rdb ./backup/redis_$(date +%Y%m%d).rdb

# Restore
docker cp ./backup/redis_20260116.rdb agenticrag-redis:/data/dump.rdb
docker-compose restart redis
```

### Milvus Backup

```bash
# Volume backup
docker run --rm -v agenticrag_milvus_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/milvus_$(date +%Y%m%d).tar.gz /data
```

---

## Security Checklist

### Before Production Deployment

- [ ] Change all default passwords
- [ ] Generate SECRET_KEY, ENCRYPTION_KEY
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Close unnecessary ports
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Enable rate limiting
- [ ] Verify CORS settings

---

## Additional Resources

- **Docker Documentation:** https://docs.docker.com/
- **Docker Compose Documentation:** https://docs.docker.com/compose/
- **PostgreSQL Tuning:** https://pgtune.leopard.in.ua/
- **Redis Configuration:** https://redis.io/docs/management/config/
- **Milvus Documentation:** https://milvus.io/docs

---

**Author:** Kiro AI Assistant  
**Version:** 2.0  
**Last Updated:** 2026-01-16
