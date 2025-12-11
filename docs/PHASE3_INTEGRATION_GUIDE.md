# Phase 3 통합 가이드

## 개요
Phase 3 (보안 강화 및 캐싱 개선)의 통합 및 배포 가이드입니다.

## 배포 전 체크리스트

### 1. 환경 변수 설정

`.env` 파일에 다음 변수를 추가하세요:

```bash
# API Key Encryption (필수!)
API_KEY_ENCRYPTION_KEY=<32-byte-base64-encoded-key>

# Tracing (선택사항 - 프로덕션 권장)
JAEGER_HOST=localhost
JAEGER_PORT=6831

# Redis (기존 설정 확인)
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
REDIS_PASSWORD=
```

**API_KEY_ENCRYPTION_KEY 생성 방법**:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # 이 값을 .env에 저장
```

⚠️ **중요**: 이 키를 안전하게 보관하세요! 키를 잃어버리면 모든 API 키를 복구할 수 없습니다.

### 2. 데이터베이스 마이그레이션

```bash
cd backend

# 마이그레이션 실행
alembic upgrade head

# 또는 Windows에서
run_migrations.bat
```

마이그레이션이 성공하면 `api_keys` 테이블이 생성됩니다.

### 3. 의존성 설치

새로운 패키지가 필요합니다:

```bash
pip install cryptography apscheduler bleach
```

또는:

```bash
pip install -r requirements.txt
```

## 기능별 사용 가이드

### API 키 관리

#### 1. API 키 생성

**Frontend (사용자용)**:
```typescript
// API 키 생성 요청
const response = await fetch('/api/security/api-keys', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Production API Key',
    expires_in_days: 90,
    scopes: ['workflows:read', 'workflows:execute']
  })
});

const { key, id, prefix } = await response.json();

// ⚠️ 중요: key는 한 번만 표시됩니다!
alert(`Save this key: ${key}`);
```

**Backend (프로그래밍 방식)**:
```python
from backend.core.security.api_key_manager import get_api_key_manager
from backend.db.database import SessionLocal

manager = get_api_key_manager()
db = SessionLocal()

key_info = await manager.create_key(
    db=db,
    user_id=user.id,
    name="My API Key",
    expires_in_days=90,
    scopes=["workflows:read", "workflows:execute"]
)

print(f"API Key: {key_info['key']}")  # 한 번만 표시!
```

#### 2. API 키로 인증

**HTTP 요청**:
```bash
curl -H "Authorization: Bearer agr_abc123..." \
     https://api.example.com/api/workflows
```

**Python**:
```python
import httpx

headers = {"Authorization": "Bearer agr_abc123..."}
response = httpx.get("https://api.example.com/api/workflows", headers=headers)
```

**FastAPI 엔드포인트에서 사용**:
```python
from backend.middleware.api_key_auth import get_api_key_user, check_api_key_scope
from fastapi import Depends

@router.post("/workflows/execute")
async def execute_workflow(
    workflow_id: int,
    user_info: dict = Depends(get_api_key_user),
    _: None = Depends(check_api_key_scope("workflows:execute"))
):
    # user_info에 사용자 정보 포함
    user_id = user_info["user_id"]
    scopes = user_info["scopes"]
    ...
```

#### 3. API 키 관리

**키 목록 조회**:
```bash
GET /api/security/api-keys
Authorization: Bearer <user_token>
```

**키 로테이션**:
```bash
POST /api/security/api-keys/{key_id}/rotate
Authorization: Bearer <user_token>
```

**키 폐기**:
```bash
DELETE /api/security/api-keys/{key_id}
Authorization: Bearer <user_token>
```

**만료 예정 키 확인**:
```bash
GET /api/security/api-keys/expiring?days_threshold=7
Authorization: Bearer <user_token>
```

### 입력 검증

#### 1. 워크플로우 입력 검증

```python
from backend.core.security.input_validator import SecureWorkflowInput
from fastapi import HTTPException

@router.post("/workflows")
async def create_workflow(workflow: SecureWorkflowInput):
    # workflow는 자동으로 검증되고 정제됨
    # - SQL injection 체크
    # - XSS 체크
    # - 노드 타입 검증
    # - 코드 안전성 검증
    
    # 안전하게 사용 가능
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        nodes=workflow.nodes,
        edges=workflow.edges
    )
    ...
```

#### 2. 쿼리 입력 검증

```python
from backend.core.security.input_validator import SecureQueryInput

@router.post("/query")
async def query(query_input: SecureQueryInput):
    # query_input.query는 검증되고 정제됨
    # - SQL injection 방지
    # - 길이 제한
    # - HTML 태그 제거
    
    results = search_engine.search(query_input.query)
    ...
```

#### 3. 파일 업로드 검증

```python
from backend.core.security.input_validator import SecureFileUpload
from fastapi import UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile):
    # 파일 검증
    file_validation = SecureFileUpload(
        filename=file.filename,
        content_type=file.content_type,
        size=file.size
    )
    
    # 검증 통과 시 안전하게 처리
    content = await file.read()
    ...
```

### 캐시 의존성 관리

#### 1. 캐시 저장 with 의존성

```python
from backend.core.cache_invalidation import CacheDependencyGraph
from backend.core.dependencies import get_redis_client

async def cache_workflow(workflow_id: int, user_id: int, data: dict):
    redis = await get_redis_client()
    cache_deps = CacheDependencyGraph(redis)
    
    # 캐시 저장
    key = f"workflow:{workflow_id}"
    await redis.setex(key, 3600, json.dumps(data))
    
    # 의존성 추적
    await cache_deps.add_dependency(
        key=key,
        depends_on=[
            f"user:{user_id}",
            f"workflow_list:{user_id}"
        ]
    )
