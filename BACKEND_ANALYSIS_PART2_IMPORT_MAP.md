# Backend Import Dependency Map & Usage Analysis

## 1. ENTRY POINT DEPENDENCY TREE

### main.py → All Dependencies

```
backend/main.py (1,198 lines)
│
├─ config.py
│  └─ pydantic_settings, pydantic, logging
│
├─ app/factory.py
│  ├─ app/lifecycle/startup.py
│  ├─ app/lifecycle/shutdown.py
│  ├─ app/middleware/__init__.py
│  │  ├─ app/middleware/error_handling.py
│  │  ├─ app/middleware/logging.py
│  │  ├─ app/middleware/rate_limit.py
│  │  ├─ app/middleware/request_id.py
│  │  └─ app/middleware/security.py
│  ├─ app/exception_handlers.py
│  └─ app/routers/__init__.py
│     ├─ api/auth.py
│     ├─ api/conversations.py
│     ├─ api/documents.py
│     ├─ api/query.py
│     ├─ api/tasks.py
│     ├─ api/feedback.py
│     ├─ api/analytics.py
│     ├─ api/health.py
│     ├─ api/monitoring.py
│     ├─ api/web_search.py
│     ├─ api/advanced_rag.py
│     ├─ api/enterprise.py
│     ├─ api/agent_builder/ (60+ routers)
│     ├─ api/v1/health.py
│     ├─ api/v2/workflows.py
│     ├─ api/v2/auth.py
│     └─ ... (80+ total routers)
│
├─ core/dependencies.py (ServiceContainer)
│  ├─ services/embedding.py
│  │  └─ sentence_transformers
│  ├─ services/milvus.py
│  │  └─ pymilvus
│  ├─ services/llm_manager.py
│  │  ├─ litellm
│  │  ├─ langchain
│  │  └─ ollama
│  ├─ services/document_processor.py
│  │  ├─ PyPDF2
│  │  ├─ python-docx
│  │  ├─ python-pptx
│  │  ├─ openpyxl
│  │  └─ docling
│  ├─ memory/manager.py
│  │  ├─ memory/stm.py (Redis-based)
│  │  └─ memory/ltm.py (Milvus-based)
│  ├─ agents/aggregator.py
│  │  ├─ agents/vector_search.py
│  │  ├─ agents/local_data.py
│  │  ├─ agents/web_search.py
│  │  └─ agents/router.py
│  ├─ services/hybrid_search.py
│  ├─ services/search_cache.py
│  ├─ services/query_expansion.py
│  ├─ services/reranker.py
│  ├─ services/speculative_processor.py
│  ├─ services/response_coordinator.py
│  ├─ services/hybrid_query_router.py
│  ├─ services/performance_monitor.py
│  ├─ services/adaptive_rag_service.py
│  ├─ services/intelligent_mode_router.py
│  ├─ core/advanced_cache.py
│  ├─ core/circuit_breaker.py
│  └─ mcp/manager.py (optional)
│
├─ core/connection_pool.py
│  └─ redis.asyncio
│
├─ core/milvus_pool.py
│  └─ pymilvus
│
├─ core/cache_manager.py
│  └─ redis.asyncio
│
├─ core/health_check.py
│  ├─ db/database.py
│  ├─ services/milvus.py
│  └─ redis.asyncio
│
├─ core/tracing.py
│  └─ opentelemetry
│
├─ core/cache_warming.py
│  ├─ redis.asyncio
│  └─ db/database.py
│
├─ core/security/api_key_manager.py
│  └─ cryptography
│
├─ core/tools/init_tools.py
│  └─ core/tools/catalog/ (70+ tools)
│
├─ core/scheduler.py
│  └─ apscheduler
│
├─ db/database.py
│  ├─ sqlalchemy
│  ├─ sqlalchemy.orm
│  └─ db/models/ (18 models)
│
├─ services/sentry_service.py
│  └─ sentry_sdk
│
└─ models/error.py
   └─ pydantic
```

