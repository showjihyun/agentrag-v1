@echo off
REM ============================================
REM Docker Restart Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo ========================================
echo Restarting Agentic RAG Docker Services
echo ========================================
echo.

if "%1"=="" (
    echo Restarting all services...
    docker-compose restart
) else (
    echo Restarting %1...
    docker-compose restart %1
)

echo.
echo ========================================
echo Services restarted successfully!
echo ========================================
