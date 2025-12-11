@echo off
chcp 65001 >nul
echo ========================================
echo Quick Start - Agentic RAG
echo ========================================
echo.

echo [1/2] Checking Docker services...
docker ps --filter "name=agenticrag" --format "{{.Names}}: {{.Status}}" | findstr "Up" >nul
if errorlevel 1 (
    echo [WARNING] Some services are not running
    echo Starting Docker services...
    call start-services.bat
) else (
    echo [OK] All Docker services are running
)

echo.
echo [2/2] Starting backend server...
start "Agentic RAG - Backend" cmd /k "call start-backend-simple.bat"

echo.
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo System Ready!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To start frontend:
echo   cd frontend
echo   npm run dev
echo.
pause
