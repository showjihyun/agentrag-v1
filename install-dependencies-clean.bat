@echo off
chcp 65001 >nul
echo ========================================
echo   Clean Dependencies Installation
echo ========================================
echo.

REM Check virtual environment
if not exist "backend\venv" (
    echo [ERROR] Virtual environment not found!
    echo Please create it first: python -m venv backend\venv
    pause
    exit /b 1
)

echo Activating virtual environment...
cd backend
call venv\Scripts\activate.bat

echo.
echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing grpcio binary (no compilation)...
pip install --only-binary=:all: grpcio

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install grpcio
    deactivate
    cd ..
    pause
    exit /b 1
)

echo.
echo Step 3: Installing pymilvus without dependencies...
pip install --no-deps pymilvus

echo.
echo Step 4: Installing pymilvus dependencies...
pip install environs minio pyarrow ujson pandas protobuf

echo.
echo Step 5: Installing all other requirements...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Some packages may have failed
    echo But core packages (grpcio, pymilvus) are installed
)

deactivate
cd ..

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Key packages installed:
python backend\venv\Scripts\python.exe -c "import grpcio; print(f'  - grpcio {grpcio.__version__}')"
python backend\venv\Scripts\python.exe -c "import pymilvus; print(f'  - pymilvus {pymilvus.__version__}')"
echo.
echo To start Milvus: docker-compose up -d milvus
echo To start servers: start-windows.bat
echo.
pause
