@echo off
chcp 65001 >nul
echo ========================================
echo Restarting Frontend Server
echo ========================================
echo.

echo Stopping any running Next.js processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Agent Builder - Frontend*" 2>nul
timeout /t 2 /nobreak >nul

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)

:found
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%IP%") do set IP=%%a

echo.
echo Starting frontend server on all network interfaces...
start "Agent Builder - Frontend" cmd /k "cd frontend && npm run dev -- -H 0.0.0.0"

echo.
echo Frontend restarted!
echo - Local:   http://localhost:3000
echo - Network: http://%IP%:3000
echo.
pause
