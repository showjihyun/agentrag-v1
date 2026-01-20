# AgenticBuilder 워크플로우 시스템

## 개요

AgenticBuilder의 워크플로우 시스템은 시각적 인터페이스를 통해 복잡한 AI 에이전트 워크플로우를 구축하고 실행할 수 있는 핵심 기능입니다.

## 워크플로우 구성 요소

### 1. 블록 (Blocks)

워크플로우의 기본 구성 단위로, 50개 이상의 사전 구축된 블록을 제공합니다.

#### 블록 카테고리

**Agents (에이전트)**
- General Agent: 범용 AI 에이전트
- Control Agent: 워크플로우 제어 에이전트
- Specialized Agent: 특화 에이전트 (Vector Search, Web Search, Local Data)

**Triggers (트리거)**
- Webhook: HTTP 웹훅 트리거
- Schedule: 시간 기반 스케줄
- Event: 이벤트 기반 트리거
- Manual: 수동 실행

**Actions (액션)**
- Database: 데이터베이스 작업
- API Call: REST API 호출
- File Operation: 파일 읽기/쓰기
- Email: 이메일 발송
- Slack: Slack 메시지
- Discord: Discord 메시지

**Data & Knowledge (데이터 & 지식)**
- Vector Search: 벡터 검색
- Knowledge Base: 지식 베이스 조회
- Document Processing: 문서 처리
- Data Transform: 데이터 변환

**Control Flow (제어 흐름)**
- Condition: 조건 분기
- Loop: 반복
- Switch: 다중 분기
- Merge: 결과 병합

**Orchestration (오케스트레이션)**
- Sequential: 순차 실행
- Parallel: 병렬 실행
- Hierarchical: 계층적 실행
- Adaptive: 적응형 실행

### 2. 연결 (Edges)

블록 간의 데이터 흐름을 정의합니다.

```json
{
  "source_block_id": "uuid",
  "target_block_id": "uuid",
  "source_handle": "output",
  "target_handle": "input",
  "config": {
    "transform": "optional_data_transformation"
  }
}
```

### 3. 워크플로우 정의

```json
{
  "name": "Customer Support Workflow",
  "orchestration_pattern": "sequential",
  "graph_definition": {
    "nodes": [
      {
        "id": "trigger_1",
        "type": "webhook",
        "position": {"x": 100, "y": 100},
        "config": {
          "method": "POST",
          "path": "/support/ticket"
        }
      },
      {
        "id": "agent_1",
        "type": "general_agent",
        "position": {"x": 300, "y": 100},
        "config": {
          "agent_id": "uuid",
          "system_prompt": "You are a customer support agent..."
        }
      },
      {
        "id": "action_1",
        "type": "database",
        "position": {"x": 500, "y": 100},
        "config": {
          "operation": "insert",
          "table": "support_tickets"
        }
      }
    ],
    "edges": [
      {
        "source": "trigger_1",
        "target": "agent_1"
      },
      {
        "source": "agent_1",
        "target": "action_1"
      }
    ]
  }
}
```

## 오케스트레이션 패턴

### 1. Sequential (순차)

블록이 순서대로 실행됩니다.

```
Trigger → Agent 1 → Agent 2 → Action → End
```

**사용 사례:**
- 단계별 데이터 처리
- 순차적 의사결정
- 파이프라인 처리

### 2. Parallel (병렬)

여러 블록이 동시에 실행됩니다.

```
         ┌─> Agent 1 ─┐
Trigger ─┼─> Agent 2 ─┼─> Merge → End
         └─> Agent 3 ─┘
```

**사용 사례:**
- 다중 소스 데이터 수집
- 병렬 분석
- 성능 최적화

### 3. Hierarchical (계층적)

마스터 에이전트가 하위 에이전트를 관리합니다.

```
Master Agent
    ├─> Sub Agent 1
    ├─> Sub Agent 2
    └─> Sub Agent 3
```

**사용 사례:**
- 복잡한 작업 분해
- 역할 기반 처리
- 계층적 의사결정

### 4. Adaptive (적응형)

실행 중 동적으로 경로를 선택합니다.

```
Trigger → Router Agent → [Dynamic Selection]
                              ├─> Path A
                              ├─> Path B
                              └─> Path C
```

**사용 사례:**
- 컨텍스트 기반 라우팅
- 동적 워크플로우
- 지능형 분기

### 5. Consensus Building (합의 구축)

여러 에이전트의 결과를 종합하여 최종 결정을 내립니다.

```
         ┌─> Agent 1 ─┐
Input ──┼─> Agent 2 ─┼─> Consensus Agent → Decision
         └─> Agent 3 ─┘
```

**사용 사례:**
- 다중 관점 분석
- 의사결정 검증
- 품질 보증

### 6. Swarm Intelligence (군집 지능)

다수의 에이전트가 협력하여 문제를 해결합니다.

```
Coordinator
    ├─> Worker 1 ─┐
    ├─> Worker 2 ─┤
    ├─> Worker 3 ─┼─> Aggregator → Result
    ├─> Worker 4 ─┤
    └─> Worker 5 ─┘
```

