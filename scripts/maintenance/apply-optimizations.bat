@echo off
REM Apply backend optimizations (Database indexes + Caching)

echo ============================================================
echo Backend Optimization Application
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Change to backend directory
cd backend

echo.
echo ============================================================
echo Step 1: Running database migrations
echo ============================================================
echo.

REM Run Alembic migrations
alembic upgrade head

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Migration failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Verifying optimizations
echo ============================================================
echo.

REM Run verification script
python scripts/verify_optimizations.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Warning: Some verifications failed
    echo Please check the output above
) else (
    echo.
    echo ============================================================
    echo Success! All optimizations applied and verified
    echo ============================================================
)

echo.
echo ============================================================
echo Step 3: Restarting backend server
echo ============================================================
echo.

REM Go back to root
cd ..

echo Please restart your backend server to apply changes:
echo   1. Stop the current backend server (Ctrl+C)
echo   2. Run: start-backend.bat
echo.

pause
