@echo off
REM ============================================
REM Docker Shell Access Script (Windows)
REM Updated: 2026-01-16
REM ============================================

if "%1"=="" (
    echo Usage: docker-shell.bat [service]
    echo.
    echo Available services:
    echo   backend    - Backend API container
    echo   postgres   - PostgreSQL database
    echo   redis      - Redis cache
    echo   milvus     - Milvus vector database
    echo.
    echo Example: docker-shell.bat backend
    exit /b 1
)

echo Connecting to %1 container...
docker-compose exec %1 sh
