@echo off
setlocal

echo.
echo ================================================================================
echo  Starting Complete Agentic RAG System
echo ================================================================================
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop and make sure it's running.
    pause
    exit /b 1
)

echo INFO: Docker is available

REM Step 1: Start services
echo.
echo [1/3] Starting required services...
docker-compose up -d postgres redis milvus

if %errorlevel% neq 0 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo SUCCESS: Services started

REM Step 2: Wait for services to be ready
echo.
echo [2/3] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Step 3: Start backend
echo.
echo [3/3] Starting backend server...
echo.
echo Service Information:
echo    Backend API:    http://localhost:8000
echo    Frontend:       http://localhost:3000 (start separately)
echo    PostgreSQL:     localhost:5433
echo    Redis:          localhost:6380  
echo    Milvus:         localhost:19530
echo.
echo WARNING: Press Ctrl+C to stop the backend server
echo INFO: To stop all services, run: docker-compose down
echo.
echo --------------------------------------------------------------------------------
echo.

REM Start backend (this will block)
call start-backend.bat