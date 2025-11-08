# Agent Builder Backend Migration Guide

## Critical Updates Applied

이 가이드는 Agent Builder 백엔드의 Critical Issues를 수정한 후 필요한 마이그레이션 단계를 설명합니다.

---

## 1. 의존성 설치

### RestrictedPython 설치 (보안 강화)

```bash
cd backend
pip install RestrictedPython==7.0
```

또는 전체 requirements 재설치:

```bash
pip install -r requirements.txt
```

---

## 2. 데이터베이스 마이그레이션

Agent Builder 관련 테이블들이 이미 정의되어 있으므로, 마이그레이션을 생성하고 실행합니다.

### Step 1: 마이그레이션 생성

```bash
cd backend
alembic revision --autogenerate -m "Add Agent Builder tables"
```

### Step 2: 마이그레이션 검토

생성된 마이그레이션 파일을 확인합니다:

```bash
# 파일 위치: backend/alembic/versions/xxxx_add_agent_builder_tables.py
```

다음 테이블들이 포함되어야 합니다:
- `agents`
- `agent_versions`
- `agent_tools`
- `agent_knowledgebases`
- `tools`
- `agent_templates`
- `prompt_templates`
- `prompt_template_versions`
- `blocks`
- `block_versions`
- `block_dependencies`
- `block_test_cases`
- `workflows`
- `workflow_nodes`
- `workflow_edges`
- `workflow_executions`
- `agent_blocks`
- `agent_edges`
- `workflow_schedules`
- `workflow_webhooks`
- `workflow_subflows`
- `knowledgebases`
- `knowledgebase_documents`
- `knowledgebase_versions`
- `variables`
- `secrets`
- `agent_executions`
- `execution_steps`
- `execution_metrics`
- `execution_schedules`
- `permissions`
- `resource_shares`
- `audit_logs`

### Step 3: 마이그레이션 실행

```bash
alembic upgrade head
```

### Step 4: 마이그레이션 확인

```bash
# PostgreSQL에 접속
psql -h localhost -p 5433 -U postgres -d agenticrag

# 테이블 확인
\dt

# 특정 테이블 구조 확인
\d agents
\d workflows
\d blocks
\d knowledgebases
```

---

## 3. 초기 데이터 설정

### Built-in Tools 등록

Agent Builder가 사용할 기본 도구들을 등록합니다:

```python
# backend/scripts/init_agent_builder_tools.py
from backend.db.database import SessionLocal
from backend.db.models.agent_builder import Tool
import uuid

def init_builtin_tools():
    """Initialize built-in tools for Agent Builder."""
    
    db = SessionLocal()
    
    try:
        # Vector Search Tool
        vector_search = Tool(
            id="vector_search",
            name="Vector Search",
            description="Search documents using semantic similarity",
            category="search",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"}
                }
            },
            implementation_type="builtin",
            implementation_ref="backend.services.hybrid_search.HybridSearchService",
            is_builtin=True
        )
        
        # Web Search Tool
        web_search = Tool(
            id="web_search",
            name="Web Search",
            description="Search the web using DuckDuckGo",
            category="search",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"}
                }
            },
            implementation_type="builtin",
            implementation_ref="backend.services.web_search_service.WebSearchService",
            is_builtin=True
        )
        
        # Local Data Tool
        local_data = Tool(
            id="local_data",
            name="Local Data Access",
            description="Access local file system data",
            category="file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"}
                }
            },
            implementation_type="builtin",
            implementation_ref="backend.agents.local_data.LocalDataAgent",
            is_builtin=True
        )
        
        # Add tools to database
        db.add(vector_search)
        db.add(web_search)
        db.add(local_data)
        
        db.commit()
        
        print("✅ Built-in tools initialized successfully")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to initialize tools: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_builtin_tools()
```

실행:

```bash
cd backend
python scripts/init_agent_builder_tools.py
```

---

## 4. 코드 변경사항 적용

### 4.1 Workflow Service 업데이트

기존 `backend/api/agent_builder/workflows.py` 파일을 백업하고 새 버전으로 교체:

```bash
cd backend/api/agent_builder
cp workflows.py workflows.py.backup
cp workflows_fixed.py workflows.py
```

### 4.2 Block Service 보안 업데이트

