# AgenticBuilder API 레퍼런스

## 개요

AgenticBuilder는 RESTful API를 제공하며, FastAPI 기반으로 구축되어 자동 문서화(OpenAPI/Swagger)를 지원합니다.

**Base URL**: `http://localhost:8000`  
**API 문서**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`

## 인증

### JWT 토큰 기반 인증

```http
Authorization: Bearer <access_token>
```

### 토큰 획득

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## API 엔드포인트

### 1. 인증 & 사용자 관리

#### 회원가입
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "John Doe"
}
```

#### 로그인
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### 토큰 갱신
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### 2. 에이전트 관리

#### 에이전트 목록 조회
```http
GET /api/agent-builder/agents
Authorization: Bearer <access_token>

Query Parameters:
- page: 페이지 번호 (default: 1)
- limit: 페이지 크기 (default: 20)
- agent_type: 에이전트 타입 필터
- is_active: 활성 상태 필터
```

**응답:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Customer Support Agent",
      "description": "Handles customer inquiries",
      "agent_type": "general",
      "model_provider": "openai",
      "model_name": "gpt-4",
      "is_active": true,
      "created_at": "2026-01-20T10:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

#### 에이전트 생성
```http
POST /api/agent-builder/agents
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Data Analysis Agent",
  "description": "Analyzes data and generates insights",
  "agent_type": "specialized",
  "system_prompt": "You are a data analysis expert...",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "config": {
    "tools": ["python_code", "data_visualization"]
  }
}
```

#### 에이전트 상세 조회
```http
GET /api/agent-builder/agents/{agent_id}
Authorization: Bearer <access_token>
```

#### 에이전트 수정
```http
PUT /api/agent-builder/agents/{agent_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Agent Name",
  "description": "Updated description",
  "is_active": true
}
```

#### 에이전트 삭제
```http
DELETE /api/agent-builder/agents/{agent_id}
Authorization: Bearer <access_token>
```

### 3. 워크플로우 관리

#### 워크플로우 목록 조회
```http
GET /api/agent-builder/workflows
Authorization: Bearer <access_token>

Query Parameters:
- page: 페이지 번호
- limit: 페이지 크기
- is_active: 활성 상태
- orchestration_pattern: 오케스트레이션 패턴
```

#### 워크플로우 생성
```http
POST /api/agent-builder/workflows
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Customer Onboarding Flow",
  "description": "Automated customer onboarding process",
  "orchestration_pattern": "sequential",
  "graph_definition": {
    "nodes": [
      {
        "id": "node1",
        "type": "trigger",
        "config": {"type": "webhook"}
      },
      {
        "id": "node2",
        "type": "agent",
        "config": {"agent_id": "uuid"}
      }
    ],
    "edges": [
      {
        "source": "node1",
        "target": "node2"
      }
    ]
  }
}
```

#### 워크플로우 실행
```http
POST /api/agent-builder/workflows/{workflow_id}/execute
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "input_data": {
    "customer_email": "customer@example.com",
    "customer_name": "Jane Doe"
  },
  "trigger_type": "manual"
}
```

**응답:**
```json
{
  "execution_id": "uuid",
  "status": "running",
  "started_at": "2026-01-20T10:00:00Z",
  "stream_url": "/api/agent-builder/executions/{execution_id}/stream"
}
```

#### 실행 상태 조회
```http
GET /api/agent-builder/executions/{execution_id}
Authorization: Bearer <access_token>
```

**응답:**
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "input_data": {...},
  "output_data": {...},
  "execution_time_ms": 1500,
  "tokens_used": 1200,
  "cost_usd": 0.024,
  "started_at": "2026-01-20T10:00:00Z",
  "completed_at": "2026-01-20T10:00:01.5Z"
}
```

#### 실시간 스트리밍 (SSE)
```http
GET /api/agent-builder/executions/{execution_id}/stream
Authorization: Bearer <access_token>
Accept: text/event-stream
```

**이벤트 스트림:**
```
event: status
data: {"status": "running", "progress": 0.3}

event: node_start
data: {"node_id": "node2", "node_type": "agent"}

event: node_complete
data: {"node_id": "node2", "output": {...}}

