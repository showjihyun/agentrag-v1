# Memory System

Dual-layer memory management for the Agentic RAG system, providing both short-term conversation context and long-term persistent learning.

## Quick Start

```python
from backend.memory import MemoryManager, ShortTermMemory, LongTermMemory
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.config import settings

# Initialize components
stm = ShortTermMemory(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    ttl=settings.STM_TTL
)

milvus = MilvusManager(
    host=settings.MILVUS_HOST,
    port=settings.MILVUS_PORT,
    collection_name=settings.MILVUS_LTM_COLLECTION_NAME,
    embedding_dim=384
)
milvus.connect()
milvus.create_collection()

embedding = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
ltm = LongTermMemory(milvus, embedding)

# Create memory manager
memory = MemoryManager(stm, ltm)

# Use in your application
context = await memory.get_context_for_query(
    session_id="user_123",
    query="What is machine learning?"
)

# After processing
await memory.consolidate_memory(
    session_id="user_123",
    query="What is machine learning?",
    response="Machine learning is...",
    success=True,
    metadata={"source_count": 5}
)
```

## Components

### ShortTermMemory (STM)
Fast, session-based conversation context using Redis.

**Features**:
- Conversation history with TTL
- Working memory for intermediate results
- Automatic session expiration
- Health monitoring

**Usage**:
```python
stm = ShortTermMemory()

# Add messages
stm.add_message("session1", "user", "Hello")
stm.add_message("session1", "assistant", "Hi there!")

# Get history
history = stm.get_conversation_history("session1", limit=10)

# Working memory
stm.store_working_memory("session1", "task", "searching")
task = stm.get_working_memory("session1", "task")

# Cleanup
stm.clear_session("session1")
```

### LongTermMemory (LTM)
Persistent, semantic storage using Milvus vector database.

**Features**:
- Store successful interactions
- Semantic similarity search
- Pattern storage and retrieval
- Success scoring

**Usage**:
```python
ltm = LongTermMemory(milvus_manager, embedding_service)

# Store interaction
interaction_id = await ltm.store_interaction(
    query="What is deep learning?",
    response="Deep learning is...",
    session_id="session1",
    success_score=0.9,
    source_count=5,
    action_count=3
)

# Find similar interactions
similar = await ltm.retrieve_similar_interactions(
    query="Tell me about deep learning",
    top_k=5,
    min_success_score=0.7
)

# Store patterns
pattern_id = await ltm.store_learned_pattern(
    pattern_type="query_strategy",
    pattern_data={"steps": ["search", "analyze", "synthesize"]},
    description="Effective research query strategy",
    success_score=0.95
)
```

### MemoryManager
Unified interface coordinating STM and LTM.

**Features**:
- Combined context retrieval
- Automatic memory consolidation
- Success score calculation
- Pattern management

**Usage**:
```python
manager = MemoryManager(stm, ltm)

# Get combined context
context = await manager.get_context_for_query(
    session_id="session1",
    query="What is AI?",
    include_similar_interactions=True,
    max_similar=3
)

# Access context components
print(f"Recent messages: {len(context.recent_history)}")
print(f"Similar interactions: {len(context.similar_interactions)}")
print(f"Working memory: {context.working_memory}")
print(f"Summary: {context.get_summary()}")

# Consolidate after processing
await manager.consolidate_memory(
    session_id="session1",
    query="What is AI?",
    response="AI is...",
    success=True,
    metadata={
        "source_count": 5,
        "action_count": 3,
        "has_citations": True
    }
)

# Get statistics
stats = manager.get_memory_stats()
```

## Configuration

Set these environment variables in your `.env` file:

```bash
# Redis (STM)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# Milvus (LTM)
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_LTM_COLLECTION_NAME=long_term_memory

# Memory Settings
STM_TTL=3600  # 1 hour in seconds
MAX_CONVERSATION_HISTORY=20
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

```
MemoryManager
├── ShortTermMemory (Redis)
│   ├── Conversation History (TTL-based)
│   └── Working Memory (Key-Value)
└── LongTermMemory (Milvus)
    ├── Interactions (Vector Search)
    └── Patterns (Learned Behaviors)
