@echo off
chcp 65001 >nul
REM ============================================
REM Agent Builder - Windows Start Script (Debug)
REM ============================================

echo.
echo ========================================
echo   Agent Builder Starting (Debug Mode)...
echo ========================================
echo.

REM Check environment file
if not exist ".env" (
    echo [WARNING] .env file not found.
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env >nul
        echo .env file created successfully.
        echo.
    ) else (
        echo [ERROR] .env.example not found.
        pause
        exit /b 1
    )
) else (
    echo [OK] .env file found.
)

REM Check Python version
echo [1/6] Checking Python version...
python --version 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    pause
    exit /b 1
)
echo [OK] Python check passed.
echo.

REM Check Node.js version
echo [2/6] Checking Node.js version...
node --version 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed.
    pause
    exit /b 1
)
echo [OK] Node.js check passed.
echo.

REM Check backend dependencies
echo [3/6] Checking backend dependencies...
if not exist "backend\venv" (
    echo [INFO] Creating virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        cd ..
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo [INFO] Installing packages...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
) else (
    echo [OK] Virtual environment exists.
)
echo [OK] Backend dependencies check passed.
echo.

REM Check frontend dependencies
echo [4/6] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo [INFO] Installing npm packages...
    cd frontend
    call npm install
    cd ..
) else (
    echo [OK] node_modules exists.
)
echo [OK] Frontend dependencies check passed.
echo.

REM Skip database migration for now
echo [5/6] Skipping database migrations...
echo [INFO] You can run migrations manually later if needed.
echo.

REM Start servers
echo [6/6] Starting servers...
echo.

REM Start backend server
echo [INFO] Starting backend server...
start "Agent Builder - Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start frontend server
echo [INFO] Starting frontend server...
start "Agent Builder - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Servers started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Check the new windows for logs.
echo.
pause
