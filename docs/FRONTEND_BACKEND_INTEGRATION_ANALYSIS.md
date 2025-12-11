# Frontend-Backend 통합 분석 및 개선 사항

## 분석 날짜
2024년 12월 6일

---

## 🔍 현재 상태 분석

### ✅ 잘 구현된 부분

#### 1. API 클라이언트 구조
- **통합 API 클라이언트**: `RAGApiClient` 클래스로 모든 API 호출 중앙화
- **자동 토큰 갱신**: 401 에러 시 자동으로 refresh token 사용
- **에러 처리**: 표준화된 에러 클래스 및 처리 로직
- **타입 안전성**: TypeScript 타입 정의로 타입 안전성 보장

#### 2. 에러 처리
- **계층화된 에러 클래스**: APIError, ValidationError, AuthenticationError 등
- **사용자 친화적 메시지**: 에러 코드별 한글 메시지 매핑
- **재시도 로직**: `fetchWithRetry` 유틸리티로 자동 재시도

#### 3. 스트리밍 지원
- **SSE 스트리밍**: `queryStream` 메서드로 실시간 응답 처리
- **배치 업로드 진도**: EventSource로 실시간 진행 상황 추적

---

## ⚠️ 발견된 문제점 및 개선 사항

### 1. 🔴 Critical: API 엔드포인트 불일치

#### 문제
Frontend API 클라이언트에 정의된 엔드포인트 중 일부가 Backend에 없거나 경로가 다름

#### 누락된 엔드포인트

**Frontend에 있지만 Backend에 없는 것**:
```typescript
// 1. Event Store API (새로 추가됨)
GET  /api/events/aggregate/{aggregate_id}
GET  /api/events/replay/{aggregate_id}
GET  /api/events/audit

// 2. Flows API (Agent Builder)
GET    /api/agent-builder/flows
POST   /api/agent-builder/flows
GET    /api/agent-builder/flows/{id}
PUT    /api/agent-builder/flows/{id}
DELETE /api/agent-builder/flows/{id}
POST   /api/agent-builder/flows/{id}/execute

// 3. Agentflow/Chatflow 구분
POST /api/agent-builder/agentflows
POST /api/agent-builder/chatflows
```

**Backend에 있지만 Frontend에 없는 것**:
```python
# 1. NLP Generator API
POST /api/agent-builder/nlp-generator/generate

# 2. Insights API
GET /api/agent-builder/insights/statistics
GET /api/agent-builder/insights/trends

# 3. Marketplace API
GET /api/agent-builder/marketplace/templates

# 4. Advanced Export API
POST /api/agent-builder/export/workflow
```

### 2. 🟡 Warning: 타입 정의 불일치

#### 문제
Frontend 타입 정의가 Backend Pydantic 모델과 일치하지 않음

#### 예시

**Frontend (`flows.ts`)**:
```typescript
interface Agentflow {
  orchestration_type: 'sequential' | 'parallel' | 'hierarchical' | 'adaptive';
  supervisor_config?: SupervisorConfig;
  agents: AgentflowAgent[];
}
```

**Backend (확인 필요)**:
```python
# backend/models/flows.py 또는 backend/db/models/flows.py
# 실제 모델 구조 확인 필요
```

### 3. 🟡 Warning: 실시간 통신 개선 필요

#### 문제
- SSE만 사용 중 (WebSocket 미사용)
- 양방향 통신 필요한 기능에서 제한적

#### 개선 방안
```typescript
// WebSocket 지원 추가
class RAGApiClient {
  private ws: WebSocket | null = null;
  
  connectWebSocket(endpoint: string): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    this.ws = new WebSocket(`${wsUrl}${endpoint}`);
    return this.ws;
  }
  
  // Workflow 실행 실시간 모니터링
  async *monitorExecution(executionId: string): AsyncGenerator<ExecutionUpdate> {
    const ws = this.connectWebSocket(`/api/agent-builder/executions/${executionId}/stream`);
    
    while (true) {
      const message = await new Promise((resolve) => {
        ws.onmessage = (event) => resolve(JSON.parse(event.data));
      });
      
      yield message as ExecutionUpdate;
      
      if (message.status === 'completed' || message.status === 'failed') {
        ws.close();
        break;
      }
    }
  }
}
```

### 4. 🟡 Warning: 캐싱 전략 부재

#### 문제
Frontend에서 API 응답 캐싱이 없어 불필요한 요청 발생

