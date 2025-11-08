@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Checking Server Status
echo ========================================
echo.

echo Checking port 8000 (Backend)...
netstat -ano | findstr :8000 | findstr LISTENING
if errorlevel 1 (
    echo [X] Backend NOT running on port 8000
) else (
    echo [OK] Backend is running on port 8000
)
echo.

echo Checking port 3000 (Frontend)...
netstat -ano | findstr :3000 | findstr LISTENING
if errorlevel 1 (
    echo [X] Frontend NOT running on port 3000
) else (
    echo [OK] Frontend is running on port 3000
)
echo.

echo ========================================
echo   Server URLs
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
pause
