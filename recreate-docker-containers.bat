@echo off
REM Docker 컨테이너 재생성 스크립트

echo ========================================
echo Docker 컨테이너 재생성
echo ========================================
echo.

REM Step 1: 기존 컨테이너 중지 및 제거
echo [1/5] 기존 컨테이너 중지 및 제거...
docker-compose down
echo.

REM Step 2: 사용하지 않는 리소스 정리
echo [2/5] 사용하지 않는 Docker 리소스 정리...
docker system prune -f
echo.

REM Step 3: 네트워크 확인 및 재생성
echo [3/5] Docker 네트워크 확인...
docker network ls | findstr agenticrag-network
if errorlevel 1 (
    echo 네트워크 생성...
    docker network create agenticrag-network
) else (
    echo 네트워크 이미 존재함
)
echo.

REM Step 4: 볼륨 확인
echo [4/5] Docker 볼륨 확인...
docker volume ls | findstr agenticrag
echo.

REM Step 5: 컨테이너 재생성
echo [5/5] 컨테이너 재생성 중...
echo.
echo 시작하는 서비스:
echo - PostgreSQL (포트 5433)
echo - Redis (포트 6380)
echo - Etcd (Milvus 의존성)
echo - MinIO (Milvus 스토리지)
echo - Milvus (포트 19531)
echo.

docker-compose up -d postgres redis etcd minio milvus

echo.
echo 컨테이너 초기화 대기 중 (20초)...
timeout /t 20 /nobreak >nul

echo.
echo ========================================
echo 컨테이너 상태 확인
echo ========================================
docker-compose ps

echo.
echo ========================================
echo 서비스 헬스 체크
echo ========================================

REM PostgreSQL 체크
echo.
echo [PostgreSQL] 연결 테스트...
docker-compose exec -T postgres pg_isready -U postgres -d agenticrag
if errorlevel 1 (
    echo [FAIL] PostgreSQL이 준비되지 않았습니다
    echo 로그 확인: docker-compose logs postgres
) else (
    echo [OK] PostgreSQL 준비 완료
)

REM Redis 체크
echo.
echo [Redis] 연결 테스트...
docker-compose exec -T redis redis-cli ping
if errorlevel 1 (
    echo [FAIL] Redis가 준비되지 않았습니다
    echo 로그 확인: docker-compose logs redis
) else (
    echo [OK] Redis 준비 완료
)

REM Milvus 체크
echo.
echo [Milvus] 연결 테스트...
curl -s http://localhost:9092/healthz
if errorlevel 1 (
    echo [FAIL] Milvus가 준비되지 않았습니다
    echo 로그 확인: docker-compose logs milvus
    echo 참고: Milvus는 시작하는데 1-2분 소요될 수 있습니다
) else (
    echo [OK] Milvus 준비 완료
)

echo.
echo ========================================
echo 재생성 완료!
echo ========================================
echo.
echo 접속 정보:
echo PostgreSQL: localhost:5433 (agenticrag/postgres/postgres)
echo Redis: localhost:6380
echo Milvus: localhost:19531
echo MinIO Console: http://localhost:9002
echo.
echo 문제가 있다면:
echo 1. docker-compose logs [service-name] 으로 로그 확인
echo 2. docker-compose restart [service-name] 으로 재시작
echo 3. check-docker-services.bat 으로 상태 확인
echo.
pause
