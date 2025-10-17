# Agentic RAG System - Design Document

## Overview

The Agentic RAG system is a sophisticated document question-answering platform that combines retrieval-augmented generation with multi-agent reasoning. The system uses specialized agents coordinated by an aggregator to provide accurate, contextual responses while maintaining conversation memory and supporting multimodal content.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Chat   │  │ Document │  │   Auth   │  │Dashboard │   │
│  │Interface │  │  Upload  │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │ SSE/REST API
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (Endpoints)                    │  │
│  │  /query  /documents  /auth  /conversations  /users   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │  Query   │  │Document  │  │   LLM    │           │  │
│  │  │ Router   │  │Processor │  │ Manager  │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Layer                              │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │         Aggregator Agent (LangGraph)         │    │  │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐         │    │  │
│  │  │  │ Vector │  │ Local  │  │  Web   │         │    │  │
│  │  │  │ Search │  │  Data  │  │ Search │         │    │  │
│  │  │  └────────┘  └────────┘  └────────┘         │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Memory Layer                             │  │
│  │  ┌──────────┐  ┌──────────┐                          │  │
│  │  │   STM    │  │   LTM    │                          │  │
│  │  │ (Redis)  │  │ (Milvus) │                          │  │
│  │  └──────────┘  └──────────┘                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Milvus  │  │  Redis   │  │PostgreSQL│  │  Ollama  │   │
│  │ (Vector) │  │ (Cache)  │  │   (DB)   │  │  (LLM)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. API Layer

#### Query Endpoint (`/api/query`)
- **Purpose**: Process user queries with streaming responses
- **Input**: QueryRequest (query text, mode, session_id)
- **Output**: SSE stream of QueryResponse chunks
- **Authentication**: Optional (supports guest mode)

#### Documents Endpoint (`/api/documents`)
- **Purpose**: Upload, list, and manage documents
- **Operations**: POST (upload), GET (list), DELETE (remove)
- **Authentication**: Required for upload/delete

#### Authentication Endpoints (`/api/auth`)
- **Purpose**: User registration and login
- **Operations**: POST /register, POST /login, POST /refresh
- **Output**: JWT tokens

### 2. Service Layer

#### HybridQueryRouter
- **Purpose**: Analyze query complexity and route to appropriate mode
- **Modes**: Fast (simple), Balanced (moderate), Deep (complex)
- **Algorithm**: ML-based complexity scoring + pattern matching

#### DocumentProcessor
- **Purpose**: Process uploaded documents
- **Capabilities**:
  - Text extraction (PyPDF2, python-docx)
  - Table extraction (Docling)
  - Image extraction (PIL, ColPali)
  - Semantic chunking
  - Embedding generation

#### LLMManager
- **Purpose**: Unified interface for multiple LLM providers
- **Providers**: Ollama (local), OpenAI, Claude
- **Features**: Streaming, retry logic, fallback handling

### 3. Agent Layer

#### Aggregator Agent (LangGraph)
```python
class AggregatorAgent:
    """Master coordinator using ReAct pattern"""
    
    def process_query(self, query: str, context: dict) -> AsyncIterator[str]:
        # 1. Analyze query (Chain of Thought)
        plan = await self.create_plan(query)
        
        # 2. Execute plan (ReAct loop)
        for step in plan:
            # Reason about next action
            action = await self.reason(step, context)
            
            # Act using specialized agents
            result = await self.act(action)
            
            # Observe and update context
            context = self.observe(result, context)
        
        # 3. Synthesize final response
        response = await self.synthesize(context)
        return response
```

#### Vector Search Agent
- **Purpose**: Query Milvus for relevant document chunks
- **Input**: Query embedding, filters, top_k
- **Output**: Ranked list of document chunks with scores

#### Local Data Agent
- **Purpose**: Access file system and database
- **Capabilities**: File reading, metadata queries, structured data access

#### Web Search Agent
- **Purpose**: Perform web searches when needed
- **Provider**: DuckDuckGo Search API

