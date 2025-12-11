@echo off
chcp 65001 >nul
REM ============================================
REM PostgreSQL Setup Helper
REM ============================================

echo.
echo ========================================
echo   PostgreSQL Setup Helper
echo ========================================
echo.

REM Check if psql is available
where psql >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL is not installed or not in PATH
    echo.
    echo Please install PostgreSQL:
    echo 1. Download from: https://www.postgresql.org/download/windows/
    echo 2. Install with default settings
    echo 3. Remember the password you set for 'postgres' user
    echo.
    pause
    exit /b 1
)

echo PostgreSQL is installed.
echo.

REM Get database details from user
echo Please enter your PostgreSQL details:
echo (Press Enter to use default values shown in brackets)
echo.

set /p DB_HOST="Host [localhost]: " || set DB_HOST=localhost
set /p DB_PORT="Port [5432]: " || set DB_PORT=5432
set /p DB_NAME="Database name [agenticrag]: " || set DB_NAME=agenticrag
set /p DB_USER="Username [postgres]: " || set DB_USER=postgres

REM Get password (hidden input not possible in batch, so just prompt)
echo.
echo Password for user '%DB_USER%':
set /p DB_PASSWORD="Password: "

echo.
echo ========================================
echo   Creating Database
echo ========================================
echo.

REM Try to create database
echo Creating database '%DB_NAME%'...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -c "CREATE DATABASE %DB_NAME%;" 2>nul

if errorlevel 1 (
    echo.
    echo Database might already exist or connection failed.
    echo Checking if database exists...
    
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT 1;" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to connect to database.
        echo Please check your credentials and try again.
        pause
        exit /b 1
    ) else (
        echo [OK] Database '%DB_NAME%' already exists and is accessible.
    )
) else (
    echo [OK] Database '%DB_NAME%' created successfully.
)

echo.
echo ========================================
echo   Updating .env File
echo ========================================
echo.

REM Create DATABASE_URL
set DATABASE_URL=postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%

echo Updating .env file with PostgreSQL settings...

REM Backup .env
if exist ".env" (
    copy .env .env.backup >nul
    echo Backup created: .env.backup
)

REM Update .env file (simple approach - replace the line)
powershell -Command "(Get-Content .env) -replace '^DATABASE_URL=.*', 'DATABASE_URL=%DATABASE_URL%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^POSTGRES_HOST=.*', 'POSTGRES_HOST=%DB_HOST%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^POSTGRES_PORT=.*', 'POSTGRES_PORT=%DB_PORT%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^POSTGRES_DB=.*', 'POSTGRES_DB=%DB_NAME%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^POSTGRES_USER=.*', 'POSTGRES_USER=%DB_USER%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^POSTGRES_PASSWORD=.*', 'POSTGRES_PASSWORD=%DB_PASSWORD%' | Set-Content .env"

echo [OK] .env file updated.

echo.
echo ========================================
echo   Running Migrations
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Please run setup-windows.bat first
    cd ..
    pause
    exit /b 1
)

REM Set PYTHONPATH
set PYTHONPATH=%~dp0;%PYTHONPATH%

echo Running database migrations...
alembic upgrade head

if errorlevel 1 (
    echo.
    echo [ERROR] Migration failed!
    echo Please check the error messages above.
    deactivate
    cd ..
    pause
    exit /b 1
)

deactivate
cd ..

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo PostgreSQL is configured and ready to use.
echo.
echo Database: %DB_NAME%
echo Host: %DB_HOST%:%DB_PORT%
echo User: %DB_USER%
echo.
echo You can now start the servers with:
echo   start-windows.bat
echo.
pause
