@echo off
echo ========================================
echo Starting Backend Server
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo Starting FastAPI server...
echo.
echo Backend will be available at:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo.

REM Set PYTHONPATH to include the project root
set PYTHONPATH=%CD%

REM Suppress Python warnings (including Pydantic deprecation warnings)
set PYTHONWARNINGS=ignore::DeprecationWarning,ignore::UserWarning,ignore::FutureWarning
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_DISABLE_TORCH_LOAD_CHECK=1

venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