```

#### 2. 캐시 무효화

```python
async def update_user(user_id: int):
    redis = await get_redis_client()
    cache_deps = CacheDependencyGraph(redis)
    
    # 사용자 캐시 무효화 (cascade로 모든 의존 캐시도 무효화)
    await cache_deps.invalidate(
        key=f"user:{user_id}",
        cascade=True  # workflow:*, workflow_list:* 등 자동 무효화
    )
```

#### 3. 패턴 무효화

```python
async def clear_all_workflows():
    redis = await get_redis_client()
    cache_deps = CacheDependencyGraph(redis)
    
    # 모든 워크플로우 캐시 무효화
    await cache_deps.invalidate_pattern("workflow:*")
```

### 캐시 워밍

캐시 워밍은 자동으로 실행됩니다:

- **인기 워크플로우**: 5분마다
- **활성 사용자**: 10분마다
- **분석 데이터**: 매일 자정

수동으로 워밍하려면:

```python
from backend.core.cache_warming import get_cache_warmer

warmer = get_cache_warmer()

# 인기 워크플로우 워밍
await warmer.warm_popular_workflows()

# 특정 사용자 예측 워밍
await warmer.predictive_warming(user_id=123)

# 온디맨드 워밍
await warmer.warm_on_demand(
    keys=["workflow:123", "workflow:456"],
    fetch_func=fetch_workflow_data,
    ttl=3600
)
```

## 모니터링

### 1. API 키 사용 모니터링

로그에서 API 키 사용 추적:

```bash
# 성공적인 인증
grep "api_key_authenticated" logs/app.log

# 실패한 인증
grep "api_key_authentication_failed" logs/app.log

# 키 생성
grep "api_key_created" logs/app.log

# 키 로테이션
grep "api_key_rotated" logs/app.log
```

### 2. 보안 이벤트 모니터링

```bash
# SQL injection 시도
grep "sql_injection_attempt_detected" logs/app.log

# XSS 시도
grep "xss_attempt_detected" logs/app.log

# Command injection 시도
grep "command_injection_attempt_detected" logs/app.log
```

### 3. 캐시 성능 모니터링

```bash
# 캐시 무효화
grep "cache_invalidated" logs/app.log

# 캐시 워밍
grep "cache_warmer" logs/app.log

# 캐시 히트율 (Redis)
redis-cli INFO stats | grep keyspace_hits
```

## 트러블슈팅

### 문제: API 키 생성 실패

**증상**: `Failed to create API key: encryption key not found`

**해결**:
1. `.env` 파일에 `API_KEY_ENCRYPTION_KEY` 설정
2. 서버 재시작

### 문제: 마이그레이션 실패

**증상**: `Table 'api_keys' already exists`

**해결**:
```bash
# 마이그레이션 상태 확인
alembic current

# 특정 버전으로 다운그레이드
alembic downgrade -1

# 다시 업그레이드
alembic upgrade head
```

### 문제: 캐시 워밍 실패

**증상**: `Failed to initialize cache warmer`

**해결**:
1. Redis 연결 확인
2. 데이터베이스 연결 확인
3. 로그에서 상세 에러 확인

### 문제: 입력 검증 너무 엄격

**증상**: 정상적인 입력이 거부됨

**해결**:
```python
# 검증 규칙 조정
from backend.core.security.input_validator import InputValidator

# 특정 패턴 허용
validator = InputValidator()
# 커스텀 검증 로직 구현
```

## 성능 최적화

### 1. 캐시 워밍 스케줄 조정

```python
# backend/core/cache_warming.py 수정
def _schedule_popular_workflows(self):
    job = self.scheduler.add_job(
        self.warm_popular_workflows,
        trigger=IntervalTrigger(minutes=10),  # 5분 -> 10분
        ...
    )
```

### 2. API 키 검증 캐싱

```python
# API 키 검증 결과를 짧은 시간 캐싱
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_key_hash(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()
```

### 3. 의존성 그래프 최적화

```python
# 의존성 깊이 제한
MAX_DEPENDENCY_DEPTH = 5

# 순환 의존성 방지
visited = set()
```

## 보안 권장사항

### 1. API 키 관리

- ✅ 키는 HTTPS로만 전송
- ✅ 키를 로그에 기록하지 않음
- ✅ 정기적인 키 로테이션 (90일)
- ✅ 최소 권한 원칙 (필요한 scope만)
- ✅ 사용하지 않는 키는 즉시 폐기

### 2. 입력 검증

- ✅ 모든 사용자 입력 검증
- ✅ 화이트리스트 방식 사용
- ✅ 길이 제한 적용
- ✅ 타입 검증
- ✅ 정제 후 사용

### 3. 캐시 보안

- ✅ 민감한 데이터는 암호화하여 캐싱
- ✅ 적절한 TTL 설정
- ✅ 사용자별 캐시 격리
- ✅ 권한 확인 후 캐시 접근

## 다음 단계

Phase 3 통합 완료 후:

1. ✅ 통합 테스트 실행
2. ✅ 성능 테스트
3. ✅ 보안 감사
4. 📅 Phase 4: 이벤트 소싱 및 성능 최적화

## 참고 자료

- [SECURITY_CACHING_COMPLETE.md](./SECURITY_CACHING_COMPLETE.md) - 상세 구현 문서
- [ARCHITECTURE_IMPROVEMENTS_PROGRESS.md](./ARCHITECTURE_IMPROVEMENTS_PROGRESS.md) - 전체 진행 상황
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - 보안 베스트 프랙티스

---

**작성일**: 2024년 12월 6일
**버전**: 1.0.0
