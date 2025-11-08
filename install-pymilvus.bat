@echo off
chcp 65001 >nul
echo ========================================
echo   Installing pymilvus with grpcio
echo ========================================
echo.

REM Activate virtual environment
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found at backend\venv
    echo Please create it first: python -m venv backend\venv
    pause
    exit /b 1
)

echo Step 1: Checking Docker and Milvus...
docker ps --filter "name=agenticrag-milvus" --format "{{.Names}}: {{.Status}}" | findstr agenticrag-milvus >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Milvus container found!
) else (
    echo [WARNING] Milvus container not running
    echo Please start it with: docker-compose up -d milvus
)

echo.
echo Step 2: Uninstalling existing grpcio and pymilvus...
pip uninstall -y grpcio pymilvus 2>nul

echo.
echo Step 3: Installing grpcio binary (no compilation)...
pip install --only-binary :all: "grpcio>=1.60.0,<2.0.0"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Binary installation failed, trying --prefer-binary...
    pip install "grpcio>=1.60.0,<2.0.0" --prefer-binary
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Failed to install grpcio
        echo Please check your internet connection
        pause
        exit /b 1
    )
)

echo.
echo Step 4: Verifying grpcio installation...
python -c "import grpcio; print(f'grpcio {grpcio.__version__} installed successfully')"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] grpcio verification failed
    pause
    exit /b 1
)

echo.
echo Step 5: Installing pymilvus...
pip install pymilvus==2.3.5

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install pymilvus
    pause
    exit /b 1
)

echo.
echo Step 6: Verifying pymilvus installation...
python -c "from pymilvus import connections; print('pymilvus installed successfully')"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pymilvus verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo pymilvus client is now installed.
echo.
echo Milvus connection info:
echo   Host: localhost
echo   Port: 19530
echo.
echo To start Milvus: docker-compose up -d milvus
echo To check status: docker-compose ps milvus
echo.
pause
