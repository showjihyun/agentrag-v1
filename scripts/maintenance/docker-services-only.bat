@echo off
REM Start only Docker infrastructure services (PostgreSQL, Redis, Milvus)

echo ========================================
echo Starting Agentic RAG Infrastructure
echo ========================================
echo.

REM Check Docker
echo Checking Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)
echo Docker is running.
echo.

REM Start services
echo Starting infrastructure services:
echo - PostgreSQL (Port 5432)
echo - Redis (Port 6379)
echo - Milvus (Port 19530)
echo - Etcd (for Milvus)
echo - MinIO (for Milvus storage)
echo.

docker-compose up -d postgres redis etcd minio milvus

echo.
echo Waiting for services to be ready...
timeout /t 15 /nobreak >nul

REM Check service status
echo.
echo ========================================
echo Service Status
echo ========================================
docker-compose ps postgres redis milvus

echo.
echo ========================================
echo Infrastructure Ready!
echo ========================================
echo.
echo PostgreSQL: localhost:5433
echo   Database: agenticrag
echo   User: postgres
echo   Password: postgres
echo.
echo Redis: localhost:6380
echo.
echo Milvus: localhost:19531
echo.
echo MinIO Console: http://localhost:9002
echo.
echo To stop services: docker-compose down
echo To view logs: docker-compose logs -f
echo.
pause
