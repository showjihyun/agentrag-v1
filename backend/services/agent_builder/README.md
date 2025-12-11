# Agent Builder - DDD Architecture

## 🎯 Overview

Agent Builder는 Domain-Driven Design (DDD) 원칙을 따르는 엔터프라이즈급 워크플로우 실행 엔진입니다.

## 📁 Structure

```
backend/services/agent_builder/
├── domain/                    # 비즈니스 로직 (순수)
│   ├── agent/                 # Agent Aggregate
│   ├── workflow/              # Workflow Aggregate
│   ├── execution/             # Execution Aggregate
│   └── block/                 # Block Aggregate
│
├── application/               # 유스케이스
│   ├── commands/              # Write operations (CQRS)
│   ├── queries/               # Read operations (CQRS)
│   ├── agent_application_service.py
│   ├── workflow_application_service.py
│   └── execution_application_service.py
│
├── infrastructure/            # 기술적 구현
│   ├── execution/             # 실행 엔진
│   │   ├── executor.py        # UnifiedExecutor
│   │   └── node_handlers/     # 7개 핸들러
│   ├── persistence/           # Repository 구현
│   └── messaging/             # Event Bus
│
├── shared/                    # 공통 유틸리티
│   ├── errors.py
│   ├── validators.py
│   └── utils.py
│
├── facade.py                  # 통합 API
├── dependencies.py            # FastAPI Dependencies
│
└── docs/
    ├── DDD_ARCHITECTURE.md
    ├── DDD_VERIFICATION_REPORT.md
    ├── MIGRATION_GUIDE.md
    └── DDD_IMPROVEMENTS.md
```

## 🚀 Quick Start

### 1. Facade 사용 (권장)

```python
from backend.services.agent_builder.dependencies import get_agent_builder_facade

@router.post("/workflows")
async def create_workflow(
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
):
    workflow = facade.create_workflow(
        user_id=user_id,
        name="My Workflow",
        nodes=[...],
        edges=[...],
    )
    return workflow
```

### 2. Application Service 사용

```python
from backend.services.agent_builder.dependencies import get_workflow_service

@router.post("/workflows")
async def create_workflow(
    service: WorkflowApplicationService = Depends(get_workflow_service),
):
    workflow = service.create_workflow(...)
    return workflow
```

### 3. CQRS 사용

```python
from backend.services.agent_builder.dependencies import (
    get_workflow_command_handler,
    get_workflow_query_handler,
)

# Write
@router.post("/workflows")
async def create_workflow(
    handler = Depends(get_workflow_command_handler),
):
    command = CreateWorkflowCommand(...)
    workflow = handler.handle_create(command)
    return workflow

# Read
@router.get("/workflows/{id}")
async def get_workflow(
    workflow_id: str,
    handler = Depends(get_workflow_query_handler),
):
    query = GetWorkflowQuery(workflow_id=workflow_id)
    workflow = handler.handle_get(query)
    return workflow
```

## 📚 Documentation

| 문서 | 설명 |
|------|------|
| [DDD_ARCHITECTURE.md](./DDD_ARCHITECTURE.md) | DDD 구조 상세 설명 |
| [DDD_VERIFICATION_REPORT.md](./DDD_VERIFICATION_REPORT.md) | 검증 결과 리포트 |
| [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) | 레거시 코드 마이그레이션 가이드 |
| [DDD_IMPROVEMENTS.md](./DDD_IMPROVEMENTS.md) | 최신 개선사항 |

## 🧪 Testing

### 검증 스크립트 실행

```bash
cd backend
python verify_ddd_architecture.py
```

### 통합 테스트 실행

```bash
cd backend
pytest tests/integration/test_ddd_workflow.py -v
```

## 🎨 Architecture Patterns

### Domain-Driven Design (DDD)
- **Aggregates**: Agent, Workflow, Execution, Block
- **Entities**: 비즈니스 객체
- **Value Objects**: 불변 값 객체
- **Domain Events**: 도메인 이벤트
- **Repository Interfaces**: 저장소 인터페이스

### CQRS (Command Query Responsibility Segregation)
- **Commands**: 쓰기 작업
- **Queries**: 읽기 작업
- **Handlers**: 명령/쿼리 처리

