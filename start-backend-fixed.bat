@echo off
chcp 65001 >nul
echo ========================================
echo Starting Backend (Encoding Fix Applied)
echo ========================================
echo.

cd backend

REM Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Set Python to ignore encoding errors
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Temporarily rename .env to avoid pymilvus loading it
cd ..
if exist ".env" (
    echo [INFO] Temporarily moving .env to prevent encoding issues...
    move .env .env.temp >nul
)

REM Set environment variables manually from .env
for /f "usebackq tokens=1,* delims==" %%a in (".env.temp") do (
    set "line=%%a"
    setlocal enabledelayedexpansion
    if not "!line:~0,1!"=="#" (
        if not "!line!"=="" (
            endlocal
            set "%%a=%%b"
        ) else (
            endlocal
        )
    ) else (
        endlocal
    )
)

REM Restore .env
move .env.temp .env >nul

cd backend

echo.
echo Starting uvicorn on http://localhost:8000
echo Press Ctrl+C to stop
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
