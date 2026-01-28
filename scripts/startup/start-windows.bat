@echo off
chcp 65001 >nul
REM ============================================
REM Agent Builder - Windows Start Script
REM ============================================

echo.
echo ========================================
echo   Agent Builder Starting...
echo ========================================
echo.

REM Check environment file
if not exist ".env" (
    echo [WARNING] .env file not found.
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env >nul
        echo .env file created successfully.
        echo Please review and update the configuration if needed.
        echo.
    ) else (
        echo [ERROR] .env.example not found. Cannot create .env file.
        echo Please create .env file manually.
        pause
        exit /b 1
    )
) else (
    echo .env file found.
)

REM Check Python version
echo [1/6] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.10+: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js version
echo [2/6] Checking Node.js version...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed.
    echo Please install Node.js 18+: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM Check backend dependencies
echo [3/6] Checking backend dependencies...
if not exist "backend\venv" (
    echo Virtual environment not found. Creating...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo Installing Python packages...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python packages
        deactivate
        cd ..
        pause
        exit /b 1
    )
    deactivate
    cd ..
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
    echo Verifying critical packages...
    cd backend
    call venv\Scripts\activate.bat
    python -c "import pymilvus" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Some packages are missing. Reinstalling...
        pip install -r requirements.txt
    ) else (
        echo [OK] All packages verified.
    )
    deactivate
    cd ..
)
echo.

REM Check frontend dependencies
echo [4/6] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo node_modules not found. Installing...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm packages
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo npm packages installed successfully.
) else (
    echo node_modules already exists.
)
echo.

REM Database migration
echo [5/6] Running database migrations...
cd backend
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    cd ..
    pause
    exit /b 1
)

REM Set PYTHONPATH to include project root
set PYTHONPATH=%~dp0;%PYTHONPATH%

alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Database migration failed.
    echo This is normal if database is not set up yet.
    echo You can run migrations later after setting up PostgreSQL.
)
call deactivate
cd ..
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :ip_found
)

:ip_found
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%LOCAL_IP%") do set LOCAL_IP=%%a

REM Start servers
echo [6/6] Starting servers...
echo.
echo ========================================
echo   Backend:
echo   - Local:   http://localhost:8000
echo   - Network: http://%LOCAL_IP%:8000
echo   - Docs:    http://%LOCAL_IP%:8000/docs
echo.
echo   Frontend:
echo   - Local:   http://localhost:3000
echo   - Network: http://%LOCAL_IP%:3000
echo ========================================
echo.
echo Press Ctrl+C to stop servers.
echo.

REM Start backend server (new window with virtual environment)
start "Agent Builder - Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server (new window)
start "Agent Builder - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- -H 0.0.0.0"

echo.
echo ========================================
echo   Servers started successfully!
echo ========================================
echo.
echo Backend:
echo - Local:   http://localhost:8000
echo - Network: http://%LOCAL_IP%:8000
echo.
echo Frontend:
echo - Local:   http://localhost:3000
echo - Network: http://%LOCAL_IP%:3000
echo.
echo Check the new windows for server logs.
echo Close those windows to stop the servers.
echo.
pause
