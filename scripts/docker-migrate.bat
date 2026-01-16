@echo off
REM ============================================
REM Docker Migration Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo ========================================
echo Running Database Migrations
echo ========================================
echo.

REM Check if backend is running
docker-compose ps backend | findstr "Up" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Backend container is not running!
    echo Please start services first: scripts\docker-start.bat
    pause
    exit /b 1
)

REM Run migrations
echo Running Alembic migrations...
docker-compose exec backend alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Migrations completed successfully!
    echo ========================================
) else (
    echo.
    echo ERROR: Migration failed!
    echo Check logs: scripts\docker-logs.bat backend
)

echo.
pause
