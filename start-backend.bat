@echo off
setlocal

echo.
echo ================================================================================
echo  Starting Agentic RAG Backend Server
echo ================================================================================
echo.

REM Set up paths
set PROJECT_ROOT=%~dp0
set BACKEND_PATH=%PROJECT_ROOT%backend
set VENV_PATH=%BACKEND_PATH%\venv

REM Validate project structure
if not exist "%BACKEND_PATH%" (
    echo ERROR: Backend directory not found!
    echo Please ensure you're running this script from the project root directory.
    pause
    exit /b 1
)

REM Set working directory and environment
cd /d "%PROJECT_ROOT%"
set PYTHONPATH=%PROJECT_ROOT%
set PYTHONWARNINGS=ignore::DeprecationWarning,ignore::UserWarning,ignore::FutureWarning
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set DEBUG=True

REM Determine Python executable
set PYTHON_EXE=
if exist "%VENV_PATH%\Scripts\python.exe" (
    set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
    echo OK: Using virtual environment
    goto :python_found
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    echo WARNING: Using system Python - virtual environment recommended
    goto :python_found
)

echo ERROR: Python not found! Please install Python or create a virtual environment.
pause
exit /b 1

:python_found
REM Stop existing processes
echo INFO: Stopping existing backend processes...
taskkill /F /IM python.exe /FI "COMMANDLINE eq *backend.main*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Display server information
echo.
echo Server Information:
echo    Backend API:    http://localhost:8000
echo    API Docs:       http://localhost:8000/docs
echo    Health Check:   http://localhost:8000/api/health
echo.
echo Related Services:
echo    Frontend:       http://localhost:3000
echo    PostgreSQL:     localhost:5433
echo    Redis:          localhost:6380
echo    Milvus:         localhost:19530
echo.
echo WARNING: Press Ctrl+C to stop the server
echo.
echo --------------------------------------------------------------------------------
echo.

REM Start the server
echo INFO: Starting server...
"%PYTHON_EXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start server
    echo Common issues:
    echo    Missing dependencies: pip install -r backend/requirements.txt
    echo    Port already in use: Check if another server is running
    echo    Database not running: Start with docker-compose up -d
    pause
    exit /b 1
)

echo.
echo INFO: Server stopped
pause