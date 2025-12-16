@echo off
setlocal

echo.
echo ================================================================================
echo  Starting Required Services (Docker Compose)
echo ================================================================================
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop and make sure it's running.
    pause
    exit /b 1
)

echo INFO: Docker is available
echo INFO: Starting required services...
echo.

REM Start the services
docker-compose up -d postgres redis milvus

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services
    echo Please check Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Services started successfully!
echo.
echo Service Information:
echo    PostgreSQL:     localhost:5433
echo    Redis:          localhost:6380  
echo    Milvus:         localhost:19530
echo.
echo INFO: You can now run start-backend.bat to start the backend server
echo.
pause