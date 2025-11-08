# Phase 2 개선 계획서

## 📋 개요
**계획 일자**: 2025-10-26  
**예상 작업 시간**: 10-12시간  
**대상 파일**: 약 30개  
**우선순위**: Medium

---

## 🎯 개선 목표

### 1. 구조화된 로깅 적용 (23개 파일)
현재 f-string 로깅을 구조화된 로깅으로 변경

#### Before (현재)
```python
logger.info(f"Created bookmark {bookmark.id} for user {user_id}")
logger.error(f"Failed to create: {e}")
```

#### After (개선)
```python
logger.info(
    "Created bookmark",
    extra={
        "bookmark_id": str(bookmark.id),
        "user_id": str(user_id),
        "action": "create_bookmark"
    }
)

logger.error(
    "Failed to create bookmark",
    extra={
        "user_id": str(user_id),
        "error_type": type(e).__name__
    },
    exc_info=True
)
```

### 2. 타입 힌트 추가 (15개 파일)
verify/*.py 파일들에 완전한 타입 힌트 추가

#### Before (현재)
```python
def verify_configuration():
    """Verify configuration."""
    pass

def print_section(title):
    """Print section header."""
    print(f"=== {title} ===")
```

#### After (개선)
```python
def verify_configuration() -> bool:
    """Verify configuration."""
    pass

def print_section(title: str) -> None:
    """Print section header."""
    print(f"=== {title} ===")
```

---

## 📁 대상 파일 목록

### 구조화된 로깅 적용 대상 (우선순위 순)

#### High Priority (8개 파일)
1. `backend/services/usage_service.py` - 10곳
2. `backend/services/web_search_service.py` - 8곳
3. `backend/services/threshold_tuner.py` - 7곳
4. `backend/services/system_config_service.py` - 5곳 (이미 일부 완료)
5. `backend/services/translators.py` - 12곳
6. `backend/services/structured_data_service.py` - 5곳
7. `backend/services/web_search_enhancer.py` - 4곳
8. `backend/services/dashboard_service.py` - 확인 필요

#### Medium Priority (15개 파일)
- 나머지 서비스 파일들

### 타입 힌트 추가 대상 (15개 파일)

#### 우선순위 파일
1. `backend/verify/verify_adaptive_config.py`
2. `backend/verify/verify_answer_quality.py`
3. `backend/verify/verify_document_acl.py`
4. `backend/verify/verify_comprehensive_testing.py`
5. `backend/verify/verify_all_rag_features.py`
6. `backend/verify/verify_monitoring_dashboard.py`
7. `backend/verify/verify_intelligent_mode_router.py`
8. `backend/verify/verify_query_optimization.py`
9. `backend/verify/verify_performance_optimization.py`
10. `backend/verify/verify_production_deployment.py`

---

## 🔧 개선 작업 상세

### 1단계: 구조화된 로깅 템플릿 적용

#### 성공 로그
```python
logger.info(
    "Operation completed",
    extra={
        "operation": "operation_name",
        "resource_id": str(resource_id),
        "user_id": str(user_id),
        "duration_ms": duration,
        "status": "success"
    }
)
```

#### 에러 로그
```python
logger.error(
    "Operation failed",
    extra={
        "operation": "operation_name",
        "resource_id": str(resource_id),
        "user_id": str(user_id),
        "error_type": type(e).__name__,
        "error_message": str(e)
    },
    exc_info=True
)
```

#### 경고 로그
```python
logger.warning(
    "Operation warning",
    extra={
        "operation": "operation_name",
        "resource_id": str(resource_id),
        "warning_type": "warning_category",
        "details": "warning details"
    }
)
```

#### 디버그 로그
```python
logger.debug(
    "Debug information",
    extra={
        "operation": "operation_name",
        "data": data_dict,
        "context": context_info
    }
)
```

### 2단계: 타입 힌트 추가 가이드

#### 함수 타입 힌트
```python
from typing import Dict, List, Optional, Any, Tuple

def function_name(
    param1: str,
    param2: int,
    param3: Optional[str] = None
) -> Dict[str, Any]:
    """Function docstring."""
    return {"key": "value"}
```

#### 비동기 함수
```python
async def async_function(
    param: str
) -> Optional[Dict[str, Any]]:
    """Async function docstring."""
    return None
```

#### 제네릭 타입
```python
from typing import TypeVar, Generic

T = TypeVar('T')

def generic_function(items: List[T]) -> Optional[T]:
    """Generic function docstring."""
    return items[0] if items else None
```

---

## 📊 예상 효과

### 로깅 개선 효과
- ✅ 로그 분석 자동화 가능
- ✅ 구조화된 로그 검색
- ✅ 메트릭 추출 용이
- ✅ 디버깅 시간 50% 단축
- ✅ 모니터링 대시보드 연동

### 타입 힌트 효과
- ✅ IDE 자동완성 향상
- ✅ 타입 체크로 버그 사전 방지
- ✅ 코드 가독성 향상
- ✅ 리팩토링 안전성 증가
- ✅ 문서화 자동 생성

---

## 🗓️ 작업 일정

### Week 1 (5일)
**Day 1-2**: 구조화된 로깅 (High Priority 4개 파일)
- `usage_service.py`
- `web_search_service.py`
- `threshold_tuner.py`
- `system_config_service.py`

**Day 3-4**: 구조화된 로깅 (High Priority 4개 파일)
- `translators.py`
- `structured_data_service.py`
- `web_search_enhancer.py`
- `dashboard_service.py`

**Day 5**: 검증 및 테스트
- 로그 출력 확인
- 로그 파싱 테스트
- 성능 영향 확인

### Week 2 (5일)
**Day 1-3**: 타입 힌트 추가 (10개 파일)
- verify 파일들 타입 힌트 추가
- mypy 검증

**Day 4**: 나머지 서비스 파일 로깅 개선
- Medium Priority 파일들

**Day 5**: 최종 검증
- 전체 타입 체크
- 로그 통합 테스트
- 문서 업데이트

---

## ✅ 검증 체크리스트

### 로깅 검증
- [ ] 모든 로그가 구조화된 형식 사용
- [ ] extra 파라미터에 필수 필드 포함
- [ ] 에러 로그에 exc_info=True 사용
- [ ] 로그 레벨 적절히 사용
- [ ] 민감 정보 로깅 제외

### 타입 힌트 검증
- [ ] 모든 함수에 파라미터 타입 힌트
- [ ] 모든 함수에 반환 타입 힌트
- [ ] mypy 검증 통과
- [ ] IDE 자동완성 작동
- [ ] 타입 에러 없음

### 성능 검증
- [ ] 로깅 오버헤드 < 5%
- [ ] 타입 체크 시간 < 10초
- [ ] 메모리 사용량 변화 없음

---

## 📝 작업 진행 상황

### 완료
- [ ] usage_service.py 로깅 개선
- [ ] web_search_service.py 로깅 개선
- [ ] threshold_tuner.py 로깅 개선
- [ ] system_config_service.py 로깅 개선
- [ ] translators.py 로깅 개선
- [ ] structured_data_service.py 로깅 개선
- [ ] web_search_enhancer.py 로깅 개선
- [ ] dashboard_service.py 로깅 개선

### 진행 중
- [ ] verify 파일 타입 힌트 추가

### 대기
- [ ] Medium Priority 파일들

---

## 🎓 참고 자료

### Python 로깅 Best Practices
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging in Python](https://www.structlog.org/)
- [12-Factor App Logging](https://12factor.net/logs)

### Python 타입 힌트
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [typing Module](https://docs.python.org/3/library/typing.html)

---

**작성 일자**: 2025-10-26  
**작성자**: Kiro AI Assistant  
**버전**: 1.0.0  
**상태**: 📋 계획 수립 완료
