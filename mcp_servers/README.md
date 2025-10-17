# MCP Servers

This directory contains Model Context Protocol (MCP) servers that provide specialized tools for the Agentic RAG system.

## Available Servers

### 1. Vector Search Server (`vector_server.py`)
Provides vector similarity search capabilities using Milvus.

**Tools:**
- `vector_search`: Search for similar documents using embeddings

**Usage:**
```bash
python -m mcp_servers.vector_server
```

**Configuration:**
- `MILVUS_HOST`: Milvus server host (default: localhost)
- `MILVUS_PORT`: Milvus server port (default: 19530)
- `MILVUS_COLLECTION_NAME`: Collection name (default: documents)
- `EMBEDDING_MODEL`: Sentence transformer model

### 2. Local Data Server (`local_data_server.py`)
Provides secure access to local files and SQLite databases.

**Tools:**
- `read_file`: Read file contents
- `query_database`: Execute SELECT queries on SQLite databases

**Usage:**
```bash
ALLOWED_PATHS=/path/to/data python -m mcp_servers.local_data_server
```

**Configuration:**
- `ALLOWED_PATHS`: Comma-separated list of allowed directories

**Security:**
- Only files within allowed paths can be accessed
- Only SELECT queries are permitted on databases

### 3. Web Search Server (`search_server.py`)
Provides web search capabilities using DuckDuckGo.

**Tools:**
- `web_search`: Search the web and return formatted results

**Usage:**
```bash
MAX_CALLS_PER_MINUTE=10 python -m mcp_servers.search_server
```

**Configuration:**
- `MAX_CALLS_PER_MINUTE`: Rate limit for searches (default: 10)

## Installation

Install required dependencies:
```bash
pip install mcp duckduckgo-search
```

## Integration with MCPServerManager

```python
from backend.mcp.manager import MCPServerManager

# Create manager
manager = MCPServerManager()

# Connect to vector search server
await manager.connect_server(
    server_name="vector_server",
    command="python",
    args=["-m", "mcp_servers.vector_server"]
)

# Use the tool
result = await manager.call_tool(
    "vector_server",
    "vector_search",
    {"query": "machine learning", "top_k": 5}
)
```

## Testing

Run tests:
```bash
# Unit tests
pytest backend/tests/unit/test_mcp_manager.py -v

# Integration tests
pytest backend/tests/integration/test_mcp_servers.py -v -m integration
```

## Architecture

```
┌─────────────────────────────────────┐
│      Specialized Agents              │
│  (Vector, Local Data, Web Search)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      MCPServerManager                │
│  (Connection & Tool Management)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         MCP Servers                  │
│  (Vector, Local Data, Search)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    External Resources                │
│  (Milvus, Files, DuckDuckGo)         │
└─────────────────────────────────────┘
```

## Development

### Adding a New MCP Server

1. Create a new file in `mcp_servers/` (e.g., `my_server.py`)
2. Import MCP SDK:
   ```python
   from mcp.server import Server
   from mcp.server.stdio import stdio_server
   from mcp.types import Tool, TextContent
   ```
3. Define your server class and register tools
4. Implement tool handlers
5. Add to MCPServerManager configuration

### Tool Schema

Tools must define an input schema:
```python
Tool(
    name="my_tool",
    description="What the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
)
```

## Troubleshooting

### MCP SDK Not Found
```bash
pip install mcp
```

### Server Won't Start
- Check that all dependencies are installed
- Verify environment variables are set correctly
- Check logs for specific error messages

### Connection Timeout
- Ensure the server process is running
- Check that the command and args are correct
- Verify network connectivity (for remote servers)

### Tool Execution Fails
- Check tool parameters match the schema
- Verify required resources are available (Milvus, files, etc.)
- Review server logs for detailed error messages

## See Also

- [MCPServerManager Documentation](../backend/mcp/manager.py)
- [Task 8 Summary](../backend/tests/TASK_8_SUMMARY.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
