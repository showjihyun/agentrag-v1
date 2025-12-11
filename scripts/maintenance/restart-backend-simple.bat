@echo off
echo ========================================
echo Backend Server - Simple Restart
echo ========================================
echo.

echo [1/4] Stopping existing processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Setting up environment...
set PYTHONPATH=%CD%
set PYTHONWARNINGS=ignore

echo [3/4] Activating virtual environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)
call backend\venv\Scripts\activate.bat

echo [4/4] Starting server (no auto-reload)...
echo.
echo Server will be available at:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn backend.main:app --port 8000

pause
