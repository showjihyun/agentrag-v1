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
├── mcp_servers/          # MCP server implementations
├── scripts/              # Utility scripts
├── data/                 # Runtime data (BM25 index, queries)
├── uploads/              # File upload storage
├── logs/                 # Application logs
├── docker-compose.yml    # Docker orchestration
└── .env                  # Root environment config
```

## Backend Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic settings
├── exceptions.py              # Custom exception classes
├── requirements*.txt          # Python dependencies
├── alembic.ini               # Database migration config
│
├── app/                      # Application factory pattern
│   ├── factory.py           # App creation
│   ├── exception_handlers.py # Global exception handlers
│   ├── routers/             # Router registration
│   ├── middleware/          # Custom middleware
│   └── lifecycle/           # Startup/shutdown hooks
│
├── api/                      # API route handlers (organized by domain)
│   ├── auth/                # Authentication domain
│   ├── documents/           # Document management domain
│   ├── conversations/       # Conversation domain
│   ├── query/               # Query processing domain
│   ├── monitoring/          # Monitoring domain
│   ├── admin/               # Administration domain
│   ├── agent_builder/       # Agent Builder feature APIs
│   ├── v1/                  # API version 1
│   └── v2/                  # API version 2
│
├── agents/                   # Multi-agent system
│   ├── aggregator.py        # Master orchestrator (ReAct + CoT)
│   ├── vector_search.py     # Semantic search agent
│   ├── local_data.py        # File system agent
│   ├── web_search.py        # Web search agent
│   └── base.py              # Base agent class
│
├── services/                 # Business logic layer
│   ├── agent_builder/       # Agent Builder DDD service
│   │   ├── domain/          # Domain layer (entities, aggregates)
│   │   ├── application/     # Application services
│   │   ├── infrastructure/  # Infrastructure (repos, handlers)
│   │   └── shared/          # Shared utilities
│   ├── common/              # Common services
│   ├── connectors/          # External connectors
│   ├── document/            # Document processing
│   ├── integrations/        # Third-party integrations
│   ├── rag/                 # RAG-specific services
│   ├── search/              # Search services
│   ├── tools/               # Tool implementations
│   └── triggers/            # Trigger services
│
├── core/                     # Core infrastructure
│   ├── dependencies.py      # Dependency injection
│   ├── cache_manager.py     # Multi-level caching
│   ├── cache_decorators.py  # Cache decorators
│   ├── connection_pool.py   # Redis connection pooling
│   ├── milvus_pool.py       # Milvus connection pooling
│   ├── rate_limiter.py      # Rate limiting
│   ├── health_check.py      # Health monitoring
│   ├── circuit_breaker.py   # Circuit breaker pattern
│   ├── saga.py              # Saga pattern for transactions
│   ├── event_bus.py         # Event-driven architecture
│   ├── tracing.py           # Distributed tracing
│   ├── security/            # Security utilities
│   ├── tools/               # Tool integrations
│   ├── triggers/            # Trigger handlers
│   ├── blocks/              # Block implementations
│   ├── execution/           # Execution engine
│   └── knowledge_base/      # KB utilities
│
├── models/                   # Pydantic models
│   ├── user.py              # User models
│   ├── document.py          # Document models
│   ├── query.py             # Query request/response
│   ├── conversation.py      # Conversation models
│   └── agent_builder/       # Agent builder models
│
├── db/                       # Database layer
│   ├── database.py          # Database connection
│   ├── session.py           # SQLAlchemy session
│   ├── models/              # ORM models
│   └── repositories/        # Data access layer
│
├── middleware/               # Custom middleware
│   └── security.py          # Security headers, CORS
│
├── utils/                    # Utility functions
│
├── tests/                    # Test suite
│   ├── fixtures/            # Reusable test fixtures
│   ├── utils/               # Test utilities
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── performance/         # Performance tests
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
│   ├── providers.tsx        # Global providers
│   ├── auth/                # Authentication pages
│   ├── dashboard/           # Dashboard
│   ├── monitoring/          # Monitoring dashboard
│   ├── agent-builder/       # Agent Builder UI
│   │   ├── agentflows/      # Agent flow management
│   │   ├── chatflows/       # Chat flow management
│   │   ├── workflows/       # Workflow management
│   │   ├── marketplace/     # Template marketplace
│   │   ├── api-keys/        # API key management
│   │   ├── observability/   # Observability dashboard
│   │   └── embed/           # Embed configuration
│   ├── demo/                # Demo pages
│   └── api/                 # API routes
│
├── components/               # React components (organized by domain)
│   ├── index.ts             # Main barrel file
│   ├── ui/                  # Shadcn/ui components
│   ├── chat/                # Chat components
│   ├── documents/           # Document components
│   ├── search/              # Search components
│   ├── feedback/            # Feedback components
│   ├── layout/              # Layout components
│   ├── onboarding/          # Onboarding components
│   ├── forms/               # Form components
│   ├── loading/             # Loading states
│   ├── agent-builder/       # Agent Builder components
│   ├── workflow/            # Workflow components
│   ├── monitoring/          # Monitoring components
│   └── error-boundary/      # Error boundaries
│
├── contexts/                 # React contexts
│   ├── ThemeContext.tsx     # Theme provider
│   └── AuthContext.tsx      # Auth provider
│
├── hooks/                    # Custom React hooks
│   ├── index.ts             # Hook exports
│   ├── queries/             # React Query hooks
│   └── use*.ts              # Individual hooks
│
├── lib/                      # Utilities and configs
│   ├── api-client.ts        # API client
│   ├── errors.ts            # Unified error handling
│   ├── queryClient.ts       # React Query configuration
│   ├── utils.ts             # Helper functions
│   ├── api/                 # API modules
│   ├── types/               # TypeScript types
│   ├── stores/              # Zustand stores
│   ├── hooks/               # Additional hooks
│   ├── performance/         # Performance utilities
│   └── i18n/                # Internationalization
│
├── styles/                   # Global styles
│
├── public/                   # Static assets
│
├── __tests__/                # Jest unit tests
│   ├── utils/               # Test utilities
│   └── [feature]/           # Feature tests
│
├── e2e/                      # Playwright E2E tests
│
├── next.config.ts            # Next.js configuration
├── tailwind.config.ts        # Tailwind configuration
└── package.json              # Dependencies
```