**사용 사례:**
- 대규모 데이터 처리
- 분산 검색
- 최적화 문제

### 7. Event-Driven (이벤트 기반)

이벤트에 반응하여 워크플로우가 실행됩니다.

```
Event Bus
    ├─> Event 1 → Handler 1
    ├─> Event 2 → Handler 2
    └─> Event 3 → Handler 3
```

**사용 사례:**
- 실시간 처리
- 비동기 작업
- 마이크로서비스 통합

### 8. Reflection (자기 성찰)

에이전트가 자신의 출력을 검토하고 개선합니다.

```
Agent → Output → Reflection Agent → [Improve/Accept]
  ↑                                        |
  └────────────────────────────────────────┘
```

**사용 사례:**
- 품질 개선
- 자가 수정
- 반복적 개선

## 워크플로우 실행

### 실행 프로세스

```
1. 트리거 발생
   ↓
2. 워크플로우 로드
   ↓
3. 실행 계획 수립
   ↓
4. 블록 순차/병렬 실행
   ├─ 입력 데이터 준비
   ├─ 블록 실행
   ├─ 출력 데이터 수집
   └─ 다음 블록으로 전달
   ↓
5. 결과 집계
   ↓
6. 실행 완료
```

### 실행 상태

- **pending**: 대기 중
- **running**: 실행 중
- **completed**: 완료
- **failed**: 실패
- **cancelled**: 취소됨
- **paused**: 일시 중지

### 실시간 모니터링

Server-Sent Events (SSE)를 통해 실시간으로 실행 상태를 모니터링할 수 있습니다.

```javascript
const eventSource = new EventSource(
  '/api/agent-builder/executions/{execution_id}/stream'
);

eventSource.addEventListener('status', (e) => {
  const data = JSON.parse(e.data);
  console.log('Status:', data.status, 'Progress:', data.progress);
});

eventSource.addEventListener('node_start', (e) => {
  const data = JSON.parse(e.data);
  console.log('Node started:', data.node_id);
});

eventSource.addEventListener('node_complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('Node completed:', data.node_id, 'Output:', data.output);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('Workflow completed:', data.output);
  eventSource.close();
});
```

## 데이터 흐름

### 블록 간 데이터 전달

```json
{
  "input": {
    "customer_email": "customer@example.com",
    "issue_description": "Cannot login to account"
  },
  "output": {
    "ticket_id": "TICKET-12345",
    "priority": "high",
    "assigned_to": "support_team"
  }
}
```

### 데이터 변환

```json
{
  "transform": {
    "type": "jq",
    "expression": ".customer_email | split(\"@\") | .[0]"
  }
}
```

## 에러 처리

### 재시도 전략

```json
{
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential",
    "initial_delay_ms": 1000,
    "max_delay_ms": 10000
  }
}
```

### Circuit Breaker

```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "timeout_ms": 30000,
    "reset_timeout_ms": 60000
  }
}
```

### Fallback

```json
{
  "fallback": {
    "type": "default_value",
    "value": {
      "status": "error",
      "message": "Service unavailable"
    }
  }
}
```

## 성능 최적화

### 캐싱

```json
{
  "cache": {
    "enabled": true,
    "ttl_seconds": 3600,
    "key_pattern": "workflow:{workflow_id}:input:{hash}"
  }
}
```

### 병렬 실행

```json
{
  "parallel": {
    "max_concurrent": 5,
    "timeout_ms": 30000
  }
}
```

### 배치 처리

```json
{
  "batch": {
    "size": 100,
    "timeout_ms": 5000
  }
}
```

## 버전 관리

### 워크플로우 버전

```json
{
  "version": 2,
  "changelog": "Added error handling and retry logic",
  "previous_version_id": "uuid"
}
```

### 롤백

```http
POST /api/agent-builder/workflows/{workflow_id}/rollback
{
  "target_version": 1
}
```

## 테스팅

### 단위 테스트

```http
POST /api/agent-builder/workflows/{workflow_id}/test
{
  "test_input": {
    "customer_email": "test@example.com"
  },
  "expected_output": {
    "ticket_id": "TICKET-*"
  }
}
```

### 통합 테스트

```http
POST /api/agent-builder/workflows/{workflow_id}/test/suite
{
  "test_cases": [
    {
      "name": "Happy path",
      "input": {...},
      "expected": {...}
    },
    {
      "name": "Error handling",
      "input": {...},
      "expected": {...}
    }
  ]
}
```

## 모범 사례

### 1. 워크플로우 설계

- 단일 책임 원칙: 각 워크플로우는 하나의 명확한 목적
- 재사용 가능한 블록: 공통 로직을 재사용 가능한 블록으로 분리
- 에러 처리: 모든 블록에 적절한 에러 처리 추가

### 2. 성능

- 병렬 실행: 독립적인 작업은 병렬로 실행
- 캐싱: 반복적인 작업 결과 캐싱
- 타임아웃: 모든 블록에 적절한 타임아웃 설정

### 3. 모니터링

- 로깅: 중요한 단계마다 로그 기록
- 메트릭: 실행 시간, 성공률 등 메트릭 수집
- 알림: 실패 시 알림 설정

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-20
