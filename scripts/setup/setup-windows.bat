@echo off
chcp 65001 >nul
REM ============================================
REM Agent Builder - Setup Script (One-time)
REM ============================================

echo.
echo ========================================
echo   Agent Builder Setup
echo ========================================
echo.

REM Create .env
if not exist ".env" (
    if exist ".env.example" (
        echo [1/4] Creating .env file...
        copy .env.example .env >nul
        echo .env created. Please review the configuration.
    )
) else (
    echo [1/4] .env file already exists.
)
echo.

REM Setup backend
echo [2/4] Setting up backend...
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
    
    echo Installing Python packages...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages
        deactivate
        cd ..
        pause
        exit /b 1
    )
    deactivate
    cd ..
    echo Backend setup complete.
) else (
    echo Backend already set up.
)
echo.

REM Setup frontend
echo [3/4] Setting up frontend...
if not exist "frontend\node_modules" (
    echo Installing npm packages...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm packages
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo Frontend setup complete.
) else (
    echo Frontend already set up.
)
echo.

REM Database migration
echo [4/4] Running database migrations...
cd backend
call venv\Scripts\activate.bat

REM Set PYTHONPATH to include project root
set PYTHONPATH=%~dp0;%PYTHONPATH%

alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Database migration failed.
    echo This is normal if database is not set up yet.
    echo Please set up PostgreSQL and update .env file, then run:
    echo   cd backend
    echo   venv\Scripts\activate.bat
    echo   alembic upgrade head
)
deactivate
cd ..
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review .env file and update if needed
echo 2. Make sure PostgreSQL is running
echo 3. Make sure Redis is running
echo 4. Make sure Milvus is running
echo 5. Run: quick-start.bat
echo.
pause
