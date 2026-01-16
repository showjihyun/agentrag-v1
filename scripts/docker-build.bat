@echo off
REM ============================================
REM Docker Build Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo ========================================
echo Building Agentic RAG Docker Images
echo ========================================
echo.

REM Check if .env exists
if not exist "backend\.env" (
    echo WARNING: backend\.env not found!
    echo Copying from backend\.env.example...
    copy backend\.env.example backend\.env
    echo.
    echo IMPORTANT: Please edit backend\.env with your configuration!
    echo.
    pause
)

REM Build backend image
echo Building backend image...
docker build -t agenticrag-backend:latest -f backend/Dockerfile backend/

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Backend build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit backend\.env with your configuration
echo 2. Run: scripts\docker-start.bat
echo.
pause
