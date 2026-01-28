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

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)

:found
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%IP%") do set IP=%%a

echo.
echo [2/3] Starting backend server...
start "Agentic RAG - Backend" cmd /k "call start-backend-simple.bat"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting frontend...
start "Agentic RAG - Frontend" cmd /k "cd frontend && npm run dev -- -H 0.0.0.0"

echo.
echo ========================================
echo System Started!
echo ========================================
echo.
echo Backend:
echo - Local:   http://localhost:8000
echo - Network: http://%IP%:8000
echo - Docs:    http://%IP%:8000/docs
echo.
echo Frontend:
echo - Local:   http://localhost:3000
echo - Network: http://%IP%:3000
echo.
echo Check the new windows for logs.
echo.
pause
