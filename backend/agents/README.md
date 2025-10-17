# Specialized Agents

This directory contains specialized agent implementations that interface with MCP (Model Context Protocol) servers to perform specific tasks.

## Overview

The agent architecture follows a modular design where each agent specializes in a particular domain:

- **VectorSearchAgent**: Semantic search using vector embeddings
- **LocalDataAgent**: Local file system and database access
- **WebSearchAgent**: External web search capabilities

All agents communicate with their respective MCP servers through the `MCPServerManager`.

## Agents

### VectorSearchAgent

**File**: `vector_search.py`

**Purpose**: Performs vector similarity search on the document knowledge base.

**Key Methods**:
- `search(query, top_k, filters)`: Search for similar documents
- `health_check()`: Verify MCP server connectivity

**MCP Server**: `vector_server`
**MCP Tool**: `vector_search`

**Example Usage**:
```python
from backend.agents import VectorSearchAgent
from backend.mcp.manager import MCPServerManager

mcp_manager = MCPServerManager()
await mcp_manager.connect_server(
    "vector_server",
    "python",
    ["mcp_servers/vector_server.py"]
)

agent = VectorSearchAgent(mcp_manager)
results = await agent.search("machine learning", top_k=10)

for result in results:
    print(f"{result.document_name}: {result.text[:100]}...")
    print(f"Score: {result.score}")
```

**Features**:
- Flexible result parsing for different MCP response formats
- Automatic conversion to `SearchResult` objects
- Error handling with retry logic via MCP manager
- Support for metadata filtering

### LocalDataAgent

**File**: `local_data.py`

**Purpose**: Accesses local files and databases through MCP server.

**Key Methods**:
- `read_file(file_path)`: Read local file content
- `query_database(query, db_name)`: Execute SQL queries
- `list_files(directory)`: List files in directory (if supported)
- `health_check()`: Verify MCP server connectivity

**MCP Server**: `local_data_server`
**MCP Tools**: `read_file`, `query_database`

**Example Usage**:
```python
from backend.agents import LocalDataAgent

agent = LocalDataAgent(mcp_manager)

# Read a file
content = await agent.read_file("/path/to/document.txt")
print(content)

# Query a database
rows = await agent.query_database(
    "SELECT * FROM users WHERE active = 1",
    db_name="app_db"
)
for row in rows:
    print(row)
```

**Features**:
- Multiple content format handling
- Database query result parsing
- Path validation and security checks
- Flexible result formatting

### WebSearchAgent

**File**: `web_search.py`

**Purpose**: Performs web searches to retrieve external information.

**Key Methods**:
- `search_web(query, num_results, filters)`: Perform web search
- `search_with_context(query, context, num_results)`: Context-aware search
- `format_results_as_text(results)`: Format results as readable text
- `health_check()`: Verify MCP server connectivity

**MCP Server**: `search_server`
**MCP Tool**: `web_search`

**Example Usage**:
```python
from backend.agents import WebSearchAgent

agent = WebSearchAgent(mcp_manager)

# Basic search
results = await agent.search_web("latest AI research", num_results=5)

for result in results:
    print(f"{result.title}")
    print(f"URL: {result.url}")
    print(f"Snippet: {result.snippet}")
    print(f"Relevance: {result.score:.2f}\n")

# Context-aware search
results = await agent.search_with_context(
    query="transformer architecture",
    context="Looking for information about attention mechanisms in NLP"
)
```

**Features**:
- Relevance scoring based on query term matching
- Result ranking by relevance
- Context-aware search enhancement
- Flexible result formatting
- `WebSearchResult` data class for structured results

## Architecture

### Agent Communication Flow

```
┌─────────────────┐
│ Aggregator      │
│ Agent           │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
         v              v              v              v
┌────────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ VectorSearch   │ │ LocalData  │ │ WebSearch  │ │ Future     │
│ Agent          │ │ Agent      │ │ Agent      │ │ Agents     │
└────────┬───────┘ └─────┬──────┘ └─────┬──────┘ └────────────┘
         │               │              │
         v               v              v
┌────────────────────────────────────────────────┐
│         MCP Server Manager                     │
└────────┬───────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
         v              v              v              v
┌────────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ Vector MCP     │ │ Local Data │ │ Search MCP │ │ Future MCP │
│ Server         │ │ MCP Server │ │ Server     │ │ Servers    │
└────────────────┘ └────────────┘ └────────────┘ └────────────┘
```

### Design Principles

1. **Single Responsibility**: Each agent focuses on one domain
2. **MCP Abstraction**: All external communication goes through MCP servers
3. **Error Resilience**: Graceful degradation when servers are unavailable
4. **Flexible Parsing**: Handle various MCP response formats
5. **Type Safety**: Use Pydantic models for structured data

## Error Handling

All agents implement consistent error handling:

- **ValueError**: For invalid input parameters
- **RuntimeError**: For MCP communication failures
- **Graceful Degradation**: Return empty results rather than crashing

Example:
```python
try:
    results = await agent.search("query")
except ValueError as e:
    # Invalid parameters
    print(f"Invalid input: {e}")
except RuntimeError as e:
    # MCP server failure
    print(f"Server error: {e}")
```

## Health Checks

All agents provide health check methods to verify MCP server connectivity:

```python
# Check if agent's MCP server is healthy
is_healthy = await agent.health_check()

if not is_healthy:
    print("Agent's MCP server is not available")
    # Handle gracefully or reconnect
```

## Integration with Aggregator Agent

These specialized agents are orchestrated by the `AggregatorAgent` (to be implemented in task 10), which:

1. Receives user queries
2. Uses ReAct + CoT reasoning to plan actions
3. Delegates tasks to specialized agents
4. Synthesizes results into comprehensive responses

## Testing

Each agent should be tested with:

1. **Unit Tests**: Mock MCP manager responses
2. **Integration Tests**: Test with actual MCP servers
3. **Error Cases**: Test failure scenarios

Example test structure:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_vector_search_agent():
    # Mock MCP manager
    mcp_manager = MagicMock()
    mcp_manager.call_tool = AsyncMock(return_value={
        "results": [
            {
                "chunk_id": "test_chunk",
                "document_id": "test_doc",
                "document_name": "test.pdf",
                "text": "Test content",
                "score": 0.95
            }
        ]
    })
    
    agent = VectorSearchAgent(mcp_manager)
    results = await agent.search("test query")
    
    assert len(results) == 1
    assert results[0].score == 0.95
```

## Future Enhancements

Potential additions to the agent system:

1. **CodeAnalysisAgent**: Analyze code repositories
2. **ImageAnalysisAgent**: Process and analyze images
3. **DataVisualizationAgent**: Generate charts and graphs
4. **APIIntegrationAgent**: Call external APIs
5. **DocumentGenerationAgent**: Create formatted documents

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 3.3**: Vector Search Agent with MCP integration
- **Requirement 3.4**: Local Data Agent with file and database access
- **Requirement 3.5**: Web Search Agent with external search capabilities
- **Requirement 8.1**: Agent access to multiple tools and strategies

## Next Steps

After implementing these specialized agents, the next task is:

**Task 10**: Implement the Aggregator Agent with ReAct and Chain of Thought reasoning to orchestrate these specialized agents.