### Event-Driven Architecture
- **Event Bus**: 이벤트 발행/구독
- **Domain Events**: 비즈니스 이벤트
- **Event Handlers**: 이벤트 처리

### Facade Pattern
- **Unified Interface**: 통합 API
- **Simplified Access**: 간편한 접근
- **Backward Compatibility**: 하위 호환성

## 🔧 Components

### Domain Layer (4 Aggregates)
- **AgentAggregate**: AI 에이전트 관리
- **WorkflowAggregate**: 워크플로우 그래프 관리
- **ExecutionAggregate**: 실행 상태 추적
- **BlockAggregate**: 재사용 가능한 블록

### Application Layer (3 Services + CQRS)
- **AgentApplicationService**: Agent 유스케이스
- **WorkflowApplicationService**: Workflow 유스케이스
- **ExecutionApplicationService**: Execution 유스케이스
- **Command/Query Handlers**: CQRS 패턴

### Infrastructure Layer
- **UnifiedExecutor**: 통합 실행 엔진
- **7 Node Handlers**: Agent, Tool, LLM, Condition, Code, HTTP, Start/End
- **3 Repository Implementations**: Agent, Workflow, Execution
- **EventBus**: 이벤트 버스

## 📊 API Examples

### Reference Implementation

새로운 DDD 패턴을 사용하는 참조 구현:

```
GET  /api/agent-builder/workflows-ddd/comparison
POST /api/agent-builder/workflows-ddd/facade
GET  /api/agent-builder/workflows-ddd/facade/{id}
POST /api/agent-builder/workflows-ddd/facade/{id}/execute
GET  /api/agent-builder/workflows-ddd/facade/{id}/execute/stream
```

자세한 내용은 `backend/api/agent_builder/workflows_ddd.py` 참조

## 🎯 Migration Path

### Phase 1: 핵심 기능 (완료)
- ✅ DDD 구조 구현
- ✅ Facade 패턴
- ✅ Application Services
- ✅ CQRS 패턴
- ✅ UnifiedExecutor

### Phase 2: API 마이그레이션 (진행 중)
- ⏳ Workflow API → Facade
- ⏳ Agent API → Application Service
- ⏳ Execution API → CQRS

### Phase 3: 레거시 정리 (예정)
- ⏳ 중복 코드 제거
- ⏳ 사용하지 않는 파일 제거
- ⏳ 문서 업데이트

## 🔍 Verification

### 자동 검증

```bash
python verify_ddd_architecture.py
```

### 수동 검증

```python
# 1. Domain Layer
from backend.services.agent_builder.domain.workflow.aggregate import WorkflowAggregate

# 2. Application Layer
from backend.services.agent_builder.application import WorkflowApplicationService

# 3. Infrastructure Layer
from backend.services.agent_builder.infrastructure.execution import UnifiedExecutor

# 4. Facade
from backend.services.agent_builder.facade import AgentBuilderFacade
```

## 🤝 Contributing

### 새 기능 추가시

1. **Domain Layer**: 비즈니스 로직 추가
2. **Application Layer**: 유스케이스 구현
3. **Infrastructure Layer**: 기술적 구현
4. **API Layer**: 엔드포인트 추가
5. **Tests**: 테스트 작성
6. **Documentation**: 문서 업데이트

### 코드 스타일

- Domain: 순수 Python, 외부 의존성 없음
- Application: Domain에만 의존
- Infrastructure: Domain에만 의존
- Shared: 모든 레이어에서 사용 가능

## 📈 Performance

### 목표
- Workflow 실행: <5초
- API 응답: <100ms
- 캐시 히트율: >60%

### 최적화
- Multi-level caching (L1 + L2)
- Connection pooling
- Async execution
- Event-driven architecture

## 🔒 Security

- Input validation
- Authorization checks
- Secure execution sandbox
- Audit logging
- Secret management

## 📞 Support

- **Documentation**: 이 디렉토리의 MD 파일들
- **Examples**: `backend/api/agent_builder/workflows_ddd.py`
- **Tests**: `backend/tests/integration/test_ddd_workflow.py`
- **Verification**: `backend/verify_ddd_architecture.py`

## 📝 License

Copyright © 2025 Agentic RAG System

---

**Version**: 1.0  
**Last Updated**: 2025-12-06  
**Status**: ✅ Production Ready
