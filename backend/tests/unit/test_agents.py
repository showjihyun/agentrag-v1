"""
Unit tests for specialized agents.

Tests the VectorSearchAgent, LocalDataAgent, and WebSearchAgent
with mocked MCP server responses.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.agents import VectorSearchAgent, LocalDataAgent, WebSearchAgent
from backend.models.query import SearchResult


class TestVectorSearchAgent:
    """Tests for VectorSearchAgent."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager."""
        manager = MagicMock()
        manager.call_tool = AsyncMock()
        manager.is_connected = MagicMock(return_value=True)
        manager.list_tools = AsyncMock(
            return_value=[{"name": "vector_search", "description": "Search vectors"}]
        )
        return manager

    @pytest.fixture
    def agent(self, mock_mcp_manager):
        """Create a VectorSearchAgent with mocked MCP manager."""
        return VectorSearchAgent(mock_mcp_manager, "test_vector_server")

    @pytest.mark.asyncio
    async def test_search_success(self, agent, mock_mcp_manager):
        """Test successful vector search."""
        # Mock MCP response
        mock_mcp_manager.call_tool.return_value = {
            "results": [
                {
                    "chunk_id": "chunk_1",
                    "document_id": "doc_1",
                    "document_name": "test.pdf",
                    "text": "Machine learning is a subset of AI",
                    "score": 0.95,
                    "metadata": {"page": 1},
                },
                {
                    "chunk_id": "chunk_2",
                    "document_id": "doc_2",
                    "document_name": "research.pdf",
                    "text": "Deep learning uses neural networks",
                    "score": 0.87,
                    "metadata": {"page": 3},
                },
            ]
        }

        # Perform search
        results = await agent.search("machine learning", top_k=10)

        # Verify results
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].chunk_id == "chunk_1"
        assert results[0].score == 0.95
        assert results[0].text == "Machine learning is a subset of AI"

        # Verify MCP call
        mock_mcp_manager.call_tool.assert_called_once_with(
            server_name="test_vector_server",
            tool_name="vector_search",
            arguments={"query": "machine learning", "top_k": 10},
        )

    @pytest.mark.asyncio
    async def test_search_with_filters(self, agent, mock_mcp_manager):
        """Test vector search with filters."""
        mock_mcp_manager.call_tool.return_value = {"results": []}

        filters = {"document_id": "doc_123"}
        await agent.search("test query", top_k=5, filters=filters)

        # Verify filters were passed
        call_args = mock_mcp_manager.call_tool.call_args
        assert call_args[1]["arguments"]["filters"] == filters

    @pytest.mark.asyncio
    async def test_search_empty_query(self, agent):
        """Test search with empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await agent.search("")

    @pytest.mark.asyncio
    async def test_search_invalid_top_k(self, agent):
        """Test search with invalid top_k raises ValueError."""
        with pytest.raises(ValueError, match="top_k must be between"):
            await agent.search("test", top_k=0)

        with pytest.raises(ValueError, match="top_k must be between"):
            await agent.search("test", top_k=101)

    @pytest.mark.asyncio
    async def test_health_check_success(self, agent, mock_mcp_manager):
        """Test successful health check."""
        is_healthy = await agent.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, agent, mock_mcp_manager):
        """Test health check when server not connected."""
        mock_mcp_manager.is_connected.return_value = False

        is_healthy = await agent.health_check()
        assert is_healthy is False


class TestLocalDataAgent:
    """Tests for LocalDataAgent."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager."""
        manager = MagicMock()
        manager.call_tool = AsyncMock()
        manager.is_connected = MagicMock(return_value=True)
        manager.list_tools = AsyncMock(
            return_value=[
                {"name": "read_file", "description": "Read file"},
                {"name": "query_database", "description": "Query DB"},
            ]
        )
        return manager

    @pytest.fixture
    def agent(self, mock_mcp_manager):
        """Create a LocalDataAgent with mocked MCP manager."""
        return LocalDataAgent(mock_mcp_manager, "test_local_server")

    @pytest.mark.asyncio
    async def test_read_file_success(self, agent, mock_mcp_manager):
        """Test successful file reading."""
        file_content = "This is the file content"
        mock_mcp_manager.call_tool.return_value = {"content": file_content}

        result = await agent.read_file("/path/to/file.txt")

        assert result == file_content
        mock_mcp_manager.call_tool.assert_called_once_with(
            server_name="test_local_server",
            tool_name="read_file",
            arguments={"path": "/path/to/file.txt"},
        )

    @pytest.mark.asyncio
    async def test_read_file_empty_path(self, agent):
        """Test read_file with empty path raises ValueError."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            await agent.read_file("")

    @pytest.mark.asyncio
    async def test_query_database_success(self, agent, mock_mcp_manager):
        """Test successful database query."""
        mock_rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_mcp_manager.call_tool.return_value = {"rows": mock_rows}

        results = await agent.query_database("SELECT * FROM users", "test_db")

        assert len(results) == 2
        assert results[0]["name"] == "Alice"

        mock_mcp_manager.call_tool.assert_called_once_with(
            server_name="test_local_server",
            tool_name="query_database",
            arguments={"query": "SELECT * FROM users", "database": "test_db"},
        )

    @pytest.mark.asyncio
    async def test_query_database_empty_query(self, agent):
        """Test query_database with empty query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            await agent.query_database("", "test_db")

    @pytest.mark.asyncio
    async def test_health_check_success(self, agent, mock_mcp_manager):
        """Test successful health check."""
        is_healthy = await agent.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_missing_tools(self, agent, mock_mcp_manager):
        """Test health check when required tools are missing."""
        mock_mcp_manager.list_tools.return_value = [
            {"name": "read_file", "description": "Read file"}
            # Missing query_database tool
        ]

        is_healthy = await agent.health_check()
        assert is_healthy is False


