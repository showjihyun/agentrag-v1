@echo off
chcp 65001 >nul
REM ============================================
REM Fix Dependencies - Reinstall packages
REM ============================================

echo.
echo ========================================
echo   Fixing Dependencies
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo [ERROR] Virtual environment not found!
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    cd ..
)

echo [1/3] Activating virtual environment...
cd backend
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    cd ..
    pause
    exit /b 1
)

echo [2/3] Upgrading pip...
python -m pip install --upgrade pip

echo [3/6] Uninstalling existing grpcio and pymilvus...
pip uninstall -y grpcio pymilvus 2>nul

echo [4/6] Installing grpcio binary (no compilation)...
pip install --only-binary=:all: grpcio
if errorlevel 1 (
    echo [ERROR] Failed to install grpcio binary
    deactivate
    cd ..
    pause
    exit /b 1
)

echo [5/6] Installing pymilvus without dependencies...
pip install --no-deps pymilvus

echo [6/6] Installing all dependencies...
echo This may take a few minutes...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo.
    echo Please check:
    echo 1. Internet connection
    echo 2. requirements.txt file exists
    echo 3. No conflicting packages
    echo.
    deactivate
    cd ..
    pause
    exit /b 1
)

deactivate
cd ..

echo.
echo ========================================
echo   Dependencies Fixed!
echo ========================================
echo.
echo All packages have been installed successfully.
echo You can now start the servers with:
echo   start-windows.bat
echo.
pause