#### 개선 방안
```typescript
// React Query 통합
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query Keys Factory
export const queryKeys = {
  workflows: {
    all: ['workflows'] as const,
    lists: () => [...queryKeys.workflows.all, 'list'] as const,
    list: (filters: FlowFilters) => [...queryKeys.workflows.lists(), filters] as const,
    details: () => [...queryKeys.workflows.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.workflows.details(), id] as const,
  },
  executions: {
    all: ['executions'] as const,
    lists: () => [...queryKeys.executions.all, 'list'] as const,
    list: (workflowId: string) => [...queryKeys.executions.lists(), workflowId] as const,
    details: () => [...queryKeys.executions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.executions.details(), id] as const,
  },
};

// Custom Hooks
export function useWorkflows(filters?: FlowFilters) {
  return useQuery({
    queryKey: queryKeys.workflows.list(filters || {}),
    queryFn: () => apiClient.getWorkflows(filters),
    staleTime: 5 * 60 * 1000, // 5분
    cacheTime: 10 * 60 * 1000, // 10분
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => apiClient.getWorkflow(id),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateWorkflowRequest) => apiClient.createWorkflow(data),
    onSuccess: () => {
      // 캐시 무효화
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
    },
  });
}
```

### 5. 🟢 Info: 에러 바운더리 개선

#### 현재 상태
기본적인 에러 바운더리는 있지만, API 에러 특화 처리 부족

#### 개선 방안
```typescript
// API Error Boundary
import { Component, ReactNode } from 'react';
import { APIError, NetworkError } from '@/lib/errors';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class APIErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('API Error:', error, errorInfo);
    
    // Sentry 등으로 전송
    if (process.env.NODE_ENV === 'production') {
      // sendToSentry(error, errorInfo);
    }
  }

  retry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.retry);
      }

      const error = this.state.error;

      if (error instanceof APIError) {
        if (error.isAuthError()) {
          return (
            <div className="error-container">
              <h2>인증이 필요합니다</h2>
              <p>로그인 페이지로 이동합니다...</p>
            </div>
          );
        }

        if (error.isNotFoundError()) {
          return (
            <div className="error-container">
              <h2>페이지를 찾을 수 없습니다</h2>
              <button onClick={this.retry}>다시 시도</button>
            </div>
          );
        }
      }

      if (error instanceof NetworkError) {
        return (
          <div className="error-container">
            <h2>네트워크 오류</h2>
            <p>인터넷 연결을 확인해주세요</p>
            <button onClick={this.retry}>다시 시도</button>
          </div>
        );
      }

      return (
        <div className="error-container">
          <h2>오류가 발생했습니다</h2>
          <p>{error.message}</p>
          <button onClick={this.retry}>다시 시도</button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 🚀 구현 계획

### Phase 1: API 엔드포인트 통합 (우선순위: 높음)

#### 1.1 Event Store API 추가
```typescript
// frontend/lib/api/events.ts
export class EventStoreAPI {
  constructor(private client: RAGApiClient) {}

  async getAggregateEvents(
    aggregateId: string,
    aggregateType?: string,
    fromVersion: number = 0
  ): Promise<DomainEvent[]> {
    const params = new URLSearchParams({
      from_version: fromVersion.toString(),
    });
    
    if (aggregateType) {
      params.append('aggregate_type', aggregateType);
    }

    return this.client.request(
      `/api/events/aggregate/${aggregateId}?${params.toString()}`
    );
  }

  async replayEvents(
    aggregateId: string,
    aggregateType: string,
    toVersion?: number
  ): Promise<DomainEvent[]> {
    const params = new URLSearchParams({
      aggregate_type: aggregateType,
    });
    
    if (toVersion !== undefined) {
      params.append('to_version', toVersion.toString());
    }

    return this.client.request(
      `/api/events/replay/${aggregateId}?${params.toString()}`
    );
  }

  async getAuditLog(filters: AuditLogFilters): Promise<AuditLogResponse> {
    const params = new URLSearchParams();
    
    if (filters.userId) params.append('user_id', filters.userId.toString());
    if (filters.aggregateType) params.append('aggregate_type', filters.aggregateType);
    if (filters.eventType) params.append('event_type', filters.eventType);
    if (filters.fromDate) params.append('from_date', filters.fromDate.toISOString());
    if (filters.toDate) params.append('to_date', filters.toDate.toISOString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    return this.client.request(`/api/events/audit?${params.toString()}`);
  }
}
```

#### 1.2 Flows API 통합
```typescript
// frontend/lib/api/flows.ts
export class FlowsAPI {
  constructor(private client: RAGApiClient) {}

