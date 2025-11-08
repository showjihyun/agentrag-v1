# Project Structure

## Repository Layout

```
agenticrag/
├── backend/              # FastAPI backend application
├── frontend/             # Next.js frontend application
├── docs/                 # Documentation
├── examples/             # Sample documents and usage examples
├── monitoring/           # Prometheus/Grafana configs
├── nginx/                # Nginx reverse proxy config
├── data/                 # Runtime data (BM25 index, queries)
├── uploads/              # File upload storage
├── logs/                 # Application logs
├── docker-compose.yml    # Docker orchestration
└── .env                  # Root environment config
```

## Backend Structure

```
backend/
├── main.py                    # FastAPI app entry point, middleware, routers
├── config.py                  # Pydantic settings (env vars, validation)
├── exceptions.py              # Custom exception classes
├── requirements*.txt          # Python dependencies
├── alembic.ini               # Database migration config
│
├── api/                      # API route handlers
│   ├── auth.py              # Authentication endpoints
│   ├── documents.py         # Document upload/management
│   ├── query.py             # Query processing endpoints
│   ├── conversations.py     # Conversation history
│   ├── monitoring.py        # System monitoring
│   ├── web_search.py        # Web search integration
│   ├── health.py            # Health checks
│   └── agent_builder/       # Agent builder UI APIs
│       ├── agents.py
│       ├── blocks.py
│       ├── workflows.py
│       └── ...
│
├── agents/                   # Multi-agent system
│   ├── aggregator.py        # Master orchestrator (ReAct + CoT)
│   ├── vector_search.py     # Semantic search agent
│   ├── local_data.py        # File system agent
│   ├── web_search.py        # Web search agent
│   └── base.py              # Base agent class
│
├── services/                 # Business logic layer
│   ├── embedding.py         # Text embedding service
│   ├── milvus.py            # Vector DB operations
│   ├── llm_manager.py       # LLM provider abstraction
│   ├── document_processor.py # Document parsing
│   ├── hybrid_search.py     # Vector + BM25 search
│   ├── speculative_processor.py # Fast path processing
│   ├── intelligent_router.py # Adaptive query routing
│   ├── memory_manager.py    # STM/LTM management
│   ├── colpali_processor.py # Image/chart understanding
│   ├── web_search_service.py # DuckDuckGo integration
│   └── system_config_service.py # System configuration
│
├── core/                     # Core infrastructure
│   ├── dependencies.py      # Dependency injection
│   ├── connection_pool.py   # Redis connection pooling
│   ├── milvus_pool.py       # Milvus connection pooling
│   ├── cache_manager.py     # L1/L2 caching
│   ├── rate_limiter.py      # Rate limiting
│   ├── health_check.py      # Health monitoring
│   ├── background_tasks.py  # Async task queue
│   ├── structured_logging.py # JSON logging
│   └── tools/               # Tool integrations
│       └── init_tools.py
│
├── models/                   # Pydantic models
│   ├── user.py              # User models
│   ├── document.py          # Document models
│   ├── query.py             # Query request/response
│   ├── conversation.py      # Conversation models
│   ├── error.py             # Error response models
│   └── agent_builder/       # Agent builder models
│
├── db/                       # Database layer
│   ├── session.py           # SQLAlchemy session
│   ├── models.py            # ORM models
│   └── repositories/        # Data access layer
│
├── middleware/               # Custom middleware
│   └── security.py          # Security headers, CORS
│
├── utils/                    # Utility functions
│   ├── file_utils.py        # File operations
│   ├── text_utils.py        # Text processing
│   └── validation.py        # Input validation
│
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Pytest fixtures
│
└── alembic/                  # Database migrations
    └── versions/
```

