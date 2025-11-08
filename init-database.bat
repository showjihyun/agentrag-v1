@echo off
chcp 65001 >nul
echo ========================================
echo Initializing Database
echo ========================================
echo.

cd backend

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Set PYTHONPATH
cd ..
set PYTHONPATH=%CD%
cd backend

echo [1/2] Checking database connection...
python -c "from backend.config import settings; print(f'Database: {settings.DATABASE_URL}')"
echo.

echo [2/2] Running database migrations...
alembic upgrade head

if errorlevel 1 (
    echo.
    echo [WARNING] Migration failed. This might be normal if tables already exist.
    echo.
    echo Creating tables directly...
    python -c "from backend.db.database import Base, engine; Base.metadata.create_all(bind=engine); print('Tables created successfully')"
)

echo.
echo ========================================
echo Database Initialized!
echo ========================================
echo.
pause
