@echo off
chcp 65001 >nul
echo ========================================
echo Setting up PostgreSQL Database
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat

REM Set PYTHONPATH
cd ..
set PYTHONPATH=%CD%
cd backend

echo [1/3] Verifying database connection...
python -c "from backend.config import settings; print(f'DATABASE_URL: {settings.DATABASE_URL}')"
echo.

echo [2/3] Creating database tables...
python -c "from backend.db.database import Base, engine; Base.metadata.create_all(bind=engine); print('✓ All tables created successfully')"

if errorlevel 1 (
    echo [ERROR] Failed to create tables
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying tables...
python -c "from backend.db.database import engine; from sqlalchemy import inspect; inspector = inspect(engine); tables = inspector.get_table_names(); print(f'✓ Found {len(tables)} tables: {tables[:5]}...')"

echo.
echo ========================================
echo PostgreSQL Setup Complete!
echo ========================================
echo.
echo Now restart the backend server.
echo.
pause
