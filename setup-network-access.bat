@echo off
REM ============================================
REM Network Access Setup Script
REM Configure the system for local network access
REM ============================================

echo ============================================
echo Network Access Setup
echo ============================================
echo.

REM Get local IP address
echo Detecting your local IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)

:found
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%IP%") do set IP=%%a

echo.
echo Your local IP address: %IP%
echo.
echo ============================================
echo Configuration Instructions
echo ============================================
echo.
echo 1. Backend Configuration (.env file):
echo    - Copy backend/.env.example to backend/.env
echo    - Update CORS_ORIGINS to include:
echo      CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://%IP%:3000
echo.
echo 2. Frontend Configuration (.env.local file):
echo    - Copy frontend/.env.local.example to frontend/.env.local
echo    - Update the following variables:
echo      NEXT_PUBLIC_API_URL=http://%IP%:8000
echo      NEXT_PUBLIC_BASE_URL=http://%IP%:3000
echo.
echo 3. Start the services:
echo    - Backend: cd backend ^&^& uvicorn main:app --host 0.0.0.0 --port 8000
echo    - Frontend: cd frontend ^&^& npm run dev -- -H 0.0.0.0
echo.
echo 4. Access from other devices:
echo    - Frontend: http://%IP%:3000
echo    - Backend API: http://%IP%:8000
echo    - API Docs: http://%IP%:8000/docs
echo.
echo ============================================
echo Firewall Configuration
echo ============================================
echo.
echo You may need to allow these ports in Windows Firewall:
echo    - Port 3000 (Frontend)
echo    - Port 8000 (Backend)
echo.
echo Run these commands as Administrator:
echo    netsh advfirewall firewall add rule name="AgenticRAG Frontend" dir=in action=allow protocol=TCP localport=3000
echo    netsh advfirewall firewall add rule name="AgenticRAG Backend" dir=in action=allow protocol=TCP localport=8000
echo.

pause