Block Service는 이미 업데이트되었습니다. 변경사항:
- `_execute_logic_block()` 메서드가 `SecureBlockExecutor` 사용
- `exec()` 직접 호출 제거
- RestrictedPython 기반 안전한 실행

### 4.3 Agent Service 트랜잭션 관리 개선

Agent Service는 이미 업데이트되었습니다. 변경사항:
- 모든 create/update 메서드에 try-except-rollback 추가
- Validation을 transaction 시작 전에 수행
- 명확한 에러 메시지 제공

---

## 5. 테스트

### 5.1 Unit Tests

```bash
cd backend
pytest tests/unit/services/test_agent_service.py -v
pytest tests/unit/services/test_workflow_service.py -v
pytest tests/unit/services/test_block_service.py -v
```

### 5.2 Integration Tests

```bash
pytest tests/integration/test_agent_builder_api.py -v
```

### 5.3 Security Tests

Logic Block 보안 테스트:

```python
# tests/unit/services/test_block_executor_secure.py
import pytest
from backend.services.agent_builder.block_executor_secure import SecureBlockExecutor

def test_secure_executor_basic():
    """Test basic secure execution."""
    executor = SecureBlockExecutor()
    
    code = """
output = input['value'] * 2
"""
    
    result = executor.execute_logic_block(
        code=code,
        input_data={'value': 5},
        context={}
    )
    
    assert result['output'] == 10


def test_secure_executor_blocks_dangerous_code():
    """Test that dangerous code is blocked."""
    executor = SecureBlockExecutor()
    
    # Try to import os (should fail)
    code = """
import os
output = os.listdir('/')
"""
    
    with pytest.raises(ValueError):
        executor.execute_logic_block(
            code=code,
            input_data={},
            context={}
        )


def test_secure_executor_blocks_file_access():
    """Test that file access is blocked."""
    executor = SecureBlockExecutor()
    
    code = """
with open('/etc/passwd', 'r') as f:
    output = f.read()
"""
    
    with pytest.raises(ValueError):
        executor.execute_logic_block(
            code=code,
            input_data={},
            context={}
        )


def test_secure_executor_timeout():
    """Test execution timeout."""
    executor = SecureBlockExecutor()
    executor.max_execution_time = 1  # 1 second
    
    # Infinite loop (should timeout)
    code = """
while True:
    pass
"""
    
    with pytest.raises(TimeoutError):
        executor.execute_logic_block(
            code=code,
            input_data={},
            context={}
        )
```

실행:

```bash
pytest tests/unit/services/test_block_executor_secure.py -v
```

---

## 6. 환경 변수 설정

`.env` 파일에 Agent Builder 관련 설정 추가:

```bash
# Agent Builder Configuration
AGENT_BUILDER_ENABLED=true
AGENT_BUILDER_MAX_AGENTS_PER_USER=50
AGENT_BUILDER_MAX_WORKFLOWS_PER_USER=100
AGENT_BUILDER_MAX_BLOCKS_PER_USER=200

# Block Execution Security
BLOCK_EXECUTOR_TYPE=restricted  # restricted or docker
BLOCK_EXECUTOR_TIMEOUT=5  # seconds
BLOCK_EXECUTOR_MAX_MEMORY=128  # MB

# Docker Executor (optional)
DOCKER_ENABLED=false
DOCKER_IMAGE=python:3.10-alpine
```

---

## 7. API 테스트

### 7.1 Agent 생성 테스트

```bash
curl -X POST http://localhost:8000/api/agent-builder/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Agent",
    "description": "A test agent",
    "agent_type": "custom",
    "llm_provider": "ollama",
    "llm_model": "llama3.1",
    "tool_ids": ["vector_search"],
    "knowledgebase_ids": []
  }'
```

### 7.2 Workflow 생성 테스트

```bash
curl -X POST http://localhost:8000/api/agent-builder/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Workflow",
    "description": "A test workflow",
    "nodes": [
      {
        "id": "node_1",
        "node_type": "agent",
        "node_ref_id": "AGENT_ID",
        "position_x": 100,
        "position_y": 100,
        "configuration": {}
      }
    ],
    "edges": [],
    "entry_point": "node_1"
  }'
```

### 7.3 Block 테스트

