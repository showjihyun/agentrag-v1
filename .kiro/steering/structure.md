# Project Structure

## Root Layout

```
/
├── backend/          # FastAPI backend application
├── frontend/         # Next.js frontend application
├── scripts/          # Utility scripts (setup, docker, maintenance)
├── docs/            # Documentation
├── monitoring/      # Prometheus, Grafana configs
├── docker-compose.yml
└── .env             # Root environment variables
```

## Backend Structure (`backend/`)

### Core Directories

- **`api/`** - FastAPI route handlers organized by feature
  - `agent_builder/` - Agent builder API endpoints (workflows, blocks, executions)
  - `auth.py`, `health.py`, `monitoring.py` - Core API modules
  - Each module is a FastAPI router with related endpoints

- **`agents/`** - AI agent implementations
  - `base.py` - Base agent class
  - `router.py` - Query routing logic
  - `aggregator.py` - Response aggregation
  - `web_search.py`, `vector_search.py`, `local_data.py` - Specialized agents

- **`core/`** - Core business logic and utilities
  - `cache/` - Caching strategies and managers
  - `database/` - Database utilities and connection management
  - `security/` - Authentication, authorization, encryption
  - `monitoring/` - Metrics, logging, tracing
  - `tools/` - Tool integrations for agents

- **`db/`** - Database layer
  - `models/` - SQLAlchemy ORM models
  - `repositories/` - Data access layer (repository pattern)
  - `database.py` - Database session management
  - `migrations/` - Alembic migration files

- **`services/`** - Business logic services
  - `agent_builder/` - Agent builder orchestration services
  - Service layer sits between API and data access

- **`models/`** - Pydantic models for request/response validation
  - `agent_builder.py`, `conversation.py`, `document.py` - Domain models
  - `dto.py` - Data transfer objects
  - `enums.py` - Enumerations

- **`app/`** - Application factory and configuration
  - `factory.py` - FastAPI app creation
  - `middleware/` - Custom middleware
  - `routers/` - Router registration
  - `lifecycle/` - Startup/shutdown handlers

### Other Backend Directories

- **`config/`** - Configuration modules (database, cache, LLM, RAG)
- **`exceptions/`** - Custom exception classes
- **`memory/`** - Short-term and long-term memory implementations
- **`middleware/`** - HTTP middleware (auth, performance, monitoring)
- **`utils/`** - Utility functions
- **`validators/`** - Input validation logic
- **`scripts/`** - Database scripts, migrations, seed data
- **`tests/`** - Pytest test suite

## Frontend Structure (`frontend/`)

### Core Directories

- **`app/`** - Next.js 15 App Router pages
  - Route-based file structure
  - `page.tsx` - Page components
  - `layout.tsx` - Layout components

- **`components/`** - React components
  - `agent-builder/` - Agent builder UI components
  - `ui/` - Reusable UI components (Radix UI + Tailwind)
  - Organized by feature/domain

- **`lib/`** - Utility libraries and helpers
  - API clients, utilities, helpers

- **`hooks/`** - Custom React hooks
  - Reusable stateful logic

- **`contexts/`** - React Context providers
  - Global state management

- **`types/`** - TypeScript type definitions
  - Shared types and interfaces

- **`styles/`** - Global styles and Tailwind config

- **`public/`** - Static assets

## Key Architectural Patterns

### Backend Patterns

1. **Layered Architecture**
   - API Layer (`api/`) → Service Layer (`services/`) → Repository Layer (`db/repositories/`) → Models (`db/models/`)

2. **Dependency Injection**
   - `core/dependencies.py` - FastAPI dependency injection
   - `core/service_factory.py` - Service factory pattern

3. **Repository Pattern**
   - Data access abstracted in `db/repositories/`
   - Separates business logic from data access

4. **Agent Pattern**
   - Base agent class with specialized implementations
   - LangChain/LangGraph integration for orchestration

### Frontend Patterns

1. **Component Composition**
   - Small, reusable components in `components/ui/`
   - Feature-specific components in domain folders

2. **Server/Client Components**
   - Next.js 15 App Router with RSC (React Server Components)
   - Client components marked with `'use client'`

3. **State Management**
   - Zustand for client state
   - TanStack Query for server state

## Configuration Files

- **Backend**: `backend/.env`, `backend/config.py`
- **Frontend**: `frontend/.env.local`, `frontend/next.config.ts`
- **Database**: `backend/alembic.ini`, `backend/alembic/`
- **Docker**: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
- **Code Quality**: `pyproject.toml`, `frontend/eslint.config.mjs`, `frontend/tsconfig.json`

## Import Conventions

### Backend
```python
# Absolute imports from backend root
from backend.api.auth import router
from backend.core.dependencies import get_db
from backend.services.agent_builder import AgentFlowOrchestrator
```

### Frontend
```typescript
// Path aliases configured in tsconfig.json
import { Button } from '@/components/ui/button'
import { useWorkflow } from '@/hooks/use-workflow'
import type { Workflow } from '@/types/workflow'
```

## File Naming Conventions

- **Backend**: `snake_case.py` (Python convention)
- **Frontend**: `kebab-case.tsx` for components, `camelCase.ts` for utilities
- **Tests**: `test_*.py` (backend), `*.test.tsx` (frontend)
