# Project Structure

## Directory Organization

```
.
├── backend/                    # Python FastAPI backend
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Environment configuration
│   ├── api/                   # API endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── documents.py       # Document upload/management
│   │   ├── query.py           # Query processing with streaming
│   │   ├── conversations.py   # Conversation history
│   │   └── users.py           # User management
│   ├── services/              # Core business logic
│   │   ├── embedding.py       # EmbeddingService
│   │   ├── milvus.py          # MilvusManager
│   │   ├── document_processor.py  # DocumentProcessor
│   │   ├── llm_manager.py     # LLMManager with multi-provider support
│   │   ├── hybrid_query_router.py  # Adaptive query routing
│   │   ├── speculative_processor.py  # Speculative RAG
│   │   └── response_coordinator.py  # Response coordination
│   ├── agents/                # Agent implementations
│   │   ├── aggregator.py      # AggregatorAgent (ReAct + CoT)
│   │   ├── vector_search.py   # VectorSearchAgent
│   │   ├── local_data.py      # LocalDataAgent
│   │   └── web_search.py      # WebSearchAgent
│   ├── memory/                # Memory management
│   │   ├── stm.py             # ShortTermMemory (Redis)
│   │   ├── ltm.py             # LongTermMemory (Milvus)
│   │   └── manager.py         # MemoryManager
│   ├── mcp/                   # MCP server integration
│   │   └── manager.py         # MCPServerManager
│   ├── models/                # Pydantic data models
│   │   ├── document.py        # Document, TextChunk
│   │   ├── query.py           # QueryRequest, QueryResponse
│   │   ├── agent.py           # AgentState, AgentStep
│   │   ├── user.py            # User models
│   │   └── conversation.py    # Conversation models
│   ├── db/                    # Database
│   │   ├── database.py        # Database connection
│   │   ├── models.py          # SQLAlchemy models
│   │   └── migrations/        # Alembic migrations
│   └── tests/                 # Backend tests
│       ├── unit/              # Unit tests
│       ├── integration/       # Integration tests
│       └── e2e/               # End-to-end tests
│
├── frontend/                  # Next.js React frontend
│   ├── app/                   # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── login/             # Login page
│   │   ├── register/          # Register page
│   │   ├── dashboard/         # User dashboard
│   │   └── api/               # API routes (if needed)
│   ├── components/            # React components
│   │   ├── DocumentUpload.tsx # File upload component
│   │   ├── ChatInterface.tsx  # Chat UI
│   │   ├── MessageList.tsx    # Message display
│   │   ├── ReasoningSteps.tsx # Agent reasoning display
│   │   ├── SourceCitations.tsx # Source references
│   │   ├── ModeSelector.tsx   # Query mode selector
│   │   ├── SessionNavigation.tsx # Conversation history
│   │   └── auth/              # Authentication components
│   ├── lib/                   # Utilities and services
│   │   ├── api-client.ts      # RAGApiClient
│   │   ├── auth-context.tsx   # Authentication context
│   │   └── types.ts           # TypeScript interfaces
│   ├── public/                # Static assets
│   └── styles/                # Global styles
│
├── mcp_servers/               # MCP server implementations
│   ├── vector_server.py       # Vector search MCP server
│   ├── local_data_server.py   # Local data access MCP server
│   └── search_server.py       # Web search MCP server
│
├── .kiro/                     # Kiro configuration
│   ├── specs/                 # Feature specifications
│   └── steering/              # Project guidance documents
│
├── docker-compose.yml         # Service orchestration
├── .env.example               # Environment template
└── README.md                  # Project documentation
```

## Key Architectural Patterns

### Backend Organization

- **API Layer** (`api/`): FastAPI endpoints with request/response handling
- **Service Layer** (`services/`): Core business logic and external integrations
- **Agent Layer** (`agents/`): Specialized agents with ReAct/CoT reasoning
- **Memory Layer** (`memory/`): STM (Redis) and LTM (Milvus) management
- **Models** (`models/`): Pydantic schemas for type safety and validation
- **Database Layer** (`db/`): SQLAlchemy models and database operations

### Frontend Organization

- **App Router**: Next.js 14+ file-based routing
- **Components**: Reusable React components with TypeScript
- **API Client**: Centralized service for backend communication
- **Streaming**: SSE handling for real-time agent updates
- **Authentication**: Context-based auth state management

### Agent Architecture

The system uses a hierarchical agent structure:

1. **Aggregator Agent**: Master coordinator using LangGraph
   - Implements ReAct (Reasoning + Acting) pattern
   - Uses Chain of Thought for planning
   - Manages memory context (STM + LTM)
   - Orchestrates specialized agents

2. **Specialized Agents**: Domain-specific tools
   - VectorSearchAgent: Milvus similarity search via MCP
   - LocalDataAgent: File system and database access via MCP
   - WebSearchAgent: Web search capabilities via MCP

### Memory System

- **Short-Term Memory (STM)**: Redis-based conversation context with TTL
- **Long-Term Memory (LTM)**: Milvus-based persistent learning and patterns
- **MemoryManager**: Coordinates STM/LTM and handles consolidation

## Naming Conventions

- **Python**: snake_case for functions/variables, PascalCase for classes
- **TypeScript**: camelCase for functions/variables, PascalCase for components/interfaces
- **Files**: Lowercase with hyphens for frontend, snake_case for backend
- **Environment Variables**: UPPER_SNAKE_CASE

## Code Organization Principles

- Keep services focused and single-purpose
- Use dependency injection for testability
- Separate concerns: API, business logic, data access
- Agent nodes should be pure functions operating on state
- Stream responses for better UX with long-running operations
- Follow RESTful API design principles
- Use proper error handling and logging
