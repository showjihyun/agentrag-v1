@echo off
chcp 65001 >nul
echo ========================================
echo Merging Alembic Migrations
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat

echo Current heads:
alembic heads
echo.

echo Creating merge migration...
alembic merge -m "merge_multiple_heads" heads

if errorlevel 1 (
    echo [ERROR] Failed to create merge migration
    pause
    exit /b 1
)

echo.
echo Merge migration created successfully!
echo.
echo Now running: alembic upgrade head
alembic upgrade head

if errorlevel 1 (
    echo [ERROR] Failed to upgrade database
    pause
    exit /b 1
)

echo.
echo ========================================
echo Database Migration Complete!
echo ========================================
echo.
pause
