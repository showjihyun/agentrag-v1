# Technology Stack

## Backend

- **Framework**: FastAPI (Python 3.10+)
- **Agent Orchestration**: LangChain, LangGraph
- **LLM Interface**: LiteLLM (unified interface for Ollama, OpenAI, Claude)
- **Embeddings**: Sentence Transformers
- **Vector Database**: PyMilvus (Milvus 2.3+)
- **Memory/Cache**: Redis 7+
- **File Processing**: Python-multipart, Docling
- **MCP Integration**: MCP SDK for Model Context Protocol servers
- **Database**: PostgreSQL (for user data, sessions, documents metadata)
- **Authentication**: JWT tokens with python-jose

## Frontend

- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React 18+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **API Communication**: Server-Sent Events (SSE) for streaming
- **State Management**: React Context API

## Infrastructure

- **Vector Database**: Milvus (standalone or cluster)
- **Cache/Session Store**: Redis
- **Relational Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Dependencies**: Etcd (for Milvus), MinIO (for Milvus storage)

## LLM Providers

- **Local**: Ollama (no API key required)
- **Cloud**: OpenAI, Claude (API key required)

## Common Commands

### Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Start infrastructure services
docker-compose up -d

# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Start frontend
cd frontend
npm run dev
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild services
docker-compose up -d --build
```

### Ollama Setup

```bash
# Install Ollama (see https://ollama.ai)
# Pull a model
ollama pull llama3.1
ollama pull mistral

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

## Configuration

Environment variables are managed through `.env` files:

- `LLM_PROVIDER`: ollama | openai | claude
- `LLM_MODEL`: Model name (e.g., llama3.1, gpt-4, claude-3-opus)
- `MILVUS_HOST`, `MILVUS_PORT`: Vector database connection
- `REDIS_HOST`, `REDIS_PORT`: Session store connection
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database connection
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: Cloud provider keys (if used)
- `EMBEDDING_MODEL`: Sentence transformer model name
- `JWT_SECRET_KEY`: Secret key for JWT token generation
