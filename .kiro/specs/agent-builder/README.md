# Agent Builder - Getting Started

This directory contains the complete specification for the Agent Builder feature in AgenticRAG.

## Quick Start

### For Users

If you're looking to use the Agent Builder:

1. **Read the User Guide**: See [docs/agent-builder/user-guide.md](../../../docs/agent-builder/user-guide.md)
2. **Access the UI**: Navigate to `/agent-builder` in the AgenticRAG web interface
3. **Create Your First Agent**: Follow the step-by-step guide in the user documentation

### For Developers

If you're implementing or extending the Agent Builder:

1. **Read the Requirements**: [requirements.md](./requirements.md) - Detailed feature requirements
2. **Review the Design**: [design.md](./design.md) - Architecture and technical design
3. **Check the Tasks**: [tasks.md](./tasks.md) - Implementation task list with progress
4. **Review UI Design**: [ui-design.md](./ui-design.md) - Frontend component specifications

## Documentation Structure

```
.kiro/specs/agent-builder/
├── README.md              # This file - getting started guide
├── requirements.md        # Feature requirements (EARS format)
├── design.md             # Technical design document
├── tasks.md              # Implementation task list
└── ui-design.md          # UI/UX specifications

docs/agent-builder/
└── user-guide.md         # End-user documentation

backend/
├── api/agent_builder/    # FastAPI endpoints
├── services/agent_builder/ # Business logic services
├── db/models/agent_builder.py # Database models
└── tests/                # Tests

frontend/
├── app/agent-builder/    # Next.js pages
├── components/agent-builder/ # React components
└── lib/api/agent-builder.ts # API client
```

## Key Features

The Agent Builder enables users to:

### 1. Create Custom Agents
- Configure LLM providers and models
- Attach tools (vector search, web search, APIs)
- Write custom prompt templates
- Test and iterate quickly

### 2. Build Workflows
- Visual workflow designer with drag-and-drop
- Chain multiple agents together
- Add conditional logic and loops
- Execute in parallel for performance

### 3. Manage Blocks
- Create reusable components
- Share blocks with the community
- Version and test blocks
- Compose blocks into workflows

### 4. Organize Knowledge
- Create domain-specific knowledgebases
- Upload and process documents
- Attach to agents for RAG
- Version and rollback changes

### 5. Configure Variables
- Define variables at multiple scopes
- Store secrets securely
- Use in prompts and configurations
- Override at different levels

### 6. Monitor Executions
- Real-time execution dashboard
- Detailed execution traces
- Performance metrics
- Replay and debug

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15 + React 19)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent Builder│  │   Workflow   │  │  Execution   │          │
│  │      UI      │  │   Designer   │  │   Monitor    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↕ REST API + SSE
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Builder Service Layer                  │  │
│  │  • AgentService  • BlockService  • WorkflowService       │  │
│  │  • KnowledgebaseService  • VariableService               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LangGraph Workflow Execution Engine            │  │
│  │  • StateGraph Compiler  • Node Executor  • Streaming     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (SQLAlchemy ORM)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  PostgreSQL Database                      │  │
│  │  • agents  • workflows  • blocks  • knowledgebases       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Milvus Vector Store + Redis Cache            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Vector DB**: Milvus
- **Cache**: Redis
- **AI Framework**: LangChain + LangGraph
- **LLM**: LiteLLM (supports Ollama, OpenAI, Claude)

### Frontend
- **Framework**: Next.js 15
- **UI Library**: React 19
- **Components**: shadcn/ui
- **Styling**: Tailwind CSS
- **Workflow Designer**: React Flow
- **Code Editor**: Monaco Editor
- **Forms**: react-hook-form + zod

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Milvus 2.3+
- Redis 7+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Implementation Status

See [tasks.md](./tasks.md) for detailed implementation status.

### Completed Phases
- ✅ Phase 1: Database Schema and Core Models
- ✅ Phase 2: Backend Services - Core Infrastructure
- ✅ Phase 3: Workflow Execution Engine
- ✅ Phase 4: Backend API Endpoints
- ✅ Phase 5: Frontend - Agent Builder UI
- ✅ Phase 6: Frontend - Workflow Designer
- ✅ Phase 7: Frontend - Block Library and Knowledgebase Manager
- ✅ Phase 8: Frontend - Execution Monitor and Variables Manager
- ✅ Phase 9: Advanced Features (Scheduling, Hooks, Marketplace, Optimization)
- ✅ Phase 10: Integration and Polish
- ✅ Phase 11: Testing, PWA, Monitoring, and Optimization (80%+ Coverage)

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow Airbnb style guide
- **Commits**: Use conventional commits format

### Testing

- Write unit tests for all services
- Write integration tests for API endpoints
- Write component tests for UI components
- Maintain >80% code coverage

### Pull Requests

1. Create a feature branch
2. Implement changes with tests
3. Update documentation
4. Submit PR with clear description
5. Address review comments

## Support

- **Documentation**: See [docs/agent-builder/](../../../docs/agent-builder/)
- **Issues**: Report bugs on GitHub
- **Discussions**: Join the community forum
- **Email**: support@agenticrag.com

## License

See [LICENSE](../../../LICENSE) file for details.

## Changelog

See [CHANGELOG.md](../../../CHANGELOG.md) for version history.

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
**Status**: Production Ready ✅