event: complete
data: {"status": "completed", "output": {...}}
```

### 4. 블록 관리

#### 사용 가능한 블록 타입 조회
```http
GET /api/agent-builder/blocks/types
Authorization: Bearer <access_token>
```

**응답:**
```json
{
  "categories": [
    {
      "name": "Agents",
      "blocks": [
        {
          "type": "general_agent",
          "display_name": "General Agent",
          "description": "Multi-purpose AI agent",
          "config_schema": {...}
        }
      ]
    },
    {
      "name": "Triggers",
      "blocks": [...]
    }
  ]
}
```

#### 워크플로우 블록 추가
```http
POST /api/agent-builder/workflows/{workflow_id}/blocks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "block_type": "agent",
  "name": "Customer Service Agent",
  "position_x": 100,
  "position_y": 200,
  "config": {
    "agent_id": "uuid"
  }
}
```

### 5. 지식 베이스 관리

#### 지식 베이스 생성
```http
POST /api/knowledge-bases
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Product Documentation",
  "description": "All product documentation and FAQs",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

#### 문서 업로드
```http
POST /api/knowledge-bases/{kb_id}/documents
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary_file>
```

#### 문서 검색 (Vector Search)
```http
POST /api/knowledge-bases/{kb_id}/search
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "How to reset password?",
  "top_k": 10,
  "filters": {
    "document_type": "faq"
  }
}
```

**응답:**
```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "faq.pdf",
      "text": "To reset your password...",
      "score": 0.95,
      "metadata": {...}
    }
  ]
}
```

### 6. 모니터링 & 분석

#### 워크플로우 메트릭 조회
```http
GET /api/agent-builder/workflows/{workflow_id}/metrics
Authorization: Bearer <access_token>

Query Parameters:
- start_date: 시작 날짜 (ISO 8601)
- end_date: 종료 날짜 (ISO 8601)
```

**응답:**
```json
{
  "total_executions": 1000,
  "success_rate": 0.95,
  "avg_execution_time_ms": 1500,
  "total_tokens_used": 50000,
  "total_cost_usd": 1.25,
  "executions_by_status": {
    "completed": 950,
    "failed": 50
  }
}
```

#### 대시보드 데이터
```http
GET /api/agent-builder/dashboard
Authorization: Bearer <access_token>
```

**응답:**
```json
{
  "total_workflows": 25,
  "active_workflows": 20,
  "total_executions_today": 150,
  "success_rate_today": 0.96,
  "top_workflows": [
    {
      "workflow_id": "uuid",
      "name": "Customer Support",
      "execution_count": 50
    }
  ]
}
```

### 7. 플러그인 관리

#### 플러그인 목록 조회
```http
GET /api/plugins
Authorization: Bearer <access_token>

Query Parameters:
- category: 카테고리 필터
- is_verified: 검증 여부
```

#### 플러그인 설치
```http
POST /api/plugins/{plugin_id}/install
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "config": {
    "api_key": "your_api_key"
  }
}
```

### 8. 헬스 체크

#### 간단한 헬스 체크
```http
GET /api/health/simple
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-20T10:00:00Z"
}
```

#### 상세 헬스 체크
```http
GET /api/health
```

**응답:**
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "milvus": {
      "status": "healthy",
      "response_time_ms": 10
    }
  },
  "timestamp": "2026-01-20T10:00:00Z"
}
```

## 에러 응답

### 표준 에러 형식

```json
{
  "error": "Error message",
  "error_type": "ValidationError",
  "detail": "Detailed error description",
  "status_code": 400,
  "timestamp": "2026-01-20T10:00:00Z",
  "path": "/api/agents",
  "request_id": "uuid"
}
```

### HTTP 상태 코드

- `200 OK`: 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `422 Unprocessable Entity`: 검증 실패
- `429 Too Many Requests`: Rate Limit 초과
- `500 Internal Server Error`: 서버 에러

## Rate Limiting

### 기본 제한

- **분당**: 60 요청
- **시간당**: 1000 요청
- **일일**: 10000 요청

### Rate Limit 헤더

```http
X-RateLimit-Remaining-Minute: 59
X-RateLimit-Remaining-Hour: 999
X-RateLimit-Remaining-Day: 9999
Retry-After: 60
```

## 페이지네이션

### 표준 페이지네이션 응답

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

## WebSocket API

### 실시간 워크플로우 모니터링

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflows/{workflow_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Workflow event:', data);
};
```

**이벤트 타입:**
- `execution_start`: 실행 시작
- `node_start`: 노드 시작
- `node_complete`: 노드 완료
- `execution_complete`: 실행 완료
- `error`: 에러 발생

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-20
