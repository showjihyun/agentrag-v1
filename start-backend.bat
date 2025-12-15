@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Agentic RAG Backend Server - Simple Startup Script
REM ============================================================================
REM 
REM Simple script to start the FastAPI backend server from project root
REM 
REM Usage: start-backend.bat
REM ============================================================================

REM Color codes for better UX
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "GRAY=[90m"
set "RESET=[0m"

echo.
echo %CYAN%================================================================================
echo  🚀 Starting Agentic RAG Backend Server
echo ================================================================================%RESET%
echo.

REM Set up paths
set "PROJECT_ROOT=%~dp0"
set "BACKEND_PATH=%PROJECT_ROOT%backend"
set "VENV_PATH=%BACKEND_PATH%\venv"

REM Validate project structure
if not exist "%BACKEND_PATH%" (
    echo %RED%❌ Backend directory not found!%RESET%
    echo %RED%Please ensure you're running this script from the project root directory.%RESET%
    pause
    exit /b 1
)

REM Set working directory and environment
cd /d "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
set "PYTHONWARNINGS=ignore::DeprecationWarning,ignore::UserWarning,ignore::FutureWarning"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

REM Determine Python executable
set "PYTHON_EXE="
if exist "%VENV_PATH%\Scripts\python.exe" (
    set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"
    echo %GREEN%✅ Using virtual environment%RESET%
) else (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo %YELLOW%⚠️  Using system Python (virtual environment recommended)%RESET%
    ) else (
        echo %RED%❌ Python not found! Please install Python or create a virtual environment.%RESET%
        pause
        exit /b 1
    )
)

REM Stop existing processes
echo %GRAY%🔄 Stopping existing backend processes...%RESET%
taskkill /F /IM python.exe /FI "COMMANDLINE eq *backend.main*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Display server information
echo.
echo %CYAN%📡 Server Information:%RESET%
echo %GREEN%   • Backend API:    http://localhost:8000%RESET%
echo %GREEN%   • API Docs:       http://localhost:8000/docs%RESET%
echo %GREEN%   • Health Check:   http://localhost:8000/api/health%RESET%
echo.
echo %CYAN%🌐 Related Services:%RESET%
echo %GRAY%   • Frontend:       http://localhost:3000%RESET%
echo %GRAY%   • PostgreSQL:     localhost:5433%RESET%
echo %GRAY%   • Redis:          localhost:6380%RESET%
echo %GRAY%   • Milvus:         localhost:19530%RESET%
echo.
echo %YELLOW%⚠️  Press Ctrl+C to stop the server%RESET%
echo.
echo %CYAN%────────────────────────────────────────────────────────────────────────────────%RESET%
echo.

REM Start the server
echo %GREEN%🚀 Starting server...%RESET%
"%PYTHON_EXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

if !errorlevel! neq 0 (
    echo.
    echo %RED%❌ Failed to start server%RESET%
    echo %GRAY%Common issues:%RESET%
    echo %GRAY%   • Missing dependencies: pip install -r backend/requirements.txt%RESET%
    echo %GRAY%   • Port already in use: Check if another server is running%RESET%
    echo %GRAY%   • Database not running: Start with docker-compose up -d%RESET%
    pause
    exit /b 1
)

echo.
echo %YELLOW%🛑 Server stopped%RESET%
pause