---

## 2. SERVICE LAYER IMPORT DEPENDENCIES

### Core Services Import Graph

```
services/embedding.py
├─ sentence_transformers
├─ torch
├─ numpy
└─ logging

services/milvus.py
├─ pymilvus
├─ numpy
├─ logging
└─ typing

services/llm_manager.py
├─ litellm
├─ langchain
├─ ollama
├─ openai
├─ anthropic
├─ google.generativeai
├─ logging
└─ typing

services/document_processor.py
├─ PyPDF2
├─ python-docx
├─ python-pptx
├─ openpyxl
├─ docling
├─ paddleocr
├─ PIL
├─ logging
└─ typing

services/hybrid_search.py
├─ services/milvus.py
├─ services/embedding.py
├─ services/bm25_search.py
├─ services/reranker.py
├─ logging
└─ typing

services/search_cache.py
├─ redis.asyncio
├─ json
├─ logging
└─ typing

services/query_expansion.py
├─ services/llm_manager.py
├─ services/embedding.py
├─ logging
└─ typing

services/reranker.py
├─ sentence_transformers
├─ numpy
├─ logging
└─ typing

services/speculative_processor.py
├─ services/embedding.py
├─ services/milvus.py
├─ services/llm_manager.py
├─ redis.asyncio
├─ logging
└─ typing

services/response_coordinator.py
├─ logging
└─ typing

services/hybrid_query_router.py
├─ services/speculative_processor.py
├─ agents/aggregator.py
├─ services/response_coordinator.py
├─ logging
└─ typing

services/performance_monitor.py
├─ redis.asyncio
├─ logging
└─ typing

services/adaptive_rag_service.py
├─ services/query_complexity_analyzer.py
├─ services/query_analyzer.py
├─ logging
└─ typing

services/intelligent_mode_router.py
├─ services/adaptive_rag_service.py
├─ config.py
├─ logging
└─ typing
```

### Agent Builder Services Import Graph

```
services/agent_builder/agent_service.py
├─ db/database.py
├─ db/models/agent_builder.py
├─ db/repositories/agent_repository.py
├─ core/event_bus.py
├─ core/cache_manager.py
├─ logging
└─ typing

services/agent_builder/workflow_service.py
├─ db/database.py
├─ db/models/flows.py
├─ db/repositories/workflow_repository.py
├─ core/event_bus.py
├─ logging
└─ typing

services/agent_builder/block_service.py
├─ db/database.py
├─ db/models/agent_builder.py
├─ core/event_bus.py
├─ core/blocks/registry.py
├─ logging
└─ typing

services/agent_builder/workflow_executor.py
├─ core/execution/executor.py
├─ core/blocks/registry.py
├─ core/tools/registry.py
├─ services/agent_builder/tool_executor.py
├─ logging
└─ typing

services/agent_builder/tool_executor.py
├─ core/tools/registry.py
├─ core/tools/base.py
├─ logging
└─ typing

services/agent_builder/multi_agent_orchestrator.py
├─ agents/aggregator.py
├─ agents/vector_search.py
├─ agents/local_data.py
├─ agents/web_search.py
├─ logging
└─ typing

services/agent_builder/knowledge_graph_service.py
├─ services/milvus.py
├─ services/embedding.py
├─ db/database.py
├─ logging
└─ typing

services/agent_builder/knowledgebase_service.py
├─ services/document_processor.py
├─ services/embedding.py
├─ services/milvus.py
├─ db/database.py
├─ logging
└─ typing
```

---

## 3. DATABASE LAYER IMPORT DEPENDENCIES

### Database Models Import Graph