## Key Architectural Patterns

### Backend

**Application Factory Pattern**:
- App created in `app/factory.py`
- Routers registered in `app/routers/`
- Lifecycle hooks in `app/lifecycle/`

**Domain-Driven Design (Agent Builder)**:
- Domain layer: Entities, Value Objects, Aggregates
- Application layer: Commands, Queries, Services
- Infrastructure layer: Repositories, Event handlers

**Layered Architecture**:
1. API Layer (`api/`) - HTTP endpoints
2. Application Layer (`services/*/application/`) - Use cases
3. Domain Layer (`services/*/domain/`) - Business logic
4. Infrastructure Layer (`core/`, `db/`) - Technical concerns

**Event-Driven Architecture**:
- Event bus for decoupled communication
- Saga pattern for distributed transactions
- Event sourcing for audit trails

### Frontend

**Component Organization**:
- Domain-based barrel files for imports
- `components/[domain]/index.ts` for exports

**State Management**:
- Zustand for global state
- TanStack Query for server state with optimized caching
- Query keys factory for consistent cache management

**Performance Optimization**:
- Code splitting with dynamic imports
- Prefetching strategies (hover, visible, idle)
- Virtual lists for large data sets

## Configuration Files

**Backend**:
- `backend/.env` - Environment variables
- `backend/config.py` - Settings with validation
- `backend/alembic.ini` - Migration config

**Frontend**:
- `frontend/.env.local` - Environment variables
- `frontend/next.config.ts` - Next.js config (optimized)
- `frontend/tailwind.config.ts` - Styling config

## Testing

**Backend Tests** (`backend/tests/`):
- `fixtures/` - Reusable fixtures (user, document, query)
- `utils/` - Test utilities (mocks, assertions, API helpers)
- `unit/` - Unit tests
- `integration/` - Integration tests
- `e2e/` - End-to-end tests

**Frontend Tests**:
- `__tests__/utils/` - Test utilities
- `__tests__/[feature]/` - Feature tests
- `e2e/` - Playwright E2E tests

## Documentation

- `docs/REFACTORING_SUMMARY.md` - Recent refactoring changes
- `backend/api/README.md` - API layer documentation
- `backend/tests/README.md` - Test documentation
- `backend/services/agent_builder/DDD_ARCHITECTURE.md` - DDD architecture
