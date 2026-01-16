@echo off
REM ============================================
REM Docker Start Script (Windows)
REM Updated: 2026-01-16
REM ============================================

echo Starting Agentic RAG System...
echo.

REM Check if .env exists
if not exist backend\.env (
    echo Warning: .env file not found. Copying from .env.example...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env with your configuration
    echo.
)

REM Start services
echo Starting Docker Compose services...
docker-compose up -d

REM Wait for services
echo Waiting for services to start...
timeout /t 10 /nobreak > nul

REM Check service health
echo Checking service health...
docker-compose ps

REM Run migrations
echo Running database migrations...
docker-compose exec backend alembic upgrade head

echo.
echo ========================================
echo Agentic RAG System started successfully!
echo ========================================
echo.
echo Services:
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - PostgreSQL: localhost:5433
echo   - Redis: localhost:6380
echo   - Milvus: localhost:19530
echo   - MinIO Console: http://localhost:9002
echo.
echo To view logs:
echo   docker-compose logs -f backend
echo.
echo To stop:
echo   docker-compose down
echo.
pause
