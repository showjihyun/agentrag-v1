# 백엔드 개선 사항 (Backend Improvements)

## 🎯 우선순위 1: 즉시 개선 필요 (Critical)

### 1.1 API 구현 완료
**위치**: `backend/api/dashboard.py`, `backend/api/notifications.py`, `backend/api/export.py`

**문제점**:
```python
# TODO: Implement actual database operations
# For now, return mock data
```

**개선 방안**:
- Dashboard API: 실제 DB 연동 구현
- Notifications API: 실시간 알림 시스템 구현
- Export API: PDF 생성 기능 구현

**예상 작업 시간**: 2-3일

---

### 1.2 Rate Limiting 미들웨어 통합
**위치**: `backend/main.py:366`

**문제점**:
```python
# Note: Rate limiting is currently handled per-endpoint using SecurityManager
# TODO: Implement global rate_limit_middleware for centralized rate limiting
```

**개선 방안**:
```python
# main.py에 추가
from backend.core.rate_limiter import RateLimiter

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware."""
    redis_client = await get_redis_client()
    rate_limiter = RateLimiter(redis_client)
    
    identifier = request.client.host if request.client else "unknown"
    is_allowed, error_msg, remaining = await rate_limiter.check_rate_limit(
        identifier=identifier,
        endpoint=request.url.path
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={"error": error_msg, "remaining": remaining}
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining.get("minute", 0))
    return response
```

**예상 작업 시간**: 2-3시간

---

## 🔧 우선순위 2: 성능 및 안정성 개선 (High)

### 2.1 로깅 최적화
**위치**: 전체 코드베이스

**문제점**:
- 과도한 `logger.debug()` 사용 (프로덕션 성능 저하)
- 일부 민감한 정보가 로그에 노출될 가능성

**개선 방안**:
```python
# 조건부 디버그 로깅
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Expensive operation: {expensive_computation()}")

# 민감한 정보 마스킹
logger.info(f"User login: {mask_email(user.email)}")
```

**예상 작업 시간**: 1일

---

### 2.2 Connection Pool 모니터링 강화
**위치**: `backend/core/connection_pool.py`, `backend/core/milvus_pool.py`

**개선 방안**:
```python
# Pool 상태 메트릭 추가
class ConnectionPoolMetrics:
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.wait_time_ms = []
        
    async def record_checkout(self, wait_time: float):
        self.active_connections += 1
        self.wait_time_ms.append(wait_time * 1000)
        
    async def get_metrics(self) -> dict:
        return {
            "total": self.total_connections,
            "active": self.active_connections,
            "idle": self.idle_connections,
            "avg_wait_ms": sum(self.wait_time_ms) / len(self.wait_time_ms) if self.wait_time_ms else 0
        }
```

**예상 작업 시간**: 4-6시간

---

### 2.3 에러 처리 개선
**위치**: `backend/services/answer_quality_service.py`, `backend/agents/vector_search.py`

**문제점**:
```python
except Exception as e:
    logger.debug(f"Operation failed: {e}")
    return default_value  # 에러를 숨김
```

**개선 방안**:
```python
except SpecificException as e:
    logger.warning(f"Expected error: {e}", exc_info=True)
    # 적절한 fallback 처리
    return fallback_value
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # 에러를 상위로 전파하거나 명시적 처리
    raise ServiceException("Operation failed", details={"cause": str(e)})
```

**예상 작업 시간**: 1-2일

---

## 🚀 우선순위 3: 기능 확장 (Medium)

### 3.1 캐시 전략 개선
**현재 상태**:
- L1/L2 캐시 구현됨
- TTL 기반 만료

**개선 방안**:
```python
# 1. LRU 캐시 추가
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding_cached(text: str) -> np.ndarray:
    return embedding_service.embed(text)

# 2. Cache Warming 개선
class SmartCacheWarmer:
    async def warm_popular_queries(self):
        # 인기 쿼리 분석 및 사전 캐싱
        popular_queries = await self.get_popular_queries(limit=100)
        for query in popular_queries:
            await self.precompute_and_cache(query)
```

**예상 작업 시간**: 2-3일

---

### 3.2 배치 처리 최적화
**위치**: `backend/services/document_processor.py`

**개선 방안**:
```python
# 1. 청크 단위 배치 처리
async def process_documents_batch(documents: List[Document], batch_size: int = 10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await asyncio.gather(*[process_document(doc) for doc in batch])

# 2. 우선순위 큐 도입
import heapq

class PriorityQueue:
    def __init__(self):
        self.queue = []
        
    def add_task(self, priority: int, task: Callable):
        heapq.heappush(self.queue, (priority, task))
```

**예상 작업 시간**: 2-3일

---

## 📊 우선순위 4: 모니터링 및 관찰성 (Low)

### 4.1 OpenTelemetry 통합
**위치**: `backend/config.py:ENABLE_OPENTELEMETRY`

**개선 방안**:
```python
# 1. Tracer 설정
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

def setup_tracing():
    trace.set_tracer_provider(TracerProvider())
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

# 2. 주요 함수에 트레이싱 추가
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_query")
async def process_query(query: str):
    with tracer.start_as_current_span("embed_query"):
        embedding = await embed(query)
    with tracer.start_as_current_span("search_vectors"):
        results = await search(embedding)
    return results
```

**예상 작업 시간**: 3-4일

---

### 4.2 헬스 체크 개선
**위치**: `backend/api/health.py`

