# Tool Execution Service

The Tool Execution Service provides a unified interface for executing various tools across different categories. This service is inspired by n8n and Crew.AI, offering a modular and extensible architecture.

## Architecture

```
backend/services/tools/
├── base_executor.py          # Base executor class
├── tool_executor_registry.py # Registry for all executors
├── ai/                        # AI tools (OpenAI, Anthropic)
├── search/                    # Search tools (DuckDuckGo, Google)
├── data/                      # Data tools (Database)
├── developer/                 # Developer tools (HTTP, GitHub)
├── communication/             # Communication tools (Email, Slack)
└── productivity/              # Productivity tools (Calendar, Notion)
```

## Tool Categories

### 1. AI Tools
- **OpenAI**: Chat completions, embeddings
- **Anthropic**: Claude chat completions

### 2. Search Tools
- **DuckDuckGo**: Web search without API key
- **Google**: Custom search with API key

### 3. Data Tools
- **Database**: SQL query execution (PostgreSQL, MySQL, SQLite)

### 4. Developer Tools
- **HTTP**: REST API requests (GET, POST, PUT, DELETE)
- **GitHub**: Repository operations (issues, PRs, repo info)

### 5. Communication Tools
- **Email**: Send emails via SMTP
- **Slack**: Send messages to Slack channels

### 6. Productivity Tools
- **Google Calendar**: Manage calendar events
- **Notion**: Interact with Notion databases and pages

## API Endpoints

### Execute Tool
```http
POST /api/v1/agent-builder/tool-execution/execute
Content-Type: application/json

{
  "tool_name": "openai_chat",
  "parameters": {
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  },
  "config": {
    "api_key": "sk-...",
    "model": "gpt-4"
  }
}
```

Response:
```json
{
  "success": true,
  "result": {
    "content": "Hello! How can I help you?",
    "model": "gpt-4",
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 8,
      "total_tokens": 18
    }
  },
  "execution_time": 1.234
}
```

### Get Available Tools
```http
GET /api/v1/agent-builder/tool-execution/available-tools
```

Response:
```json
{
  "ai": ["openai_chat", "anthropic"],
  "search": ["duckduckgo", "google"],
  "data": ["database"],
  "developer": ["http", "github"],
  "communication": ["email", "slack"],
  "productivity": ["google_calendar", "notion"]
}
```

### Validate Tool Configuration
```http
POST /api/v1/agent-builder/tool-execution/validate
Content-Type: application/json

{
  "tool_name": "github",
  "parameters": {
    "operation": "create_issue",
    "owner": "user",
    "repo": "repo",
    "title": "Bug report"
  },
  "config": {
    "token": "ghp_..."
  }
}
```

Response:
```json
{
  "valid": true,
  "tool_name": "github",
  "message": "Configuration is valid"
}
```

## Usage Examples

### 1. OpenAI Chat
```python
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry

registry = ToolExecutorRegistry()

result = await registry.execute_tool(
    tool_name="openai_chat",
    parameters={
        "messages": [
            {"role": "user", "content": "What is RAG?"}
        ]
    },
    config={
        "api_key": "sk-...",
        "model": "gpt-4",
        "temperature": 0.7
    }
)
```

### 2. GitHub Issue Creation
```python
result = await registry.execute_tool(
    tool_name="github",
    parameters={
        "operation": "create_issue",
        "owner": "myorg",
        "repo": "myrepo",
        "title": "Feature request",
        "body": "Add new feature...",
        "labels": ["enhancement"]
    },
    config={
        "token": "ghp_..."
    }
)
```

### 3. DuckDuckGo Search
```python
result = await registry.execute_tool(
    tool_name="duckduckgo",
    parameters={
        "query": "Python async programming",
        "max_results": 5
    },
    config={}
)
```

### 4. Slack Message
```python
result = await registry.execute_tool(
    tool_name="slack",
    parameters={
        "channel": "#general",
        "text": "Deployment completed successfully!"
    },
    config={
        "webhook_url": "https://hooks.slack.com/..."
    }
)
```

### 5. Notion Page Creation
```python
result = await registry.execute_tool(
    tool_name="notion",
    parameters={
        "operation": "create_page",
        "database_id": "abc123...",
        "properties": {
            "Name": {"title": [{"text": {"content": "New Task"}}]},
            "Status": {"select": {"name": "In Progress"}}
        }
    },
    config={
        "api_key": "secret_..."
    }
)
```

## Adding New Tools

### 1. Create Executor Class
```python
# backend/services/tools/mycategory/mytool_executor.py
from typing import Any, Dict
from backend.services.tools.base_executor import BaseToolExecutor

class MyToolExecutor(BaseToolExecutor):
    def __init__(self):
        super().__init__(
            name="mytool",
            category="mycategory",
            description="My custom tool",
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Implementation
        return {"result": "success"}
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        # Validation logic
        return True
```

### 2. Register in Registry
```python
# backend/services/tools/tool_executor_registry.py
from .mycategory import MyToolExecutor

# Add to executors list in _initialize_executors()
executors = [
    # ...
    MyToolExecutor(),
]
```

### 3. Update __init__.py
```python
# backend/services/tools/mycategory/__init__.py
from .mytool_executor import MyToolExecutor

__all__ = ["MyToolExecutor"]
```

## Error Handling

All executors handle errors gracefully and return structured error responses:

```json
{
  "success": false,
  "error": "API key is invalid",
  "execution_time": 0.123
}
```

Common error types:
- **ValueError**: Invalid parameters or configuration
- **httpx.HTTPError**: HTTP request failures
- **TimeoutError**: Request timeout
- **AuthenticationError**: Invalid credentials

## Best Practices

1. **Configuration Security**: Store API keys and tokens securely (environment variables, secrets manager)
2. **Rate Limiting**: Implement rate limiting for external API calls
3. **Timeout Handling**: Set appropriate timeouts for all HTTP requests
4. **Error Logging**: Log errors with sufficient context for debugging
5. **Parameter Validation**: Validate all parameters before execution
6. **Async Operations**: Use async/await for non-blocking I/O
7. **Resource Cleanup**: Properly close HTTP clients and connections

## Testing

```python
import pytest
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry

@pytest.mark.asyncio
async def test_openai_executor():
    registry = ToolExecutorRegistry()
    
    result = await registry.execute_tool(
        tool_name="openai_chat",
        parameters={
            "messages": [{"role": "user", "content": "Test"}]
        },
        config={
            "api_key": "test-key",
            "model": "gpt-3.5-turbo"
        }
    )
    
    assert result["success"] is True
    assert "content" in result["result"]
```

## Performance Considerations

- **Connection Pooling**: HTTP clients use connection pooling for better performance
- **Caching**: Cache frequently used results (e.g., search results)
- **Parallel Execution**: Execute independent tools in parallel
- **Timeout Configuration**: Set appropriate timeouts based on tool type
- **Resource Limits**: Limit concurrent executions to prevent resource exhaustion

## Future Enhancements

- [ ] Add more tool categories (Finance, Analytics, etc.)
- [ ] Implement tool chaining and workflows
- [ ] Add tool execution history and analytics
- [ ] Support for custom tool plugins
- [ ] Tool marketplace for sharing custom tools
- [ ] Advanced error recovery and retry mechanisms
- [ ] Tool execution monitoring and metrics