## Frontend Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   ├── chat/                # Chat interface
│   ├── documents/           # Document management
│   ├── monitoring/          # Monitoring dashboard
│   ├── agent-builder/       # Agent builder UI
│   └── api/                 # API routes (if any)
│
├── components/               # React components
│   ├── ui/                  # Shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── chat/                # Chat-specific components
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   └── StreamingMessage.tsx
│   ├── documents/           # Document components
│   │   ├── DocumentUpload.tsx
│   │   └── DocumentList.tsx
│   └── monitoring/          # Monitoring components
│       └── MetricsChart.tsx
│
├── contexts/                 # React contexts
│   ├── ThemeContext.tsx     # Theme provider
│   └── AuthContext.tsx      # Auth provider
│
├── hooks/                    # Custom React hooks
│   ├── useChat.ts           # Chat functionality
│   ├── useDocuments.ts      # Document operations
│   └── useSSE.ts            # Server-Sent Events
│
├── lib/                      # Utilities and configs
│   ├── api.ts               # API client
│   ├── utils.ts             # Helper functions
│   └── constants.ts         # Constants
│
├── public/                   # Static assets
│   ├── images/
│   └── icons/
│
├── e2e/                      # Playwright E2E tests
│   └── chat.spec.ts
│
├── __tests__/                # Jest unit tests
│   └── components/
│
├── tailwind.config.ts        # Tailwind configuration
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies
```

## Key Architectural Patterns

### Backend

**Dependency Injection**: 
- Services initialized in `core/dependencies.py`
- Singleton pattern for shared resources
- Injected via FastAPI dependencies

**Layered Architecture**:
1. API Layer (`api/`) - HTTP endpoints
2. Service Layer (`services/`) - Business logic
3. Data Layer (`db/repositories/`) - Database access
4. Core Layer (`core/`) - Infrastructure

**Agent System**:
- `AggregatorAgent`: Master coordinator using ReAct loop
- Specialized agents: Vector, Local, Web
- Tool-based architecture with LangChain

**Query Processing Pipeline**:
1. `IntelligentModeRouter` - Analyze complexity
2. Route to Fast/Balanced/Deep mode
3. Execute via `SpeculativeProcessor` or `AggregatorAgent`
4. Stream response via SSE

### Frontend

**Component Organization**:
- `app/` - Pages and layouts (App Router)
- `components/ui/` - Reusable UI primitives
- `components/[feature]/` - Feature-specific components

**State Management**:
- Zustand for global state (theme, user)
- TanStack Query for server state
- Local state with useState/useReducer

**Data Flow**:
1. User action → Hook (e.g., `useChat`)
2. Hook calls API via `lib/api.ts`
3. Response updates TanStack Query cache
4. Components re-render automatically

## Configuration Files

**Backend**:
- `backend/.env` - Environment variables
- `backend/config.py` - Settings with validation
- `backend/alembic.ini` - Migration config
- `backend/pytest.ini` - Test configuration

**Frontend**:
- `frontend/.env.local` - Environment variables
- `frontend/next.config.ts` - Next.js config
- `frontend/tailwind.config.ts` - Styling config
- `frontend/tsconfig.json` - TypeScript config

**Root**:
- `docker-compose.yml` - Service orchestration
- `pyproject.toml` - Python tooling (black, isort, pytest)
- `.gitignore` - Git exclusions
- `.pre-commit-config.yaml` - Git hooks

## Important Conventions

### Naming

**Backend**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

**Frontend**:
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Hooks: `use*.ts`
- Types: `PascalCase` (interfaces/types)

### Import Order

**Python**:
```python
# Standard library
import os
import sys

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from backend.config import settings
from backend.services.embedding import EmbeddingService
```

**TypeScript**:
```typescript
// React/Next
import { useState } from 'react';
import Link from 'next/link';

// Third-party
import { useQuery } from '@tanstack/react-query';

// Local
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
```

### Error Handling

**Backend**: Custom exceptions in `exceptions.py`
```python
from backend.exceptions import APIException

raise APIException(
    status_code=400,
    error_code="INVALID_QUERY",
    message="Query cannot be empty"
)
```

**Frontend**: Error boundaries and try-catch
```typescript
try {
  await api.uploadDocument(file);
} catch (error) {
  toast.error('Upload failed');
}
```

## Testing Locations

**Backend Tests**:
- `backend/tests/unit/` - Unit tests (services, utils)
- `backend/tests/integration/` - Integration tests (API, DB)
- Run: `pytest` from backend directory

**Frontend Tests**:
- `frontend/__tests__/` - Jest unit tests
- `frontend/e2e/` - Playwright E2E tests
- Run: `npm test` or `npm run e2e`

## Documentation

- `README.md` - Project overview and quick start
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/` - Detailed documentation
- `backend/api/` - API endpoint docstrings
- Inline code comments for complex logic
