# AgenticBuilder 데이터베이스 스키마

## 개요

AgenticBuilder는 PostgreSQL을 주 데이터베이스로 사용하며, 총 47개의 테이블로 구성된 복잡한 스키마를 가지고 있습니다. 이 문서는 주요 테이블과 관계를 설명합니다.

## 데이터베이스 구조

### 전체 테이블 목록 (47개)

```
핵심 도메인:
├── 사용자 관리 (5개)
│   ├── users
│   ├── organizations
│   ├── teams
│   ├── user_settings
│   └── sessions
│
├── 에이전트 & 워크플로우 (12개)
│   ├── agents
│   ├── agent_versions
│   ├── agent_templates
│   ├── agent_tools
│   ├── agent_knowledgebases
│   ├── agent_executions
│   ├── agent_memories
│   ├── workflows
│   ├── agentflows
│   ├── agentflow_agents
│   ├── agentflow_edges
│   └── blocks
│
├── 실행 & 모니터링 (5개)
│   ├── flow_executions
│   ├── tool_executions
│   ├── query_logs
│   ├── event_store
│   └── feedback
│
├── 지식 베이스 & 문서 (4개)
│   ├── knowledge_bases
│   ├── documents
│   ├── knowledge_graphs
│   └── prompt_templates
│
├── 대화 & 메시지 (5개)
│   ├── conversations
│   ├── messages
│   ├── chatflows
│   ├── bookmarks
│   └── conversation_shares
│
├── 플러그인 시스템 (7개)
│   ├── plugin_registry
│   ├── plugin_configurations
│   ├── plugin_metrics
│   ├── plugin_dependencies
│   ├── plugin_audit_logs
│   ├── plugin_security_scans
│   └── tools
│
├── 마켓플레이스 (3개)
│   ├── marketplace_purchases
│   ├── marketplace_reviews
│   └── marketplace_revenue
│
├── 보안 & 인증 (3개)
│   ├── api_keys
│   ├── rate_limit_configs
│   └── credits
│
└── 시스템 (3개)
    ├── notifications
    ├── migration_history
    └── alembic_version
```

## 핵심 테이블 상세

