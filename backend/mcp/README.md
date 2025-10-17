# MCP Integration Module

This module provides integration with Model Context Protocol (MCP) servers for the Agentic RAG system.

## Overview

The MCP integration enables the system to communicate with specialized tool servers that provide:
- Vector similarity search
- Local file and database access
- Web search capabilities
- Future extensibility for additional tools

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Aggregator Agent                            │
│         (Coordinates all agents)                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────────┐
        │            │            │                │
        ▼            ▼            ▼                ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Vector  │  │  Local   │  │   Web    │  │  Future  │
│  Search  │  │   Data   │  │  Search  │  │  Agents  │
│  Agent   │  │  Agent   │  │  Agent   │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘
     │             │             │
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  MCPServerManager    │
        │  (This Module)       │
        └──────────┬───────────┘
                   │
        ┌──────────┼──────────┬────────────────┐
        │          │          │                │
        ▼          ▼          ▼                ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Vector  │ │  Local   │ │  Search  │ │  Custom  │
│  Server  │ │   Data   │ │  Server  │ │  Servers │
│   MCP    │ │  Server  │ │   MCP    │ │          │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## Components

### MCPServerManager (`manager.py`)

The central manager for all MCP server connections and tool executions.

**Key Features:**
- Stdio-based transport for server communication
- Connection lifecycle management
- Tool discovery and execution
- Automatic reconnection on failures
- Support for multiple simultaneous servers

**Basic Usage:**
```python
from backend.mcp.manager import MCPServerManager

# Create manager
manager = MCPServerManager()

# Connect to a server
await manager.connect_server(
    server_name="my_server",
    command="python",
    args=["-m", "mcp_servers.vector_server"]
)

# List available tools
tools = await manager.list_tools("my_server")

# Call a tool
result = await manager.call_tool(
    "my_server",
    "tool_name",
    {"param": "value"}
)

# Disconnect
await manager.disconnect_server("my_server")
```

## Available MCP Servers

### 1. Vector Search Server
**Location:** `mcp_servers/vector_server.py`

**Purpose:** Provides vector similarity search using Milvus

**Tools:**
- `vector_search`: Search for similar documents

**Example:**
```python
await manager.connect_server(
    "vector_server",
    "python",
    ["-m", "mcp_servers.vector_server"]
)

result = await manager.call_tool(
    "vector_server",
    "vector_search",
    {
        "query": "What is machine learning?",
        "top_k": 10,
        "filters": None
    }
)
```

### 2. Local Data Server
**Location:** `mcp_servers/local_data_server.py`

**Purpose:** Secure access to local files and SQLite databases

**Tools:**
- `read_file`: Read file contents
- `query_database`: Execute SELECT queries

**Example:**
```python
await manager.connect_server(
    "local_data",
    "python",
    ["-m", "mcp_servers.local_data_server"],
    env={"ALLOWED_PATHS": "/path/to/data"}
)

# Read file
file_result = await manager.call_tool(
    "local_data",
    "read_file",
    {"path": "/path/to/data/file.txt"}
)

# Query database
db_result = await manager.call_tool(
    "local_data",
    "query_database",
    {
        "database": "/path/to/data/db.sqlite",
        "query": "SELECT * FROM users"
    }
)
```

### 3. Web Search Server
**Location:** `mcp_servers/search_server.py`

**Purpose:** Web search using DuckDuckGo

**Tools:**
- `web_search`: Search the web

**Example:**
```python
await manager.connect_server(
    "search",
    "python",
    ["-m", "mcp_servers.search_server"]
)

result = await manager.call_tool(
    "search",
    "web_search",
    {
        "query": "latest AI developments",
        "num_results": 5
    }
)
```

## Integration with Agents

### Specialized Agents

Each specialized agent uses the MCPServerManager to access its corresponding MCP server:

```python
class VectorSearchAgent:
    def __init__(self, mcp_manager: MCPServerManager):
        self.mcp = mcp_manager
        self.server_name = "vector_server"
    
    async def search(self, query: str, top_k: int = 10):
        return await self.mcp.call_tool(
            self.server_name,
            "vector_search",
            {"query": query, "top_k": top_k}
        )
```

### Aggregator Agent

The Aggregator Agent coordinates all specialized agents:

```python
class AggregatorAgent:
    def __init__(
        self,
        mcp_manager: MCPServerManager,
        vector_agent: VectorSearchAgent,
        local_agent: LocalDataAgent,
        search_agent: WebSearchAgent
    ):
        self.mcp = mcp_manager
        self.vector_agent = vector_agent
        self.local_agent = local_agent
        self.search_agent = search_agent
    
    async def process_query(self, query: str):
        # Use agents to gather information
        vector_results = await self.vector_agent.search(query)
        # ... coordinate other agents as needed
```

## Error Handling

The MCPServerManager provides robust error handling:

```python
try:
    result = await manager.call_tool(
        "server_name",
        "tool_name",
        {"param": "value"},
        retry_on_failure=True  # Automatic reconnection
    )
except ValueError as e:
    # Server not connected or invalid parameters
    print(f"Configuration error: {e}")
except RuntimeError as e:
    # Tool execution failed
    print(f"Execution error: {e}")
```

## Testing

### Unit Tests
```bash
pytest backend/tests/unit/test_mcp_manager.py -v
```

### Integration Tests
```bash
pytest backend/tests/integration/test_mcp_servers.py -v -m integration
```

### Manual Testing
```bash
python backend/tests/manual_mcp_test.py
```

## Configuration

### Environment Variables

**Vector Server:**
- `MILVUS_HOST`: Milvus host (default: localhost)
- `MILVUS_PORT`: Milvus port (default: 19530)
- `MILVUS_COLLECTION_NAME`: Collection name
- `EMBEDDING_MODEL`: Sentence transformer model

**Local Data Server:**
- `ALLOWED_PATHS`: Comma-separated allowed directories

**Search Server:**
- `MAX_CALLS_PER_MINUTE`: Rate limit (default: 10)

## Security Considerations

### Local Data Server
- ✅ Path validation prevents directory traversal
- ✅ Only SELECT queries allowed on databases
- ✅ Configurable allowed paths
- ✅ File type validation

### Web Search Server
- ✅ Rate limiting prevents abuse
- ✅ Result count limits
- ✅ No API key exposure

### Vector Search Server
- ✅ Uses existing Milvus security
- ✅ No direct database access

## Extending with Custom Servers

To add a new MCP server:

1. Create server file in `mcp_servers/`:
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

class MyCustomServer:
    def __init__(self):
        self.server = Server("my-custom-server")
        self._register_tools()
    
    def _register_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="my_tool",
                    description="What my tool does",
                    inputSchema={...}
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name, arguments):
            if name == "my_tool":
                return await self._handle_my_tool(arguments)
    
    async def run(self):
        async with stdio_server() as (read, write):
            await self.server.run(read, write, ...)
```

2. Connect via MCPServerManager:
```python
await manager.connect_server(
    "my_custom",
    "python",
    ["-m", "mcp_servers.my_custom_server"]
)
```

3. Create specialized agent:
```python
class MyCustomAgent:
    def __init__(self, mcp_manager):
        self.mcp = mcp_manager
    
    async def do_something(self, params):
        return await self.mcp.call_tool(
            "my_custom",
            "my_tool",
            params
        )
```

## Dependencies

```bash
pip install mcp                    # MCP SDK
pip install duckduckgo-search      # For web search server
```

## See Also

- [MCP Servers README](../../mcp_servers/README.md)
- [Task 8 Summary](../tests/TASK_8_SUMMARY.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Integration Tests](../tests/integration/test_mcp_servers.py)
