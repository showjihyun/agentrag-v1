@echo off
REM ============================================
REM Docker Clean Script (Windows)
REM Updated: 2026-01-16
REM WARNING: This will delete all data!
REM ============================================

echo ========================================
echo Docker Clean - WARNING!
echo ========================================
echo.
echo This will:
echo - Stop all containers
echo - Remove all containers
echo - Remove all volumes (DATA WILL BE LOST!)
echo - Remove all networks
echo.
set /p confirm="Are you sure? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo.
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Stopping and removing everything...
docker-compose down -v

echo.
echo Removing unused images...
docker image prune -f

echo.
echo ========================================
echo Cleanup completed!
echo ========================================
echo.
pause
