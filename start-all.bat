@echo off
chcp 65001 >nul
echo ========================================
echo Starting Agentic RAG System
echo ========================================
echo.

REM Step 1: Start Docker services
echo [1/3] Starting backend services (Redis, Milvus, PostgreSQL)...
call start-services.bat
if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo.
echo [2/3] Starting backend server...
start "Agentic RAG - Backend" cmd /k "call start-backend-simple.bat"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting frontend...
start "Agentic RAG - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo System Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Check the new windows for logs.
echo.
pause
