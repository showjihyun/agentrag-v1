# Tech Stack

## Backend

**Framework**: FastAPI (Python 3.10+)
- Async/await for non-blocking I/O
- Pydantic v2 for validation and settings management
- Uvicorn ASGI server
- Application factory pattern

**AI/ML Stack**:
- LangChain/LangGraph: Agent orchestration and workflows
- LiteLLM: Unified interface for multiple LLM providers
- Sentence Transformers: Text embeddings (jhgan/ko-sroberta-multitask for Korean)
- PaddleOCR Advanced: Document processing (PP-OCRv5, PP-StructureV3, PaddleOCR-VL)
- Docling: PDF/DOCX parsing with table extraction

**Databases**:
- PostgreSQL: User data, documents, metadata, conversations
- Milvus: Vector storage for embeddings
- Redis: L1/L2 caching, sessions, rate limiting

**Key Libraries**:
- rank-bm25: Keyword search
- konlpy: Korean NLP
- PyMuPDF, python-docx, python-pptx: Document parsing
- httpx: Async HTTP client
- ddgs: DuckDuckGo search

**Architecture Patterns**:
- Domain-Driven Design (DDD) for Agent Builder
- Event-driven architecture with event bus
- Saga pattern for distributed transactions
- Circuit breaker for resilience
- Multi-level caching (L1 memory, L2 Redis)

## Frontend

**Framework**: Next.js 15 (App Router)
- React 19
- TypeScript 5
- Server-Side Rendering (SSR)

**UI/Styling**:
- Tailwind CSS 4
- Shadcn/ui components
- Lucide icons (modular imports)
- Framer Motion for animations

**State Management**:
- Zustand: Global state
- TanStack Query (React Query): Server state with optimized caching
- Context API: Theme, i18n

**Performance**:
- Code splitting with dynamic imports
- Prefetching strategies (hover, visible, idle)
- Virtual lists for large data sets
- Optimized bundle with tree-shaking

**Real-time**:
- Server-Sent Events (SSE): Streaming responses
- EventSource API

## Infrastructure

**Containerization**: Docker & Docker Compose
- Backend service
- PostgreSQL (port 5433)
- Milvus + etcd + MinIO (ports 19530, 9002-9003)
- Redis (port 6380)

**LLM Runtime**: Ollama (optional, for local models)
- Llama 3.1, Mistral, etc.
- Port 11434

## Development Tools

**Python**:
- pytest: Testing framework with fixtures
- black: Code formatting (120 char line length)
- isort: Import sorting
- mypy: Type checking
- pre-commit: Git hooks

**TypeScript**:
- ESLint: Linting
- Jest: Unit testing with custom utilities
- Playwright: E2E testing
- React Testing Library

## Common Commands

### Backend

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run tests
pytest
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest --cov=backend --cov-report=html

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Format code
black .
isort .
```

### Frontend

```bash
# Setup
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm start

# Run tests
npm test
npm run e2e
npm run e2e:ui
```

### Docker

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres milvus redis

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

## Configuration

**Environment Files**:
- Backend: `backend/.env` (from `.env.example`)
- Frontend: `frontend/.env.local` (from `.env.local.example`)

**Key Settings**:
- `LLM_PROVIDER`: ollama | openai | claude
- `ENABLE_HYBRID_SEARCH`: true (recommended)
- `ENABLE_ADAPTIVE_RERANKING`: true
- `DEFAULT_QUERY_MODE`: fast | balanced | deep
- `ADAPTIVE_ROUTING_ENABLED`: true

## Performance Optimization

**Backend Caching**:
- L1 (Memory): LRU cache with TTL
- L2 (Redis): Shared cache across instances
- Cache decorators: `@cached_short`, `@cached_medium`, `@cached_long`
- Query result caching with automatic invalidation

**Frontend Caching**:
- React Query with stale/cache time presets
- Query keys factory for consistent cache management
- Prefetch helpers for route transitions

**Connection Pooling**:
- PostgreSQL: 20 base + 30 overflow connections
- Redis: 50 max connections
- Milvus: 5 connection pool

## Code Style

**Python**:
- PEP 8 compliant
- Type hints required
- Docstrings for public functions
- 120 character line length
- snake_case naming

**TypeScript**:
- Strict mode enabled
- Functional components with hooks
- 100 character line length
- PascalCase for components, camelCase for utilities

## Testing Strategy

**Backend**:
- Unit tests: `backend/tests/unit/`
- Integration tests: `backend/tests/integration/`
- Fixtures: `backend/tests/fixtures/`
- Utilities: `backend/tests/utils/`
- Target coverage: 85%+

**Frontend**:
- Unit tests: `frontend/__tests__/`
- E2E tests: `frontend/e2e/`
- Test utilities: `frontend/__tests__/utils/`
- Target coverage: 80%+

## Deployment

**Production Checklist**:
- Set `DEBUG=false`
- Configure CORS origins
- Set strong `JWT_SECRET_KEY`
- Enable HTTPS
- Configure rate limiting
- Set up monitoring (Prometheus/Grafana)
- Configure backup strategy
