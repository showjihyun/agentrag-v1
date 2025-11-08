@echo off
chcp 65001 >nul
REM ============================================
REM Run Database Migrations (Standalone)
REM ============================================

echo.
echo Running database migrations...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Please run setup-windows.bat first
    pause
    exit /b 1
)

REM Set PYTHONPATH to include project root
set PYTHONPATH=%~dp0..;%PYTHONPATH%

REM Run migrations
alembic upgrade head

if errorlevel 1 (
    echo.
    echo [ERROR] Migration failed!
    echo.
    echo Please check:
    echo 1. PostgreSQL is running
    echo 2. Database exists (CREATE DATABASE agent_builder;)
    echo 3. .env file has correct DATABASE_URL
    echo.
    echo Example DATABASE_URL:
    echo DATABASE_URL=postgresql://postgres:password@localhost:5432/agent_builder
    echo.
) else (
    echo.
    echo [SUCCESS] Migrations completed!
    echo.
)

deactivate
pause