### 1. 사용자 관리

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    
    -- 사용량 추적
    query_count INTEGER DEFAULT 0,
    storage_used_bytes BIGINT DEFAULT 0,
    
    -- 사용자 설정
    preferences JSONB DEFAULT '{}',
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
```

**주요 필드:**
- `role`: 'user', 'admin', 'enterprise'
- `preferences`: 사용자 설정 (JSON)
- `query_count`: API 사용량 추적
- `storage_used_bytes`: 스토리지 사용량

#### organizations
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id UUID REFERENCES users(id),
    plan VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 에이전트 & 워크플로우

#### agents
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 에이전트 설정
    agent_type VARCHAR(100),
    config JSONB DEFAULT '{}',
    system_prompt TEXT,
    
    -- LLM 설정
    model_provider VARCHAR(100),
    model_name VARCHAR(100),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,
    
    -- 상태
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    
    -- 메타데이터
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**에이전트 타입:**
- `general`: 범용 에이전트
- `control`: 제어 에이전트
- `specialized`: 특화 에이전트 (vector_search, web_search, local_data)

#### agentflows (워크플로우)
```sql
CREATE TABLE agentflows (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 워크플로우 정의
    graph_definition JSONB DEFAULT '{}',
    compiled_graph JSONB,
    
    -- 오케스트레이션 패턴
    orchestration_pattern VARCHAR(100),
    
    -- 설정
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    
    -- 버전 관리
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
```

**orchestration_pattern 값:**
- Sequential, Parallel, Hierarchical, Adaptive
- Consensus, DynamicRouting, SwarmIntelligence
- EventDriven, Reflection, Neuromorphic 등

#### blocks (워크플로우 블록)
```sql
CREATE TABLE blocks (
    id UUID PRIMARY KEY,
    agentflow_id UUID REFERENCES agentflows(id) ON DELETE CASCADE,
    
    -- 블록 정보
    block_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 위치 (UI)
    position_x FLOAT,
    position_y FLOAT,
    
    -- 설정
    config JSONB DEFAULT '{}',
    inputs JSONB DEFAULT '{}',
    outputs JSONB DEFAULT '{}',
    
    -- 연결된 에이전트
    agent_id UUID REFERENCES agents(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**block_type 예시:**
- `agent`: AI 에이전트 블록
- `trigger`: 트리거 (webhook, schedule, event)
- `action`: 액션 (database, api, file)
- `condition`: 조건 분기
- `loop`: 반복
- `transform`: 데이터 변환

#### agentflow_edges (블록 연결)
```sql
CREATE TABLE agentflow_edges (
    id UUID PRIMARY KEY,
    agentflow_id UUID REFERENCES agentflows(id) ON DELETE CASCADE,
    source_block_id UUID REFERENCES blocks(id) ON DELETE CASCADE,
    target_block_id UUID REFERENCES blocks(id) ON DELETE CASCADE,
    
    -- 연결 설정
    source_handle VARCHAR(100),
    target_handle VARCHAR(100),
    config JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 실행 & 모니터링

#### flow_executions
```sql
CREATE TABLE flow_executions (
    id UUID PRIMARY KEY,
    agentflow_id UUID REFERENCES agentflows(id),
    user_id UUID REFERENCES users(id),
    
    -- 실행 정보
    status VARCHAR(50) DEFAULT 'pending',
    trigger_type VARCHAR(100),
    
    -- 입출력
    input_data JSONB,
    output_data JSONB,
    
    -- 성능 메트릭
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    
    -- 에러 정보
    error_message TEXT,
    error_stack TEXT,
    
    -- 타임스탬프
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**status 값:**
- `pending`: 대기 중
- `running`: 실행 중
- `completed`: 완료
- `failed`: 실패
- `cancelled`: 취소됨

#### agent_executions
```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    flow_execution_id UUID REFERENCES flow_executions(id),
    agent_id UUID REFERENCES agents(id),
    block_id UUID REFERENCES blocks(id),
    
    -- 실행 정보
    status VARCHAR(50),
    
    -- 입출력
    input_data JSONB,
    output_data JSONB,
    
    -- LLM 사용량
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    
    -- 성능
    execution_time_ms INTEGER,
    
    -- 에러
    error_message TEXT,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. 지식 베이스 & 문서

#### knowledge_bases
```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 설정
    embedding_model VARCHAR(100),
    chunk_size INTEGER DEFAULT 512,
    chunk_overlap INTEGER DEFAULT 50,
    
    -- 통계
    document_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    knowledge_base_id UUID REFERENCES knowledge_bases(id),
    user_id UUID REFERENCES users(id),
    
    -- 파일 정보
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- 처리 상태
    status VARCHAR(50) DEFAULT 'pending',
    
    -- 메타데이터
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**status 값:**
- `pending`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `failed`: 실패

### 5. 플러그인 시스템

#### plugin_registry
```sql
CREATE TABLE plugin_registry (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- 버전
    version VARCHAR(50) NOT NULL,
    
    -- 플러그인 정보
    category VARCHAR(100),
    author VARCHAR(255),
    repository_url VARCHAR(500),
    
    -- 설정
    config_schema JSONB,
    capabilities JSONB DEFAULT '[]',
    
    -- 상태
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- 통계
    install_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### tools
```sql
CREATE TABLE tools (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- 도구 정보
    category VARCHAR(100),
    tool_type VARCHAR(100),
    
    -- 설정
    config_schema JSONB,
    input_schema JSONB,
    output_schema JSONB,
    
    -- 실행 정보
    execution_mode VARCHAR(50),
    timeout_seconds INTEGER DEFAULT 30,
    
    -- 상태
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 데이터베이스 관계도

```
users
  ├─1:N─> organizations (owner)
  ├─1:N─> agents
  ├─1:N─> agentflows
  ├─1:N─> knowledge_bases
  ├─1:N─> documents
  └─1:N─> flow_executions

agentflows
  ├─1:N─> blocks
  ├─1:N─> agentflow_edges
  └─1:N─> flow_executions

blocks
  ├─N:1─> agents (optional)
  ├─1:N─> agentflow_edges (as source)
  └─1:N─> agentflow_edges (as target)

flow_executions
  └─1:N─> agent_executions

knowledge_bases
  └─1:N─> documents
```

## 인덱스 전략

### 주요 인덱스

```sql
-- 사용자 조회
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 워크플로우 조회
CREATE INDEX idx_agentflows_user ON agentflows(user_id);
CREATE INDEX idx_agentflows_active ON agentflows(is_active);

-- 블록 조회
CREATE INDEX idx_blocks_agentflow ON blocks(agentflow_id);
CREATE INDEX idx_blocks_agent ON blocks(agent_id);

-- 실행 이력
CREATE INDEX idx_flow_executions_agentflow ON flow_executions(agentflow_id);
CREATE INDEX idx_flow_executions_user ON flow_executions(user_id);
CREATE INDEX idx_flow_executions_status ON flow_executions(status);
CREATE INDEX idx_flow_executions_created ON flow_executions(created_at DESC);

-- 문서 조회
CREATE INDEX idx_documents_kb ON documents(knowledge_base_id);
CREATE INDEX idx_documents_status ON documents(status);
```

## 성능 최적화

### Connection Pooling
```python
# SQLAlchemy 설정
pool_size=20
max_overflow=40
pool_pre_ping=True
pool_recycle=3600
```

### Query Optimization
- Eager Loading (JOIN 사용)
- Batch Operations (bulk insert/update)
- Pagination (LIMIT/OFFSET)
- Partial Indexes (조건부 인덱스)

### 파티셔닝 전략
```sql
-- 실행 이력 테이블 파티셔닝 (월별)
CREATE TABLE flow_executions_2026_01 
PARTITION OF flow_executions
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

## 백업 및 복구

### 백업 전략
- **전체 백업**: 매일 자정 (pg_dump)
- **증분 백업**: 매시간 (WAL archiving)
- **보관 기간**: 30일

### 복구 절차
```bash
# 전체 복구
pg_restore -d agenticrag backup.dump

# 특정 시점 복구 (PITR)
pg_restore --target-time="2026-01-20 12:00:00"
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-20
