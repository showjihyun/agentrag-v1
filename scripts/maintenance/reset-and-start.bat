@echo off
chcp 65001 >nul
REM ============================================
REM Reset and Start Fresh
REM ============================================

echo.
echo ========================================
echo   Resetting Environment
echo ========================================
echo.

REM Stop any running servers
echo [1/5] Stopping any running servers...
call stop-windows.bat >nul 2>&1

REM Clean Python cache
echo [2/5] Cleaning Python cache...
if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__"
if exist "backend\alembic\__pycache__" rmdir /s /q "backend\alembic\__pycache__"
for /d /r backend %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM Clean .pyc files
echo [3/5] Cleaning .pyc files...
del /s /q backend\*.pyc >nul 2>&1

REM Remove SQLite database if exists
echo [4/5] Removing old database files...
if exist "backend\agenticrag.db" del /q "backend\agenticrag.db"
if exist "agenticrag.db" del /q "agenticrag.db"

REM Reload environment
echo [5/5] Environment cleaned.
echo.

echo ========================================
echo   Starting Fresh
echo ========================================
echo.

REM Check PostgreSQL
echo Checking PostgreSQL connection...
echo.

REM Try to connect to PostgreSQL
psql -U postgres -d postgres -c "SELECT version();" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Cannot connect to PostgreSQL.
    echo.
    echo Options:
    echo 1. Install PostgreSQL: https://www.postgresql.org/download/
    echo 2. Or use SQLite (automatic fallback)
    echo.
    echo Press any key to continue with SQLite...
    pause >nul
    
    REM Switch to SQLite
    powershell -Command "(Get-Content .env) -replace '^DATABASE_URL=.*', 'DATABASE_URL=sqlite:///./agenticrag.db' | Set-Content .env"
    echo Switched to SQLite mode.
) else (
    echo [OK] PostgreSQL is running.
    echo.
    
    REM Check if database exists
    psql -U postgres -d agenticrag -c "SELECT 1;" >nul 2>&1
    if errorlevel 1 (
        echo Database 'agenticrag' does not exist. Creating...
        psql -U postgres -c "CREATE DATABASE agenticrag;" >nul 2>&1
        if errorlevel 1 (
            echo [WARNING] Failed to create database.
            echo Switching to SQLite...
            powershell -Command "(Get-Content .env) -replace '^DATABASE_URL=.*', 'DATABASE_URL=sqlite:///./agenticrag.db' | Set-Content .env"
        ) else (
            echo [OK] Database created.
        )
    ) else (
        echo [OK] Database 'agenticrag' exists.
    )
)

echo.
echo ========================================
echo   Starting Servers
echo ========================================
echo.

REM Start servers
call start-windows.bat