```
db/models/__init__.py
├─ db/models/user.py
├─ db/models/document.py
├─ db/models/conversation.py
├─ db/models/feedback.py
├─ db/models/agent_builder.py
├─ db/models/flows.py
├─ db/models/custom_tools.py
├─ db/models/api_keys.py
├─ db/models/event_store.py
├─ db/models/knowledge_graph.py
├─ db/models/oauth.py
├─ db/models/permission.py
├─ db/models/user_settings.py
├─ db/models/usage.py
├─ db/models/bookmark.py
├─ db/models/notification.py
├─ db/models/conversation_share.py
└─ db/models/tool_models.py

db/models/user.py
├─ sqlalchemy
├─ sqlalchemy.orm
├─ datetime
└─ uuid

db/models/agent_builder.py
├─ sqlalchemy
├─ sqlalchemy.orm
├─ sqlalchemy.dialects.postgresql
├─ datetime
├─ uuid
└─ enum

db/models/flows.py
├─ sqlalchemy
├─ sqlalchemy.orm
├─ sqlalchemy.dialects.postgresql
├─ datetime
├─ uuid
└─ json
```

### Repository Import Graph

```
db/repositories/user_repository.py
├─ sqlalchemy.orm
├─ db/models/user.py
├─ logging
└─ typing

db/repositories/document_repository.py
├─ sqlalchemy.orm
├─ db/models/document.py
├─ logging
└─ typing

db/repositories/agent_repository.py
├─ sqlalchemy.orm
├─ db/models/agent_builder.py
├─ logging
└─ typing

db/repositories/workflow_repository.py
├─ sqlalchemy.orm
├─ db/models/flows.py
├─ logging
└─ typing

db/repositories/feedback_repository.py
├─ sqlalchemy.orm
├─ db/models/feedback.py
├─ logging
└─ typing
```

---

## 4. CORE INFRASTRUCTURE IMPORT DEPENDENCIES

### Caching Layer

```
core/cache_manager.py
├─ redis.asyncio
├─ json
├─ logging
└─ typing

core/advanced_cache.py
├─ redis.asyncio
├─ functools
├─ logging
└─ typing

core/cache_decorators.py
├─ functools
├─ logging
└─ typing

core/cache_warming.py
├─ redis.asyncio
├─ db/database.py
├─ logging
└─ typing

core/multi_level_cache.py
├─ redis.asyncio
├─ logging
└─ typing
```

### Resilience Layer

```
core/circuit_breaker.py
├─ enum
├─ logging
├─ time
└─ typing

core/retry.py
├─ functools
├─ logging
├─ time
└─ typing

core/saga.py
├─ logging
├─ typing
└─ enum

core/resilience.py
├─ core/circuit_breaker.py
├─ core/retry.py
├─ logging
└─ typing
```

### Execution Layer

```
core/execution/executor.py
├─ core/execution/context.py
├─ core/execution/condition_evaluator.py
├─ core/execution/loop_executor.py
├─ core/execution/parallel_executor.py
├─ core/execution/error_handler.py
├─ logging
└─ typing

core/execution/parallel_executor.py
├─ asyncio
├─ logging
└─ typing

core/execution/loop_executor.py
├─ logging
└─ typing

core/execution/condition_evaluator.py
├─ logging
└─ typing
```

### Tools & Triggers

```
core/tools/registry.py
├─ core/tools/base.py
├─ logging
└─ typing

core/tools/init_tools.py
├─ core/tools/registry.py
├─ core/tools/catalog/ (70+ tools)
├─ logging
└─ typing

core/triggers/manager.py
├─ core/triggers/base.py
├─ core/triggers/webhook.py
├─ core/triggers/schedule.py
├─ core/triggers/chat.py
├─ core/triggers/api.py
├─ logging
└─ typing
```

---

## 5. AGENTS IMPORT DEPENDENCIES

### Agent System

