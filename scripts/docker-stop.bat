@echo off
REM ============================================
REM Docker Stop Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo ========================================
echo Stopping Agentic RAG Docker Services
echo ========================================
echo.

REM Stop all services
docker-compose down

echo.
echo ========================================
echo Services stopped successfully!
echo ========================================