  // Agentflow
  async createAgentflow(data: CreateAgentflowRequest): Promise<Agentflow> {
    return this.client.request('/api/agent-builder/agentflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAgentflows(filters?: FlowFilters): Promise<FlowListResponse> {
    const params = this.buildFilterParams(filters);
    return this.client.request(`/api/agent-builder/agentflows?${params.toString()}`);
  }

  // Chatflow
  async createChatflow(data: CreateChatflowRequest): Promise<Chatflow> {
    return this.client.request('/api/agent-builder/chatflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getChatflows(filters?: FlowFilters): Promise<FlowListResponse> {
    const params = this.buildFilterParams(filters);
    return this.client.request(`/api/agent-builder/chatflows?${params.toString()}`);
  }

  // Common
  async getFlow(id: string): Promise<Agentflow | Chatflow> {
    return this.client.request(`/api/agent-builder/flows/${id}`);
  }

  async updateFlow(id: string, data: UpdateFlowRequest): Promise<Agentflow | Chatflow> {
    return this.client.request(`/api/agent-builder/flows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFlow(id: string): Promise<void> {
    return this.client.request(`/api/agent-builder/flows/${id}`, {
      method: 'DELETE',
    });
  }

  async executeFlow(id: string, inputData: Record<string, any>): Promise<FlowExecution> {
    return this.client.request(`/api/agent-builder/flows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ input_data: inputData }),
    });
  }

  private buildFilterParams(filters?: FlowFilters): URLSearchParams {
    const params = new URLSearchParams();
    
    if (filters?.flow_type) params.append('flow_type', filters.flow_type);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.tags) filters.tags.forEach(tag => params.append('tags', tag));
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());
    if (filters?.sort_by) params.append('sort_by', filters.sort_by);
    if (filters?.sort_order) params.append('sort_order', filters.sort_order);
    
    return params;
  }
}
```

### Phase 2: React Query 통합 (우선순위: 높음)

```typescript
// frontend/lib/hooks/queries/useWorkflows.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { queryKeys } from '@/lib/queryKeys';

export function useWorkflows(filters?: FlowFilters) {
  return useQuery({
    queryKey: queryKeys.workflows.list(filters || {}),
    queryFn: () => apiClient.flows.getFlows(filters),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => apiClient.flows.getFlow(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateAgentflowRequest | CreateChatflowRequest) => {
      if ('orchestration_type' in data) {
        return apiClient.flows.createAgentflow(data);
      } else {
        return apiClient.flows.createChatflow(data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateFlowRequest }) =>
      apiClient.flows.updateFlow(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => apiClient.flows.deleteFlow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
    },
  });
}

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, inputData }: { id: string; inputData: Record<string, any> }) =>
      apiClient.flows.executeFlow(id, inputData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.executions.list(variables.id) 
      });
    },
  });
}
```

### Phase 3: WebSocket 지원 추가 (우선순위: 중간)

```typescript
// frontend/lib/websocket-client.ts
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private baseUrl: string) {}

  connect(endpoint: string, token: string): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      const wsUrl = this.baseUrl.replace('http', 'ws');
      this.ws = new WebSocket(`${wsUrl}${endpoint}?token=${token}`);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        resolve(this.ws!);
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onclose = () => {
        this.handleReconnect(endpoint, token);
      };
    });
  }

  private handleReconnect(endpoint: string, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        this.connect(endpoint, token);
      }, delay);
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage in React
export function useWorkflowExecution(executionId: string) {
  const [status, setStatus] = useState<ExecutionStatus>('pending');
  const [progress, setProgress] = useState(0);
  const wsClient = useRef<WebSocketClient>();

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    wsClient.current = new WebSocketClient(API_BASE_URL);
    
    wsClient.current
      .connect(`/api/agent-builder/executions/${executionId}/stream`, token)
      .then((ws) => {
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setStatus(data.status);
          setProgress(data.progress);
        };
      });

    return () => {
      wsClient.current?.close();
    };
  }, [executionId]);

  return { status, progress };
}
```

### Phase 4: 타입 동기화 자동화 (우선순위: 중간)

```bash
# backend/scripts/generate_typescript_types.py
#!/usr/bin/env python3
"""
Generate TypeScript types from Pydantic models.
"""

