@echo off
chcp 65001 >nul
echo ========================================
echo Force Restart Backend
echo ========================================
echo.

echo Killing all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul

echo Starting backend...
start "Agent Builder - Backend" cmd /k "call start-backend-simple.bat"

echo.
echo ========================================
echo Backend Restarted!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo.
echo Check the backend window for DEBUG mode message.
echo You should see: "DEBUG mode enabled (DEBUG=True)"
echo.
pause
