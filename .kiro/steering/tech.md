# Technology Stack

## Frontend

- **Framework**: Next.js 15 with React 19 and TypeScript
- **UI Components**: Radix UI, Tailwind CSS, Framer Motion
- **Workflow Visualization**: ReactFlow (drag-and-drop workflow builder)
- **State Management**: Zustand, TanStack Query
- **Real-time**: Server-Sent Events, WebSocket
- **Build Tool**: Next.js built-in (Turbopack)

## Backend

- **Framework**: FastAPI (Python 3.10+) with async/await
- **AI/ML**: LangChain, LangGraph, LiteLLM (multi-provider support)
- **Vector Database**: Milvus with sentence-transformers embeddings
- **Database**: PostgreSQL with SQLAlchemy 2.0, Alembic migrations
- **Cache**: Redis for sessions and result caching
- **Security**: JWT authentication, OAuth2, rate limiting
- **Document Processing**: Docling, PyMuPDF, PaddleOCR, EasyOCR
- **Korean Language**: KoNLPy, Kiwipiepy for Korean text processing

## Infrastructure

- **Containerization**: Docker + Docker Compose
- **Monitoring**: Sentry (error tracking), OpenTelemetry (tracing), Prometheus (metrics)
- **Testing**: Pytest (backend), Jest + Playwright (frontend)

## Common Commands

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Docker Operations

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Database Migrations

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend
pytest
pytest --cov=backend tests/

# Frontend tests
cd frontend
npm test
npm run e2e
```

### Code Quality

```bash
# Backend
black backend/
flake8 backend/
mypy backend/

# Frontend
npm run lint
npm run type-check
```

## Key Configuration Files

- `backend/.env` - Backend environment variables
- `frontend/.env.local` - Frontend environment variables
- `docker-compose.yml` - Docker service definitions
- `backend/alembic.ini` - Database migration config
- `pyproject.toml` - Python project config (Black, isort, mypy)

## Performance Considerations

- Use async/await for all I/O operations
- Connection pooling configured for PostgreSQL, Redis, Milvus
- Redis caching with multi-level cache strategy
- Background task processing for heavy operations
- GPU support for PaddleOCR and embeddings (optional)