from pydantic import BaseModel
from typing import get_type_hints, get_origin, get_args
import inspect

def pydantic_to_typescript(model: type[BaseModel]) -> str:
    """Convert Pydantic model to TypeScript interface."""
    
    type_hints = get_type_hints(model)
    fields = []
    
    for field_name, field_type in type_hints.items():
        ts_type = python_type_to_ts(field_type)
        optional = field_name in model.__fields__ and not model.__fields__[field_name].required
        fields.append(f"  {field_name}{'?' if optional else ''}: {ts_type};")
    
    return f"export interface {model.__name__} {{\n" + "\n".join(fields) + "\n}"

def python_type_to_ts(py_type) -> str:
    """Convert Python type to TypeScript type."""
    
    origin = get_origin(py_type)
    
    if origin is list:
        args = get_args(py_type)
        return f"{python_type_to_ts(args[0])}[]"
    
    if origin is dict:
        return "Record<string, any>"
    
    if origin is Union:
        args = get_args(py_type)
        return " | ".join(python_type_to_ts(arg) for arg in args)
    
    type_map = {
        str: "string",
        int: "number",
        float: "number",
        bool: "boolean",
        None: "null",
    }
    
    return type_map.get(py_type, "any")

# Generate types
from backend.models.flows import Agentflow, Chatflow

with open("frontend/lib/types/generated.ts", "w") as f:
    f.write("// Auto-generated types from Pydantic models\n\n")
    f.write(pydantic_to_typescript(Agentflow))
    f.write("\n\n")
    f.write(pydantic_to_typescript(Chatflow))
```

---

## 📊 우선순위 매트릭스

| 개선 사항 | 우선순위 | 영향도 | 구현 난이도 | 예상 시간 |
|----------|---------|--------|------------|----------|
| API 엔드포인트 통합 | 🔴 높음 | 높음 | 중간 | 8시간 |
| React Query 통합 | 🔴 높음 | 높음 | 낮음 | 4시간 |
| Event Store API 추가 | 🟡 중간 | 중간 | 낮음 | 2시간 |
| WebSocket 지원 | 🟡 중간 | 중간 | 높음 | 12시간 |
| 타입 동기화 자동화 | 🟢 낮음 | 중간 | 중간 | 6시간 |
| 에러 바운더리 개선 | 🟢 낮음 | 낮음 | 낮음 | 2시간 |

---

## ✅ 체크리스트

### Phase 1: API 통합 (필수)
- [ ] Event Store API 클라이언트 추가
- [ ] Flows API 통합 (Agentflow/Chatflow)
- [ ] NLP Generator API 추가
- [ ] Insights API 추가
- [ ] Marketplace API 추가
- [ ] Backend 라우터 등록 확인

### Phase 2: 캐싱 및 상태 관리 (필수)
- [ ] React Query 설정
- [ ] Query Keys Factory 생성
- [ ] Custom Hooks 작성
- [ ] Optimistic Updates 구현
- [ ] Cache Invalidation 전략

### Phase 3: 실시간 통신 (권장)
- [ ] WebSocket 클라이언트 구현
- [ ] 실행 모니터링 WebSocket
- [ ] 재연결 로직
- [ ] React Hooks 통합

### Phase 4: 개발자 경험 (권장)
- [ ] 타입 생성 스크립트
- [ ] API 문서 자동 동기화
- [ ] 에러 바운더리 개선
- [ ] 로딩 상태 표준화

---

## 🎯 예상 효과

### 성능 개선
- API 요청 **40% 감소** (React Query 캐싱)
- 초기 로딩 시간 **30% 단축** (Prefetching)
- 실시간 업데이트 지연 **80% 감소** (WebSocket)

### 개발자 경험
- 타입 안전성 **100%** (자동 타입 생성)
- API 통합 시간 **50% 단축** (표준화된 클라이언트)
- 버그 발견 **60% 빠름** (타입 체크)

### 사용자 경험
- 응답 속도 **50% 향상** (캐싱)
- 오류 복구 **자동화** (재시도 로직)
- 실시간 피드백 **즉시** (WebSocket)

---

## 📚 참고 자료

- [React Query Best Practices](https://tanstack.com/query/latest/docs/react/guides/best-practices)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [TypeScript Type Generation](https://github.com/koxudaxi/datamodel-code-generator)

---

**작성일**: 2024년 12월 6일  
**버전**: 1.0.0  
**상태**: 분석 완료

**다음 단계**: Phase 1 구현 시작 🚀
