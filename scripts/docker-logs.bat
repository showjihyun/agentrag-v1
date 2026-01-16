@echo off
REM ============================================
REM Docker Logs Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo ========================================
echo Agentic RAG Docker Logs
echo ========================================
echo.

if "%1"=="" (
    echo Showing logs for all services...
    docker-compose logs -f
) else (
    echo Showing logs for %1...
    docker-compose logs -f %1
)
