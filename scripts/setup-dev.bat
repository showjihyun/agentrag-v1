@echo off
REM Development Environment Setup Script for Windows

echo ========================================
echo Agentic RAG - Development Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/8] Python found
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

echo [2/8] Node.js found
echo.

REM Create backend virtual environment
echo [3/8] Creating Python virtual environment...
cd backend
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install backend dependencies
echo.
echo [4/8] Installing backend dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Setup environment file
echo.
echo [5/8] Setting up environment files...
if not exist .env (
    copy .env.example .env
    echo .env file created from .env.example
    echo Please edit .env and add your configuration!
) else (
    echo .env file already exists
)

REM Generate API key encryption key
echo.
echo [6/8] Generating API key encryption key...
python -c "from cryptography.fernet import Fernet; print('API_KEY_ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env.generated
echo API key encryption key generated in .env.generated
echo Please copy it to your .env file!

REM Run database migrations
echo.
echo [7/8] Running database migrations...
alembic upgrade head

REM Install frontend dependencies
echo.
echo [8/8] Installing frontend dependencies...
cd ..\frontend
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit backend/.env with your configuration
echo 2. Copy API_KEY_ENCRYPTION_KEY from backend/.env.generated to backend/.env
echo 3. Start Docker services: docker-compose up -d
echo 4. Start backend: cd backend ^&^& uvicorn main:app --reload
echo 5. Start frontend: cd frontend ^&^& npm run dev
echo.
echo Happy coding! 🚀
echo.

pause
