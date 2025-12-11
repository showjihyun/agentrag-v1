@echo off
REM Backend Server Startup Script (Windows)
REM This script activates the virtual environment and starts the FastAPI server

echo ========================================
echo Agentic RAG Backend Server
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then install dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check if uvicorn is installed
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [ERROR] uvicorn not found!
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [2/3] Checking database connection...
REM You can add database connection check here if needed
echo [OK] Ready to start server
echo.

REM Start the server
echo [3/3] Starting FastAPI server...
echo.
echo ========================================
echo Server will start on: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo ReDoc: http://localhost:8000/redoc
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Change to parent directory so Python can find 'backend' module
cd ..
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

REM If server stops, deactivate venv
deactivate
