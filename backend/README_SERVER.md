# Backend Server 시작 가이드

## 🚀 빠른 시작

### Windows (PowerShell 권장)

```powershell
# PowerShell에서 실행
.\start_server.ps1
```

또는

```cmd
# CMD에서 실행
start_server.bat
```

### Linux / Mac

```bash
# 실행 권한 부여 (최초 1회만)
chmod +x start_server.sh

# 서버 시작
./start_server.sh
```

---

## 📋 사전 요구사항

### 1. Python 가상환경 생성 (최초 1회만)

```bash
# Python 3.10+ 필요
python -m venv venv
```

### 2. 의존성 설치 (최초 1회만)

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux / Mac
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 필요한 설정 입력
```

### 4. Database Migration 실행 (최초 1회만)

```bash
# venv 활성화 후
alembic upgrade head
```

---

## 🔧 스크립트 기능

### start_server.ps1 / start_server.bat / start_server.sh

**자동으로 수행하는 작업**:

1. ✅ 가상환경 존재 여부 확인
2. ✅ 가상환경 자동 활성화
3. ✅ 의존성 설치 여부 확인
4. ✅ FastAPI 서버 시작 (Hot Reload 활성화)
5. ✅ 서버 종료 시 가상환경 자동 비활성화

**서버 설정**:
- Host: `0.0.0.0` (모든 네트워크 인터페이스)
- Port: `8000`
- Reload: `활성화` (코드 변경 시 자동 재시작)

---

## 🌐 접속 URL

서버 시작 후 다음 URL로 접속할 수 있습니다:

| 서비스 | URL | 설명 |
|--------|-----|------|
| **API Server** | http://localhost:8000 | 메인 API 서버 |
| **Swagger UI** | http://localhost:8000/docs | 대화형 API 문서 |
| **ReDoc** | http://localhost:8000/redoc | API 문서 (읽기 전용) |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | OpenAPI 스펙 |
| **Health Check** | http://localhost:8000/api/health | 서버 상태 확인 |

---

## 🛠️ 수동 실행 (고급)

스크립트를 사용하지 않고 수동으로 실행하려면:

### Windows (PowerShell)

```powershell
# 1. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 2. 서버 시작
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 서버 종료 후 가상환경 비활성화
deactivate
```

### Linux / Mac

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 서버 시작
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 서버 종료 후 가상환경 비활성화
deactivate
```

---

## 🔍 문제 해결

### 1. "가상환경을 찾을 수 없습니다" 오류

**원인**: venv 폴더가 없음

**해결**:
```bash
python -m venv venv
pip install -r requirements.txt
```

### 2. "uvicorn을 찾을 수 없습니다" 오류

**원인**: 의존성이 설치되지 않음

**해결**:
```bash
# venv 활성화 후
pip install -r requirements.txt
```

### 3. "포트 8000이 이미 사용 중입니다" 오류

**원인**: 다른 프로세스가 8000 포트 사용 중

**해결**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux / Mac
lsof -ti:8000 | xargs kill -9
```

또는 다른 포트 사용:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 4. "Database 연결 오류"

**원인**: PostgreSQL, Redis, Milvus가 실행되지 않음

**해결**:
```bash
# Docker Compose로 서비스 시작
docker-compose up -d postgres redis milvus

# 서비스 상태 확인
docker-compose ps
```

### 5. PowerShell 실행 정책 오류

**원인**: PowerShell 스크립트 실행이 차단됨

**해결**:
```powershell
# 관리자 권한으로 PowerShell 실행 후
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일회성 실행
PowerShell -ExecutionPolicy Bypass -File start_server.ps1
```

---

## 📊 서버 모니터링

### 로그 확인

서버 실행 중 콘솔에서 실시간 로그를 확인할 수 있습니다:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Health Check

```bash
# curl 사용
curl http://localhost:8000/api/health

# PowerShell 사용
Invoke-WebRequest http://localhost:8000/api/health
```

**정상 응답**:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-06T12:00:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "milvus": "healthy"
  }
}
```

---

## 🎯 개발 팁

### Hot Reload

코드를 수정하면 서버가 자동으로 재시작됩니다:

```
INFO:     Detected file change in 'main.py'. Reloading...
INFO:     Application startup complete.
```

### Debug 모드

더 자세한 로그를 보려면 `.env` 파일에서:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### API 테스트

Swagger UI에서 직접 API를 테스트할 수 있습니다:

1. http://localhost:8000/docs 접속
2. 원하는 엔드포인트 선택
3. "Try it out" 클릭
4. 파라미터 입력 후 "Execute" 클릭

---

## 🚦 서버 종료

### 정상 종료

```
Ctrl + C
```

서버가 정상적으로 종료되고 가상환경이 자동으로 비활성화됩니다.

### 강제 종료 (비상시)

```bash
# Windows
taskkill /F /IM python.exe

# Linux / Mac
pkill -9 python
```

---

## 📝 추가 명령어

### Database Migration

```bash
# venv 활성화 후

# 현재 migration 상태 확인
alembic current

# 최신 migration 적용
alembic upgrade head

# migration 되돌리기
alembic downgrade -1

# 새 migration 생성
alembic revision --autogenerate -m "description"
```

### 테스트 실행

```bash
# venv 활성화 후

# 전체 테스트
pytest

# 특정 테스트
pytest tests/integration/test_flows_api.py -v

# 커버리지 포함
pytest --cov=backend --cov-report=html
```

---

## 🔗 관련 문서

- [API 문서](http://localhost:8000/docs) - Swagger UI
- [시스템 준비 상태](../SYSTEM_READY.md) - 전체 시스템 개요
- [통합 테스트 가이드](../docs/INTEGRATION_TESTING_COMPLETE.md) - 테스트 방법
- [최종 통합 상태](../docs/FINAL_INTEGRATION_STATUS.md) - 통합 현황

---

**작성일**: 2024년 12월 6일  
**버전**: 1.0.0  
**상태**: ✅ 프로덕션 준비 완료