```

## Testing

### Run Unit Tests
```bash
cd backend
python -m pytest tests/unit/test_stm.py -v
```

### Run Integration Tests
Requires Redis and Milvus running:
```bash
# Start services
docker-compose up -d redis milvus

# Run tests
python -m pytest tests/integration/test_memory_integration.py -v
```

## API Reference

### ShortTermMemory

#### `__init__(host, port, db, password, ttl, max_retries)`
Initialize STM with Redis connection.

#### `add_message(session_id, role, content, metadata=None)`
Add a message to conversation history.

#### `get_conversation_history(session_id, limit=None)`
Retrieve conversation history for a session.

#### `store_working_memory(session_id, key, value)`
Store intermediate results in working memory.

#### `get_working_memory(session_id, key=None)`
Retrieve working memory items.

#### `clear_session(session_id)`
Clear all data for a session.

#### `get_session_info(session_id)`
Get session statistics and metadata.

#### `health_check()`
Check Redis connection health.

### LongTermMemory

#### `__init__(milvus_manager, embedding_service)`
Initialize LTM with Milvus and embedding service.

#### `store_interaction(query, response, session_id, success_score, source_count, action_count, metadata=None)`
Store a successful interaction.

#### `retrieve_similar_interactions(query, top_k, min_success_score)`
Find similar past interactions using vector search.

#### `store_learned_pattern(pattern_type, pattern_data, description, success_score)`
Store a learned behavioral pattern.

#### `retrieve_patterns(pattern_type=None, min_success_score, limit)`
Retrieve learned patterns.

#### `get_stats()`
Get LTM statistics.

### MemoryManager

#### `__init__(stm, ltm, max_history_length, ltm_similarity_threshold)`
Initialize memory manager.

#### `get_context_for_query(session_id, query, include_similar_interactions, max_similar)`
Get combined memory context for a query.

#### `consolidate_memory(session_id, query, response, success, metadata)`
Consolidate memory from STM to LTM.

#### `add_working_memory(session_id, key, value)`
Add to working memory.

#### `get_working_memory(session_id, key=None)`
Retrieve working memory.

#### `clear_session(session_id)`
Clear session data.

#### `get_relevant_patterns(pattern_type=None, limit)`
Get learned patterns from LTM.

#### `store_pattern(pattern_type, pattern_data, description, success_score)`
Store a new pattern.

#### `get_memory_stats()`
Get system-wide memory statistics.

## Performance

### STM (Redis)
- **Latency**: < 5ms per operation
- **Throughput**: 10,000+ ops/sec
- **Memory**: ~1KB per message
- **TTL**: Automatic cleanup

### LTM (Milvus)
- **Search**: 50-100ms
- **Insert**: 10-50ms
- **Memory**: ~1.5KB per interaction
- **Index**: IVF_FLAT with COSINE

### MemoryManager
- **Context Retrieval**: 100-150ms (parallel)
- **Consolidation**: 50-100ms (parallel)

## Error Handling

The memory system is designed for graceful degradation:

- **Redis unavailable**: System continues without STM
- **Milvus unavailable**: System continues without LTM
- **Both unavailable**: System works without memory context

All operations include proper error handling and logging.

## Examples

See `backend/examples/` for complete usage examples:
- `memory_basic.py` - Basic STM and LTM usage
- `memory_manager.py` - MemoryManager integration
- `memory_patterns.py` - Pattern storage and retrieval

## Contributing

When adding new features:
1. Update the relevant class in `stm.py`, `ltm.py`, or `manager.py`
2. Add unit tests in `tests/unit/`
3. Add integration tests in `tests/integration/`
4. Update this README and ARCHITECTURE.md
5. Run all tests to ensure nothing breaks

## License

Part of the Agentic RAG System project.
