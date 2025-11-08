@echo off
chcp 65001 >nul
echo ========================================
echo Checking Backend Services
echo ========================================
echo.

echo Checking Docker containers...
docker ps --filter "name=agenticrag" --format "{{.Names}}: {{.Status}}"

echo.
echo Checking if services are running...

docker ps --filter "name=agenticrag-redis" --filter "status=running" -q >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis container not running. Starting...
    docker start agenticrag-redis
)

docker ps --filter "name=agenticrag-milvus" --filter "status=running" -q >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Milvus container not running. Starting...
    docker start agenticrag-milvus agenticrag-etcd agenticrag-minio
)

docker ps --filter "name=agenticrag-postgres" --filter "status=running" -q >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL container not running. Starting...
    docker start agenticrag-postgres
)

echo.
echo Waiting for services to be ready...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Services Status
echo ========================================
docker ps --filter "name=agenticrag" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ========================================
echo All services are ready!
echo ========================================
echo.
echo Redis:      localhost:6380
echo Milvus:     localhost:19530
echo PostgreSQL: localhost:5433
echo.
pause
