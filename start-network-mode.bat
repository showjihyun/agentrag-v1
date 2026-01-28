@echo off
REM ============================================
REM Start Services in Network Mode
REM Allows access from local network devices
REM ============================================

echo ============================================
echo Starting Services in Network Mode
echo ============================================
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)

:found
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%IP%") do set IP=%%a

echo Your local IP address: %IP%
echo.
echo Services will be accessible at:
echo   Frontend: http://%IP%:3000
echo   Backend:  http://%IP%:8000
echo   API Docs: http://%IP%:8000/docs
echo.

REM Check if .env files exist
if not exist "backend\.env" (
    echo ERROR: backend\.env not found!
    echo Please copy backend\.env.example to backend\.env and configure it.
    echo Run setup-network-access.bat for instructions.
    pause
    exit /b 1
)

if not exist "frontend\.env.local" (
    echo ERROR: frontend\.env.local not found!
    echo Please copy frontend\.env.local.example to frontend\.env.local and configure it.
    echo Run setup-network-access.bat for instructions.
    pause
    exit /b 1
)

echo Starting Backend on 0.0.0.0:8000...
start "AgenticRAG Backend" cmd /k "cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 /nobreak >nul

echo Starting Frontend on 0.0.0.0:3000...
start "AgenticRAG Frontend" cmd /k "cd frontend && npm run dev -- -H 0.0.0.0"

echo.
echo ============================================
echo Services Started!
echo ============================================
echo.
echo Access from any device on your network:
echo   Frontend: http://%IP%:3000
echo   Backend:  http://%IP%:8000
echo.
echo Press any key to stop all services...
pause >nul

REM Kill the services
taskkill /FI "WINDOWTITLE eq AgenticRAG Backend*" /F
taskkill /FI "WINDOWTITLE eq AgenticRAG Frontend*" /F

echo Services stopped.
pause
