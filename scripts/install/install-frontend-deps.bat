@echo off
chcp 65001 >nul
echo ========================================
echo Installing Frontend Dependencies
echo ========================================
echo.

cd frontend

echo Installing missing packages...
call npm install next-themes

if errorlevel 1 (
    echo [ERROR] Failed to install packages
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Please restart the frontend server.
echo.
pause
