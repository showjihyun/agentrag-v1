@echo off
REM Agentic RAG System Setup Script for Windows

echo ===================================
echo Agentic RAG System Setup
echo ===================================

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created. Please edit it with your configuration.
) else (
    echo [OK] .env file already exists
)

REM Setup backend
echo.
echo Setting up backend...
cd backend

if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo [OK] Backend dependencies installed

cd ..

REM Setup frontend
echo.
echo Setting up frontend...
cd frontend

if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already installed
)

cd ..

REM Start infrastructure
echo.
echo Starting infrastructure services (Milvus, Redis, etc.)...
docker-compose up -d milvus redis etcd minio

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. (Optional) Install and start Ollama: https://ollama.ai
echo 3. Start backend: .\start-backend.bat
echo 4. Start frontend: cd frontend ^&^& npm run dev
echo.
echo Or use Docker Compose for all services:
echo   docker-compose up -d
echo.
pause
