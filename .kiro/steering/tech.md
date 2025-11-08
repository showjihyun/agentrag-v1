# Tech Stack

## Backend

**Framework**: FastAPI (Python 3.10+)
- Async/await for non-blocking I/O
- Pydantic for validation and settings management
- Uvicorn ASGI server

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

## Frontend

**Framework**: Next.js 15 (App Router)
- React 19
- TypeScript 5
- Server-Side Rendering (SSR)

**UI/Styling**:
- Tailwind CSS 4
- Shadcn/ui components
- Lucide icons
- Framer Motion for animations

**State Management**:
- Zustand: Global state
- TanStack Query (React Query): Server state and caching
- Context API: Theme, i18n

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
- pytest: Testing framework
- black: Code formatting (120 char line length)
- isort: Import sorting
- mypy: Type checking
- pre-commit: Git hooks

**TypeScript**:
- ESLint: Linting
- Jest: Unit testing
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
docker-compose logs -f
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

### Database

```bash
# PostgreSQL
psql -h localhost -p 5433 -U postgres -d agenticrag

# Redis
redis-cli -h localhost -p 6380
```

## Configuration

**Environment Files**:
- Backend: `backend/.env` (from `.env.example`)
- Frontend: `frontend/.env.local` (from `.env.local.example`)

**Key Settings**:
- `LLM_PROVIDER`: ollama | openai | claude
- `ENABLE_HYBRID_SEARCH`: true (recommended)
- `ENABLE_ADAPTIVE_RERANKING`: true (auto-selects Korean/multilingual models)
- `DEFAULT_QUERY_MODE`: fast | balanced | deep
- `ADAPTIVE_ROUTING_ENABLED`: true (intelligent mode selection)

## Performance Optimization

**Connection Pooling**:
- PostgreSQL: 20 base + 30 overflow connections
- Redis: 50 max connections
- Milvus: 5 connection pool

**Caching Strategy**:
- L1 (Redis): 1 hour TTL
- L2 (Memory): Promoted after 3 hits
- LLM responses: 1 hour cache

**Parallel Processing**:
- Multi-agent execution in Deep mode
- Async document processing
- Background task queue

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
- Target coverage: 85%+

**Frontend**:
- Unit tests: Jest + React Testing Library
- E2E tests: Playwright
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