```
agents/aggregator.py
├─ agents/vector_search.py
├─ agents/local_data.py
├─ agents/web_search.py
├─ agents/router.py
├─ agents/parallel_executor.py
├─ agents/error_recovery.py
├─ services/llm_manager.py
├─ memory/manager.py
├─ services/observation_processor.py
├─ services/retry_handler.py
├─ services/episodic_memory.py
├─ logging
└─ typing

agents/vector_search.py
├─ services/milvus.py
├─ services/embedding.py
├─ services/hybrid_search.py
├─ services/query_expansion.py
├─ services/reranker.py
├─ services/search_cache.py
├─ logging
└─ typing

agents/local_data.py
├─ services/document_processor.py
├─ services/embedding.py
├─ services/milvus.py
├─ logging
└─ typing

agents/web_search.py
├─ services/web_search_service.py
├─ services/llm_manager.py
├─ logging
└─ typing

agents/router.py
├─ agents/vector_search.py
├─ agents/local_data.py
├─ agents/web_search.py
├─ logging
└─ typing

agents/parallel_executor.py
├─ asyncio
├─ logging
└─ typing
```

---

## 6. IMPORT USAGE STATISTICS

### Most Imported Modules

| Module | Import Count | Used By |
|--------|--------------|---------|
| `logging` | 150+ | All modules |
| `typing` | 140+ | All modules |
| `sqlalchemy` | 80+ | DB layer |
| `redis.asyncio` | 60+ | Cache/session |
| `services/llm_manager.py` | 50+ | Agents, services |
| `services/embedding.py` | 45+ | Search, KB |
| `services/milvus.py` | 40+ | Search, KB |
| `db/database.py` | 35+ | Repositories, services |
| `core/dependencies.py` | 30+ | API endpoints |
| `config.py` | 25+ | All modules |

### Least Imported Modules (Potential Dead Code)

| Module | Import Count | Status |
|--------|--------------|--------|
| `services/emotional/emotional_ai_service.py` | 0 | Unused |
| `services/evolution/workflow_dna_service.py` | 0 | Unused |
| `services/olympics/agent_olympics_manager.py` | 0 | Unused |
| `services/multimodal/` | 1-2 | Rarely used |
| `verify/*.py` | 0 | Test/debug only |

---

## 7. CIRCULAR DEPENDENCY ANALYSIS

### Identified Circular Dependencies

**None Critical** - Architecture prevents circular imports through:

1. **Dependency Injection**: ServiceContainer breaks cycles
2. **Lazy Imports**: Used in some modules
3. **Type Hints**: Forward references used
4. **Module Organization**: Clear layering

### Potential Risk Areas

```
agents/aggregator.py
├─ agents/vector_search.py
├─ agents/local_data.py
├─ agents/web_search.py
└─ services/llm_manager.py
    └─ (no circular back to agents)

services/hybrid_search.py
├─ services/milvus.py
├─ services/embedding.py
├─ services/bm25_search.py
└─ services/reranker.py
    └─ (no circular back)

services/agent_builder/workflow_executor.py
├─ core/execution/executor.py
├─ core/blocks/registry.py
├─ core/tools/registry.py
└─ services/agent_builder/tool_executor.py
    └─ (no circular back)
```

**Mitigation**: All circular dependencies are prevented by design.

---

## 8. IMPORT CHAIN DEPTH ANALYSIS

### Deepest Import Chains

**Chain 1: Query Processing** (8 levels)
```
main.py
└─ core/dependencies.py
   └─ services/hybrid_query_router.py
      └─ services/speculative_processor.py
         └─ services/embedding.py
            └─ sentence_transformers
               └─ torch
                  └─ numpy
```

**Chain 2: Workflow Execution** (7 levels)
```
main.py
└─ api/agent_builder/workflows.py
   └─ services/agent_builder/workflow_service.py
      └─ services/agent_builder/workflow_executor.py
         └─ core/execution/executor.py
            └─ core/blocks/registry.py
               └─ core/tools/registry.py
```

**Chain 3: Document Processing** (6 levels)
```
main.py
└─ core/dependencies.py
   └─ services/document_processor.py
      └─ docling
         └─ PIL
            └─ numpy
```

---

## 9. EXTERNAL DEPENDENCIES

### Critical External Libraries

