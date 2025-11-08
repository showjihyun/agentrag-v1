@echo off
echo ========================================
echo Starting Backend Server (venv)
echo ========================================
echo.

REM Check if venv exists in backend directory
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found in backend\venv!
    echo Please run: cd backend ^&^& python -m venv venv
    echo Then install dependencies: backend\venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo.
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

python -m uvicorn backend.main:app --reload --port 8000
