@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Clean Restart
echo ========================================
echo.

echo [1/6] Stopping all servers...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/6] Cleaning Python cache...
cd backend
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "alembic\__pycache__" rmdir /s /q "alembic\__pycache__"
if exist "db\__pycache__" rmdir /s /q "db\__pycache__"
if exist "services\__pycache__" rmdir /s /q "services\__pycache__"
if exist "api\__pycache__" rmdir /s /q "api\__pycache__"
del /s /q *.pyc >nul 2>&1
cd ..

echo [3/6] Removing old database...
if exist "backend\agenticrag.db" del /q "backend\agenticrag.db"
if exist "agenticrag.db" del /q "agenticrag.db"

echo [4/6] Checking .env file...
findstr /C:"DATABASE_URL=postgresql" .env >nul
if errorlevel 1 (
    echo [WARNING] DATABASE_URL not set to PostgreSQL
    echo Current setting:
    findstr /C:"DATABASE_URL" .env
) else (
    echo [OK] DATABASE_URL is set to PostgreSQL
)

echo [5/6] Testing PostgreSQL connection...
psql -U postgres -d postgres -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot connect to PostgreSQL
    echo.
    echo Please check:
    echo 1. PostgreSQL is installed
    echo 2. PostgreSQL service is running
    echo 3. Password is correct
    echo.
    echo Switching to SQLite for now...
    powershell -Command "(Get-Content .env) -replace '^DATABASE_URL=.*', 'DATABASE_URL=sqlite:///./agenticrag.db' | Set-Content .env"
) else (
    echo [OK] PostgreSQL connection successful
    
    REM Create database if not exists
    psql -U postgres -d agenticrag -c "SELECT 1;" >nul 2>&1
    if errorlevel 1 (
        echo Creating database 'agenticrag'...
        psql -U postgres -c "CREATE DATABASE agenticrag;"
    )
)

echo [6/6] Starting servers with virtual environment...
echo.

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup-windows.bat first.
    pause
    exit /b 1
)

echo Virtual environment found. Starting servers...
call start-windows.bat
