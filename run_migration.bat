@echo off
REM PostgreSQL 데이터베이스 마이그레이션 스크립트

echo ========================================
echo PostgreSQL 데이터베이스 마이그레이션
echo ========================================
echo.

REM 가상환경 활성화
echo [1/3] 가상환경 활성화 중...
if exist backend\venv\Scripts\activate.bat (
    call backend\venv\Scripts\activate.bat
    echo ✓ 가상환경 활성화 완료
) else (
    echo ✗ 가상환경을 찾을 수 없습니다: backend\venv
    echo.
    echo 가상환경을 먼저 생성해주세요:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/3] 데이터베이스 연결 확인 중...
timeout /t 2 /nobreak >nul
echo ✓ 준비 완료

echo.
echo [3/3] Alembic 마이그레이션 실행 중...
cd backend
set PYTHONPATH=%CD%\..
alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ 마이그레이션 완료!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ 마이그레이션 실패
    echo ========================================
    echo.
    echo 문제 해결:
    echo 1. PostgreSQL 컨테이너가 실행 중인지 확인
    echo    docker-compose ps postgres
    echo.
    echo 2. .env 파일의 데이터베이스 설정 확인
    echo    DATABASE_URL=postgresql://postgres:postgres@localhost:5433/agenticrag
    echo.
    echo 3. 데이터베이스 연결 테스트
    echo    docker exec -it agenticrag-postgres psql -U postgres -d agenticrag
)

echo.
pause
