@echo off
chcp 65001 >nul
echo Starting Backend Server...
echo.

cd backend

REM Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Check if activation worked
python -c "import sys; print(f'Python: {sys.executable}')"
echo.

REM Set PYTHONPATH to project root
cd ..
set PYTHONPATH=%CD%
echo PYTHONPATH set to: %PYTHONPATH%
cd backend
echo.

REM Start uvicorn
echo Starting uvicorn on http://localhost:8000
echo Press Ctrl+C to stop
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