class TestWebSearchAgent:
    """Tests for WebSearchAgent."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager."""
        manager = MagicMock()
        manager.call_tool = AsyncMock()
        manager.is_connected = MagicMock(return_value=True)
        manager.list_tools = AsyncMock(
            return_value=[{"name": "web_search", "description": "Search web"}]
        )
        return manager

    @pytest.fixture
    def agent(self, mock_mcp_manager):
        """Create a WebSearchAgent with mocked MCP manager."""
        return WebSearchAgent(mock_mcp_manager, "test_search_server")

    @pytest.mark.asyncio
    async def test_search_web_success(self, agent, mock_mcp_manager):
        """Test successful web search."""
        mock_mcp_manager.call_tool.return_value = {
            "results": [
                {
                    "title": "Machine Learning Guide",
                    "url": "https://example.com/ml",
                    "snippet": "A comprehensive guide to machine learning",
                    "score": 0.9,
                },
                {
                    "title": "AI Research Paper",
                    "url": "https://example.com/ai",
                    "snippet": "Latest research in artificial intelligence",
                    "score": 0.8,
                },
            ]
        }

        results = await agent.search_web("machine learning", num_results=5)

        assert len(results) == 2
        assert results[0].title == "Machine Learning Guide"
        assert results[0].url == "https://example.com/ml"
        assert results[0].score > 0

        mock_mcp_manager.call_tool.assert_called_once_with(
            server_name="test_search_server",
            tool_name="web_search",
            arguments={"query": "machine learning", "num_results": 5},
        )

    @pytest.mark.asyncio
    async def test_search_web_empty_query(self, agent):
        """Test search_web with empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await agent.search_web("")

    @pytest.mark.asyncio
    async def test_search_web_invalid_num_results(self, agent):
        """Test search_web with invalid num_results raises ValueError."""
        with pytest.raises(ValueError, match="num_results must be between"):
            await agent.search_web("test", num_results=0)

        with pytest.raises(ValueError, match="num_results must be between"):
            await agent.search_web("test", num_results=51)

    @pytest.mark.asyncio
    async def test_search_with_context(self, agent, mock_mcp_manager):
        """Test context-aware search."""
        mock_mcp_manager.call_tool.return_value = {"results": []}

        await agent.search_with_context(
            query="transformers",
            context="Looking for NLP architecture information",
            num_results=3,
        )

        # Verify the query was enhanced with context
        call_args = mock_mcp_manager.call_tool.call_args
        query_arg = call_args[1]["arguments"]["query"]
        assert "transformers" in query_arg
        assert "NLP" in query_arg or "architecture" in query_arg

    @pytest.mark.asyncio
    async def test_format_results_as_text(self, agent, mock_mcp_manager):
        """Test formatting results as text."""
        mock_mcp_manager.call_tool.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "snippet": "Test snippet",
                    "score": 0.95,
                }
            ]
        }

        results = await agent.search_web("test", num_results=1)
        formatted = agent.format_results_as_text(results)

        assert "Test Result" in formatted
        assert "https://example.com" in formatted
        assert "Test snippet" in formatted
        assert "Relevance:" in formatted  # Score may be adjusted by relevance scoring

    @pytest.mark.asyncio
    async def test_health_check_success(self, agent, mock_mcp_manager):
        """Test successful health check."""
        is_healthy = await agent.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_tool_missing(self, agent, mock_mcp_manager):
        """Test health check when web_search tool is missing."""
        mock_mcp_manager.list_tools.return_value = []

        is_healthy = await agent.health_check()
        assert is_healthy is False
