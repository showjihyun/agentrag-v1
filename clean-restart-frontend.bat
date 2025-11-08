@echo off
chcp 65001 >nul
echo ========================================
echo Clean Restart Frontend
echo ========================================
echo.

echo Stopping frontend...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Agent Builder - Frontend*" 2>nul
timeout /t 2 /nobreak >nul

cd frontend

echo Cleaning build cache...
if exist ".next" (
    rmdir /s /q ".next"
    echo [OK] Build cache cleared
)

echo.
echo Starting frontend...
start "Agent Builder - Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Frontend Restarted!
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo.
echo Please wait for the build to complete...
echo.
pause
