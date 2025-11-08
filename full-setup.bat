@echo off
chcp 65001 >nul
echo ========================================
echo Full System Setup
echo ========================================
echo.

echo [Step 1/4] Checking Docker services...
docker ps --filter "name=agenticrag" --format "{{.Names}}: {{.Status}}" | findstr "Up" >nul
if errorlevel 1 (
    echo [WARNING] Some Docker services are not running
    echo Please start Docker services first
    pause
    exit /b 1
)
echo [OK] Docker services are running
echo.

echo [Step 2/4] Setting up PostgreSQL database...
call setup-postgres.bat
if errorlevel 1 (
    echo [ERROR] Database setup failed
    pause
    exit /b 1
)

echo.
echo [Step 3/4] Stopping any running backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Agent Builder - Backend*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [Step 4/4] Starting backend server...
start "Agent Builder - Backend" cmd /k "call start-backend-simple.bat"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Check the backend window for logs.
echo.
pause
