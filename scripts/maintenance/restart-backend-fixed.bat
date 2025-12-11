@echo off
echo ========================================
echo Restarting Backend Server (Fixed)
echo ========================================
echo.

REM Kill any existing uvicorn processes
echo Stopping existing backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

REM Check if venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo.
echo Starting FastAPI server with fixed PYTHONPATH...
echo.

REM Set PYTHONPATH to project root (critical for imports)
set PYTHONPATH=%CD%

REM Suppress warnings
set PYTHONWARNINGS=ignore::DeprecationWarning,ignore::UserWarning,ignore::FutureWarning
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

REM Start from project root (not backend directory)
cd /d "%~dp0"

echo Backend will be available at:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo.

REM Use python -m to ensure proper module resolution
python -m uvicorn backend.main:app --reload --port 8000 --reload-dir backend

pause