### 4. Memory Layer

#### Short-Term Memory (Redis)
```python
class ShortTermMemory:
    """Conversation context with TTL"""
    
    def store_message(self, session_id: str, message: dict):
        key = f"session:{session_id}:messages"
        self.redis.lpush(key, json.dumps(message))
        self.redis.expire(key, ttl=3600)  # 1 hour
    
    def get_context(self, session_id: str, limit: int = 10):
        key = f"session:{session_id}:messages"
        messages = self.redis.lrange(key, 0, limit-1)
        return [json.loads(m) for m in messages]
```

#### Long-Term Memory (Milvus)
```python
class LongTermMemory:
    """Persistent learning and patterns"""
    
    def store_pattern(self, pattern: dict):
        embedding = self.embed(pattern['description'])
        self.milvus.insert(
            collection_name="patterns",
            data={
                "embedding": embedding,
                "pattern": pattern,
                "frequency": 1
            }
        )
    
    def retrieve_patterns(self, query: str, top_k: int = 5):
        query_embedding = self.embed(query)
        results = self.milvus.search(
            collection_name="patterns",
            data=[query_embedding],
            limit=top_k
        )
        return results
```

## Data Models

### Document Model
```python
class Document(BaseModel):
    id: str
    user_id: Optional[str]
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    status: str  # "processing", "completed", "failed"
    chunk_count: int
    metadata: dict
```

### Query Model
```python
class QueryRequest(BaseModel):
    query: str
    mode: Optional[str] = "auto"  # "fast", "balanced", "deep", "auto"
    session_id: Optional[str]
    filters: Optional[dict]

class QueryResponse(BaseModel):
    type: str  # "reasoning", "chunk", "source", "complete"
    content: str
    metadata: Optional[dict]
```

### Agent State Model
```python
class AgentState(TypedDict):
    query: str
    plan: List[str]
    context: dict
    retrieved_docs: List[dict]
    reasoning_steps: List[str]
    response: str
```

## Error Handling

### Error Categories
1. **Validation Errors**: Invalid input (400)
2. **Authentication Errors**: Unauthorized access (401)
3. **Authorization Errors**: Forbidden resource (403)
4. **Not Found Errors**: Resource doesn't exist (404)
5. **Processing Errors**: Document processing failed (422)
6. **Service Errors**: External service unavailable (503)
7. **Internal Errors**: Unexpected failures (500)

### Error Response Format
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict]
    timestamp: datetime
```

### Retry Strategy
- **LLM Calls**: Exponential backoff (3 retries)
- **Vector Search**: Immediate retry (2 attempts)
- **Database Operations**: Exponential backoff (3 retries)

## Testing Strategy

### Unit Tests
- Service layer functions
- Agent reasoning logic
- Memory operations
- Utility functions

### Integration Tests
- API endpoints
- Database operations
- Vector search
- LLM integration

### End-to-End Tests
- Complete query flow
- Document upload and processing
- Authentication flow
- Multi-agent coordination

### Performance Tests
- Concurrent user load
- Large document processing
- Query response times
- Memory usage

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Authorization**: Document ownership verification
3. **Input Validation**: Pydantic models for all inputs
4. **SQL Injection**: SQLAlchemy ORM with parameterized queries
5. **XSS Prevention**: Content sanitization
6. **Rate Limiting**: Per-user request limits
7. **Data Encryption**: HTTPS for all communications
8. **Secret Management**: Environment variables for sensitive data

## Performance Optimization

1. **Caching**: Redis for frequent queries
2. **Connection Pooling**: Database and Redis connections
3. **Async Operations**: FastAPI async endpoints
4. **Batch Processing**: Document chunking in batches
5. **Index Optimization**: Milvus IVF_FLAT index
6. **Query Optimization**: Efficient vector search parameters
7. **Resource Limits**: Max file size, chunk limits
8. **Streaming**: SSE for real-time responses