```bash
curl -X POST http://localhost:8000/api/agent-builder/blocks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Logic Block",
    "description": "A test logic block",
    "block_type": "logic",
    "input_schema": {
      "type": "object",
      "properties": {
        "value": {"type": "number"}
      },
      "required": ["value"]
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "result": {"type": "number"}
      }
    },
    "implementation": "output = input[\"value\"] * 2"
  }'
```

---

## 8. 모니터링 설정

### 8.1 Prometheus Metrics

Agent Builder 메트릭 추가:

```python
# backend/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Agent metrics
agent_created_total = Counter(
    'agent_builder_agent_created_total',
    'Total agents created',
    ['agent_type']
)

agent_execution_duration = Histogram(
    'agent_builder_agent_execution_seconds',
    'Agent execution duration',
    ['agent_id', 'status']
)

# Workflow metrics
workflow_created_total = Counter(
    'agent_builder_workflow_created_total',
    'Total workflows created'
)

workflow_execution_duration = Histogram(
    'agent_builder_workflow_execution_seconds',
    'Workflow execution duration',
    ['workflow_id', 'status']
)

# Block metrics
block_execution_duration = Histogram(
    'agent_builder_block_execution_seconds',
    'Block execution duration',
    ['block_id', 'block_type', 'status']
)

block_execution_errors = Counter(
    'agent_builder_block_execution_errors_total',
    'Total block execution errors',
    ['block_id', 'error_type']
)
```

### 8.2 Logging

구조화된 로깅 설정:

```python
# backend/core/structured_logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured logger for Agent Builder."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_agent_creation(self, user_id: str, agent_id: str, agent_type: str):
        """Log agent creation event."""
        self.logger.info(json.dumps({
            "event": "agent_created",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "agent_id": agent_id,
            "agent_type": agent_type
        }))
    
    def log_workflow_execution(
        self,
        workflow_id: str,
        execution_id: str,
        status: str,
        duration_ms: int
    ):
        """Log workflow execution event."""
        self.logger.info(json.dumps({
            "event": "workflow_executed",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": status,
            "duration_ms": duration_ms
        }))
```

---

## 9. 롤백 절차

문제가 발생한 경우 롤백:

### 9.1 코드 롤백

```bash
cd backend/api/agent_builder
cp workflows.py.backup workflows.py
```

### 9.2 데이터베이스 롤백

```bash
cd backend
alembic downgrade -1  # 한 단계 롤백
# 또는
alembic downgrade <revision_id>  # 특정 버전으로 롤백
```

### 9.3 의존성 롤백

```bash
pip uninstall RestrictedPython
```

---

## 10. 체크리스트

마이그레이션 완료 후 확인사항:

- [ ] RestrictedPython 설치 완료
- [ ] 데이터베이스 마이그레이션 실행 완료
- [ ] 모든 Agent Builder 테이블 생성 확인
- [ ] Built-in tools 등록 완료
- [ ] Unit tests 통과
- [ ] Integration tests 통과
- [ ] Security tests 통과
- [ ] API 엔드포인트 정상 작동 확인
- [ ] 로깅 및 모니터링 설정 완료
- [ ] 환경 변수 설정 완료

---

## 11. 문제 해결

### Issue: RestrictedPython 설치 실패

```bash
# 최신 pip로 업그레이드
pip install --upgrade pip

# 재시도
pip install RestrictedPython==7.0
```

### Issue: 마이그레이션 충돌

```bash
# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history

# 충돌 해결 후 재시도
alembic upgrade head
```

### Issue: Block 실행 실패

로그 확인:

```bash
tail -f logs/backend.log | grep "block_executor"
```

디버그 모드로 실행:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 12. 다음 단계

Critical Issues 수정 완료 후:

1. **Important Improvements (P1)** 적용
   - Missing Pydantic models 추가
   - Workflow validation 강화
   - API response 일관성 개선

2. **Nice-to-Have (P2)** 적용
   - Caching layer 구현
   - Metrics & monitoring 강화
   - Audit logging 구현

3. **Frontend 통합**
   - Agent Builder UI 연결
   - Workflow Designer 통합
   - Block Library UI 구현

---

## 참고 자료

- [RestrictedPython Documentation](https://restrictedpython.readthedocs.io/)
- [SQLAlchemy Migrations](https://alembic.sqlalchemy.org/en/latest/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
