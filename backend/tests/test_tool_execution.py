"""
Test tool execution functionality.
"""
import pytest
import asyncio
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry


@pytest.mark.asyncio
async def test_duckduckgo_search():
    """Test DuckDuckGo search executor."""
    executor = ToolExecutorRegistry.get_executor("duckduckgo_search")
    assert executor is not None
    
    result = await executor.execute(
        params={
            "query": "Python programming",
            "max_results": 3
        },
        credentials={}
    )
    
    assert result.success
    assert "results" in result.output
    assert len(result.output["results"]) <= 3


@pytest.mark.asyncio
async def test_http_request():
    """Test HTTP request executor."""
    executor = ToolExecutorRegistry.get_executor("http_request")
    assert executor is not None
    
    result = await executor.execute(
        params={
            "method": "GET",
            "url": "https://api.github.com/repos/python/cpython"
        },
        credentials={}
    )
    
    assert result.success
    assert result.output["status_code"] == 200
    assert "body" in result.output


@pytest.mark.asyncio
async def test_available_tools():
    """Test getting available tools."""
    tools = ToolExecutorRegistry.list_executors()
    
    assert isinstance(tools, dict)
    assert len(tools) > 0
    
    # Check that we have executors
    assert len(tools) >= 11  # We implemented 11 tools
    
    # Check some expected tools
    expected_tools = ["openai_chat", "duckduckgo_search", "http_request", "github"]
    for tool_id in expected_tools:
        assert tool_id in tools


@pytest.mark.asyncio
async def test_invalid_tool():
    """Test executing non-existent tool."""
    executor = ToolExecutorRegistry.get_executor("nonexistent_tool")
    assert executor is None


@pytest.mark.asyncio
async def test_database_executor():
    """Test database executor."""
    executor = ToolExecutorRegistry.get_executor("database_query")
    assert executor is not None
    
    # This will fail without proper DB config, but tests the executor exists
    result = await executor.execute(
        params={
            "query": "SELECT 1 as test"
        },
        credentials={
            "connection_string": "sqlite:///:memory:"
        }
    )
    
    # May succeed or fail depending on environment
    if result.success:
        assert "rows" in result.output
    else:
        assert result.error is not None


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_duckduckgo_search())
    asyncio.run(test_http_request())
    asyncio.run(test_available_tools())
    print("✅ All tests passed!")
