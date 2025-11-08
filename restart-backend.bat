@echo off
chcp 65001 >nul
echo ========================================
echo Restarting Backend Server
echo ========================================
echo.

echo Stopping any running uvicorn processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Agent Builder - Backend*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend server...
start "Agent Builder - Backend" cmd /k "call start-backend-simple.bat"

echo.
echo Backend restarted!
echo.
pause
