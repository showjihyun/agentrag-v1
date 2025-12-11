# Phase 3: 보안 강화 및 캐싱 개선 - 설치 가이드

## 🎯 개요

Phase 3에서는 다음 기능들이 추가되었습니다:
- ✅ API 키 관리 시스템
- ✅ 입력 검증 강화 (SQL Injection, XSS 방지)
- ✅ 스마트 캐시 무효화
- ✅ 캐시 워밍 전략
- ✅ 분산 추적 (OpenTelemetry)
- ✅ 구조화된 로깅 (Structlog)

## 📦 설치

### 1. 의존성 설치

**Windows**:
```bash
install_phase3_deps.bat
```

**Linux/Mac**:
```bash
pip install cryptography>=41.0.0 \
            bleach>=6.0.0 \
            structlog>=24.1.0 \
            apscheduler>=3.10.4 \
            opentelemetry-api>=1.20.0 \
            opentelemetry-sdk>=1.20.0 \
            opentelemetry-instrumentation-fastapi>=0.41b0 \
            opentelemetry-instrumentation-sqlalchemy>=0.41b0 \
            opentelemetry-instrumentation-redis>=0.41b0 \
            opentelemetry-instrumentation-httpx>=0.41b0 \
            opentelemetry-exporter-jaeger>=1.20.0
```

또는 전체 requirements 재설치:
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 추가:

```bash
# API Key Encryption (필수!)
API_KEY_ENCRYPTION_KEY=<generate-this-key>

# Tracing (선택사항)
JAEGER_HOST=localhost
JAEGER_PORT=6831
```

**API_KEY_ENCRYPTION_KEY 생성**:
```python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head

# 또는 Windows
run_migrations.bat
```

### 4. 테스트 실행

```bash
# API Key Manager 테스트
pytest tests/unit/test_api_key_manager.py -v

# Input Validator 테스트
pytest tests/unit/test_input_validator.py -v

# Cache Invalidation 테스트
pytest tests/unit/test_cache_invalidation.py -v

# 전체 테스트
pytest tests/unit/ -v
```

## 🚀 사용법

### API 키 생성

```python
from backend.core.security.api_key_manager import get_api_key_manager
from backend.db.database import SessionLocal

manager = get_api_key_manager()
db = SessionLocal()

# 키 생성
key_info = await manager.create_key(
    db=db,
    user_id=user.id,
    name="Production Key",
    expires_in_days=90,
    scopes=["workflows:read", "workflows:execute"]
)

print(f"API Key: {key_info['key']}")  # ⚠️ 한 번만 표시!
```

### API 키로 인증

```bash
curl -H "Authorization: Bearer agr_abc123..." \
     http://localhost:8000/api/workflows
```

### 입력 검증

```python
from backend.core.security.input_validator import SecureWorkflowInput

# 자동 검증
workflow = SecureWorkflowInput(
    name="My Workflow",
    description="Process data",
    nodes=[...],
    edges=[...]
)
# SQL injection, XSS 자동 체크!
```

### 캐시 의존성

```python
from backend.core.cache_invalidation import CacheDependencyGraph

cache_deps = CacheDependencyGraph(redis)

# 의존성 추가
await cache_deps.add_dependency(
    key="workflow:123",
    depends_on=["user:456"]
)

# Cascade 무효화
await cache_deps.invalidate("user:456", cascade=True)
```

## 📊 모니터링

### 로그 확인

```bash
# API 키 이벤트
tail -f logs/app.log | grep api_key

# 보안 이벤트
tail -f logs/app.log | grep -E "sql_injection|xss|command_injection"

# 캐시 이벤트
tail -f logs/app.log | grep cache
```

### Jaeger 추적 (선택사항)

```bash
# Jaeger 시작 (Docker)
docker run -d --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# UI 접속
open http://localhost:16686
```

## 🔧 트러블슈팅

### 문제: ModuleNotFoundError: No module named 'structlog'

**해결**:
```bash
pip install structlog>=24.1.0
```

### 문제: API key encryption key not found

**해결**:
1. `.env` 파일에 `API_KEY_ENCRYPTION_KEY` 추가
2. 키 생성: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. 서버 재시작

### 문제: Migration failed

**해결**:
```bash
# 현재 버전 확인
alembic current

# 특정 버전으로 이동
alembic downgrade -1
alembic upgrade head
```

## 📚 문서

- [SECURITY_CACHING_COMPLETE.md](../docs/SECURITY_CACHING_COMPLETE.md) - 상세 구현
- [PHASE3_INTEGRATION_GUIDE.md](../docs/PHASE3_INTEGRATION_GUIDE.md) - 통합 가이드
- [PHASE3_COMPLETION_SUMMARY.md](../docs/PHASE3_COMPLETION_SUMMARY.md) - 완료 요약

## ✅ 체크리스트

설치 완료 확인:

- [ ] 의존성 설치 완료
- [ ] 환경 변수 설정 (`API_KEY_ENCRYPTION_KEY`)
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 테스트 통과 (66/66)
- [ ] 서버 정상 시작
- [ ] API 키 생성 테스트
- [ ] 로그 확인

## 🎉 완료!

Phase 3 설치가 완료되었습니다!

시스템은 이제:
- 🔒 엔터프라이즈급 보안
- ⚡ 최적화된 성능
- 📊 완전한 관찰성

을 갖추었습니다!

---

**문의**: 문제가 발생하면 로그를 확인하거나 문서를 참조하세요.