| Library | Version | Purpose | Import Count |
|---------|---------|---------|--------------|
| `fastapi` | Latest | Web framework | 50+ |
| `sqlalchemy` | 2.0+ | ORM | 80+ |
| `pydantic` | 2.0+ | Validation | 60+ |
| `redis` | Latest | Caching | 60+ |
| `pymilvus` | Latest | Vector DB | 40+ |
| `sentence-transformers` | Latest | Embeddings | 30+ |
| `langchain` | Latest | LLM orchestration | 25+ |
| `litellm` | Latest | LLM interface | 20+ |
| `docling` | Latest | PDF parsing | 15+ |
| `paddleocr` | Latest | OCR | 10+ |

### Optional External Libraries

| Library | Purpose | Status |
|---------|---------|--------|
| `openai` | OpenAI API | Optional |
| `anthropic` | Anthropic API | Optional |
| `google.generativeai` | Google AI | Optional |
| `sentry_sdk` | Error tracking | Optional |
| `opentelemetry` | Distributed tracing | Optional |
| `prometheus_client` | Metrics | Optional |

---

## 10. IMPORT ORGANIZATION RECOMMENDATIONS

### Current Organization ✅

```
backend/
├─ main.py (entry point)
├─ config.py (configuration)
├─ app/ (application factory)
├─ api/ (HTTP endpoints)
├─ services/ (business logic)
├─ agents/ (multi-agent system)
├─ core/ (infrastructure)
├─ db/ (database layer)
├─ models/ (Pydantic models)
├─ memory/ (memory system)
├─ middleware/ (HTTP middleware)
├─ exceptions/ (custom exceptions)
├─ validators/ (input validators)
├─ utils/ (utilities)
└─ tests/ (test suite)
```

### Recommended Improvements

1. **Move verification scripts**:
   ```
   backend/verify/ → backend/tests/verify/
   ```

2. **Consolidate duplicate services**:
   ```
   services/adaptive_rag.py + services/adaptive_rag_service.py
   → Keep only adaptive_rag_service.py
   ```

3. **Organize experimental features**:
   ```
   services/emotional/ → services/experimental/emotional/
   services/evolution/ → services/experimental/evolution/
   services/olympics/ → services/experimental/olympics/
   ```

4. **Centralize tool implementations**:
   ```
   core/tools/catalog/ (already organized well)
   ```

---

## 11. IMPORT BEST PRACTICES COMPLIANCE

### ✅ Followed Best Practices

1. **Relative imports** within packages
2. **Absolute imports** from root
3. **Type hints** for all functions
4. **Lazy imports** where needed
5. **Circular dependency prevention**
6. **Clear module organization**
7. **Dependency injection** pattern
8. **Service locator** pattern (ServiceContainer)

### ⚠️ Areas for Improvement

1. **Unused imports** in some modules
2. **Star imports** in some `__init__.py` files
3. **Long import lists** in some modules
4. **Missing `__all__` exports** in some modules

---

## 12. CONCLUSION

### Import Dependency Summary

- **Total Modules**: 500+
- **Import Depth**: Max 8 levels
- **Circular Dependencies**: None critical
- **External Dependencies**: 50+
- **Critical Path**: Query → Embedding → Milvus → Response

### Health Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Circular Dependencies | ✅ Healthy | None critical |
| Import Organization | ✅ Good | Clear layering |
| Dependency Injection | ✅ Excellent | ServiceContainer pattern |
| External Dependencies | ✅ Managed | Well-documented |
| Code Organization | ✅ Good | DDD for Agent Builder |
| Dead Code | ⚠️ Minor | Some experimental features |

### Recommendations Priority

1. **High**: Consolidate duplicate services
2. **Medium**: Move verification scripts
3. **Medium**: Organize experimental features
4. **Low**: Clean up unused imports
5. **Low**: Add `__all__` exports

The import structure is **well-organized and maintainable** with clear separation of concerns and minimal circular dependencies.
