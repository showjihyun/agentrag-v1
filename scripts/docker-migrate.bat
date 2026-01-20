@echo off
REM Docker 컨테이너에서 Alembic 마이그레이션 실행
REM Usage: docker-migrate.bat [command]
REM Commands: upgrade, current, history, downgrade

echo ========================================
echo Docker 컨테이너 마이그레이션 실행
echo ========================================
echo.

REM 컨테이너 실행 확인
docker ps | findstr agenticrag-backend >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] agenticrag-backend 컨테이너가 실행 중이 아닙니다.
    echo.
    echo 컨테이너를 먼저 시작하세요:
    echo   docker-compose up -d
    echo.
    exit /b 1
)

REM 명령어 파라미터 (기본값: upgrade head)
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=upgrade

set TARGET=%2
if "%TARGET%"=="" (
    if "%COMMAND%"=="upgrade" set TARGET=head
    if "%COMMAND%"=="downgrade" set TARGET=-1
)

echo 실행 명령: alembic %COMMAND% %TARGET%
echo.

REM Docker 컨테이너에서 마이그레이션 실행
docker exec -it agenticrag-backend alembic %COMMAND% %TARGET%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 마이그레이션 성공!
    echo ========================================
    echo.
    
    REM 현재 마이그레이션 버전 확인
    echo 현재 마이그레이션 버전:
    docker exec -it agenticrag-backend alembic current
) else (
    echo.
    echo ========================================
    echo 마이그레이션 실패!
    echo ========================================
    echo.
    echo 로그를 확인하세요:
    echo   docker logs agenticrag-backend
    echo.
    exit /b 1
)

echo.
pause