**개선 방안**:
```python
# 1. 상세한 컴포넌트 체크
@router.get("/health/detailed")
async def detailed_health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "milvus": await check_milvus(),
        "llm": await check_llm_availability(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage(),
    }
    
    overall_status = "healthy" if all(c["status"] == "ok" for c in checks.values()) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

# 2. Readiness vs Liveness 분리
@router.get("/health/live")  # 프로세스 살아있는지
async def liveness():
    return {"status": "ok"}

@router.get("/health/ready")  # 트래픽 받을 준비됐는지
async def readiness():
    # DB, Redis, Milvus 연결 확인
    return {"status": "ready" if all_services_ready() else "not_ready"}
```

**예상 작업 시간**: 1-2일

---

## 🔒 우선순위 5: 보안 강화 (Medium)

### 5.1 입력 검증 강화
**개선 방안**:
```python
# 1. Pydantic 모델에 커스텀 validator 추가
from pydantic import validator, Field

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    
    @validator('query')
    def validate_query(cls, v):
        # SQL Injection 방지
        dangerous_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT']
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError("Query contains dangerous patterns")
        return v

# 2. 파일 업로드 검증 강화
async def validate_file_upload(file: UploadFile):
    # Magic number 체크 (실제 파일 타입 확인)
    content = await file.read(8)
    await file.seek(0)
    
    if content[:4] == b'%PDF':
        return 'pdf'
    elif content[:2] == b'PK':  # ZIP-based (DOCX, PPTX)
        return 'office'
    else:
        raise ValueError("Invalid file type")
```

**예상 작업 시간**: 2-3일

---

### 5.2 API Key 관리 개선
**개선 방안**:
```python
# 1. API Key 암호화 저장
from cryptography.fernet import Fernet

class APIKeyManager:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_key(self, api_key: str) -> str:
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_key(self, encrypted_key: str) -> str:
        return self.cipher.decrypt(encrypted_key.encode()).decode()

# 2. API Key 로테이션
async def rotate_api_key(user_id: str):
    new_key = secrets.token_urlsafe(32)
    await db.update_api_key(user_id, new_key)
    await notify_user_key_rotated(user_id)
    return new_key
```

**예상 작업 시간**: 2-3일

---

## 📈 성능 벤치마크 목표

### 현재 성능
- FAST 모드: ~2초
- BALANCED 모드: ~5초
- DEEP 모드: ~15초

### 개선 목표
- FAST 모드: <1초 (50% 개선)
- BALANCED 모드: <3초 (40% 개선)
- DEEP 모드: <10초 (33% 개선)

### 개선 방법
1. **쿼리 최적화**: N+1 쿼리 제거
2. **캐싱 강화**: 임베딩 캐시, LLM 응답 캐시
3. **병렬 처리**: 더 많은 작업을 병렬화
4. **인덱스 최적화**: PostgreSQL 인덱스 추가

---

## 🧪 테스트 커버리지 개선

### 현재 상태
- Unit Tests: 일부 구현됨
- Integration Tests: 일부 구현됨
- E2E Tests: 일부 구현됨

### 개선 목표
- Unit Tests: 80% 커버리지
- Integration Tests: 주요 플로우 100% 커버
- E2E Tests: 핵심 시나리오 100% 커버

### 추가 필요 테스트
```python
# 1. 에러 시나리오 테스트
async def test_llm_timeout():
    with pytest.raises(LLMException):
        await query_with_timeout(timeout=0.001)

# 2. 동시성 테스트
async def test_concurrent_queries():
    queries = [f"Query {i}" for i in range(100)]
    results = await asyncio.gather(*[process_query(q) for q in queries])
    assert len(results) == 100

# 3. 부하 테스트
async def test_load_handling():
    # 1000 RPS로 1분간 테스트
    await load_test(rps=1000, duration=60)
```

---

## 📝 문서화 개선

### 필요한 문서
1. **API 문서**: OpenAPI/Swagger 자동 생성 ✅
2. **아키텍처 문서**: 시스템 구조 다이어그램
3. **배포 가이드**: Docker, Kubernetes 배포 방법
4. **운영 가이드**: 모니터링, 트러블슈팅
5. **개발 가이드**: 로컬 개발 환경 설정

---

## 🎯 다음 스프린트 추천 작업

### Week 1-2: Critical Issues
1. Dashboard/Notifications API 구현
2. Rate Limiting 미들웨어 통합
3. 로깅 최적화

### Week 3-4: Performance
1. Connection Pool 모니터링
2. 캐시 전략 개선
3. 배치 처리 최적화

### Week 5-6: Observability
1. OpenTelemetry 통합
2. 헬스 체크 개선
3. 메트릭 대시보드 구축

---

## 💡 장기 로드맵 (3-6개월)

1. **마이크로서비스 분리**
   - Document Processing Service
   - Query Processing Service
   - LLM Gateway Service

2. **스케일링 전략**
   - Horizontal Pod Autoscaling
   - Database Read Replicas
   - CDN for Static Assets

3. **고급 기능**
   - Multi-tenancy Support
   - Advanced Analytics
   - A/B Testing Framework

---

## 📊 예상 ROI

### 개선 후 기대 효과
- **성능**: 40-50% 응답 시간 단축
- **안정성**: 99.9% 가용성 달성
- **비용**: 30% 인프라 비용 절감 (캐싱 최적화)
- **개발 속도**: 50% 빠른 기능 개발 (테스트 자동화)

---

## 🔗 참고 자료

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
