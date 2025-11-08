@echo off
chcp 65001 >nul
echo ========================================
echo Restarting Frontend Server
echo ========================================
echo.

echo Stopping any running Next.js processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Agent Builder - Frontend*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting frontend server...
start "Agent Builder - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Frontend restarted!
echo Frontend: http://localhost:3000
echo.
pause
