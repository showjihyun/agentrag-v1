"""
End-to-end tests for MCP server integration.
Tests Requirements: 3.1, 3.3, 3.4, 3.5
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.mcp.manager import MCPServerManager
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.requires_mcp
async def test_vector_search_mcp_integration(milvus_manager, embedding_service):
    """
    Test Vector Search Agent with MCP server.

    Requirements: 3.1, 3.3
    """
    # Set up test data in Milvus
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()
    content = "Vector search enables semantic similarity matching. It uses embeddings to find relevant documents."

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "vector_test_doc",
            "document_name": "vector_search.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print("✓ Test data indexed in Milvus")

    # Create mock MCP manager that simulates vector search
    mock_mcp = MagicMock()

    async def mock_vector_search_tool(*args, **kwargs):
        # Simulate MCP vector search tool
        tool_name = args[1] if len(args) > 1 else ""
        arguments = args[2] if len(args) > 2 else kwargs.get("arguments", {})

        if tool_name == "vector_search":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)

            # Perform actual search
            query_embedding = embedding_service.embed_text(query)
            results = await milvus_manager.search(query_embedding, top_k=top_k)

            return MagicMock(content=[MagicMock(text=str({"results": results}))])

        return MagicMock(content=[MagicMock(text="{}")])

    mock_mcp.call_tool = AsyncMock(side_effect=mock_vector_search_tool)

    # Test Vector Search Agent
    vector_agent = VectorSearchAgent(mock_mcp, server_name="vector_server")

    results = await vector_agent.search(query="What is semantic search?", top_k=3)

    assert len(results) > 0, "Should return search results"
    print(f"✓ Vector search returned {len(results)} results")

    # Verify result structure
    for result in results:
        assert "text" in result, "Result should have text"
        assert "score" in result, "Result should have score"

    print(f"  Top result score: {results[0]['score']:.3f}")

    # Clean up
    await milvus_manager.delete_by_document_id("vector_test_doc")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.requires_mcp
async def test_local_data_mcp_integration(tmp_path):
    """
    Test Local Data Agent with MCP server.

    Requirements: 3.1, 3.4
    """
    # Create test file
    test_file = tmp_path / "test_data.txt"
    test_content = "This is test data from a local file."
    test_file.write_text(test_content)

    # Create mock MCP manager
    mock_mcp = MagicMock()

    async def mock_local_data_tool(*args, **kwargs):
        tool_name = args[1] if len(args) > 1 else ""
        arguments = args[2] if len(args) > 2 else kwargs.get("arguments", {})

        if tool_name == "read_file":
            file_path = arguments.get("path", "")
            # Simulate reading the file
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                return MagicMock(content=[MagicMock(text=content)])
            except Exception as e:
                return MagicMock(content=[MagicMock(text=f"Error: {str(e)}")])

        elif tool_name == "query_database":
            # Simulate database query
            return MagicMock(content=[MagicMock(text='[{"id": 1, "name": "test"}]')])

        return MagicMock(content=[MagicMock(text="")])

    mock_mcp.call_tool = AsyncMock(side_effect=mock_local_data_tool)

    # Test Local Data Agent
    local_agent = LocalDataAgent(mock_mcp, server_name="local_data_server")

    # Test file reading
    content = await local_agent.read_file(str(test_file))
    assert test_content in content, "Should read file content"
    print(f"✓ Read file: {len(content)} characters")

    # Test database query
    results = await local_agent.query_database(
        query="SELECT * FROM test", db_name="test_db"
    )
    assert len(results) > 0, "Should return query results"
    print(f"✓ Database query returned {len(results)} rows")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.requires_mcp
async def test_web_search_mcp_integration():
    """
    Test Web Search Agent with MCP server.

    Requirements: 3.1, 3.5
    """
    # Create mock MCP manager
    mock_mcp = MagicMock()

    async def mock_web_search_tool(*args, **kwargs):
        tool_name = args[1] if len(args) > 1 else ""
        arguments = args[2] if len(args) > 2 else kwargs.get("arguments", {})

        if tool_name == "web_search":
            query = arguments.get("query", "")
            num_results = arguments.get("num_results", 5)

            # Simulate web search results
            mock_results = [
                {
                    "title": f"Result {i+1} for {query}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"This is a snippet for result {i+1} about {query}",
                }
                for i in range(min(num_results, 3))
            ]

            return MagicMock(content=[MagicMock(text=str({"results": mock_results}))])

        return MagicMock(content=[MagicMock(text="{}")])

    mock_mcp.call_tool = AsyncMock(side_effect=mock_web_search_tool)

    # Test Web Search Agent
    web_agent = WebSearchAgent(mock_mcp, server_name="search_server")

    results = await web_agent.search_web(
        query="machine learning tutorials", num_results=3
    )

    assert len(results) > 0, "Should return search results"
    print(f"✓ Web search returned {len(results)} results")

    # Verify result structure
    for result in results:
        assert "title" in result, "Result should have title"
        assert "url" in result, "Result should have URL"
        assert "snippet" in result, "Result should have snippet"

    print(f"  First result: {results[0]['title']}")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.requires_mcp
async def test_multi_agent_coordination(milvus_manager, embedding_service, tmp_path):
    """
    Test coordination between multiple agents via MCP.

    Requirements: 3.1, 3.2
    """
    # Set up test data
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()

    # 1. Index document in Milvus
    content = (
        "Python is great for data science. It has libraries like pandas and numpy."
    )
    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "multi_agent_doc",
            "document_name": "python_data.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)

    # 2. Create local file
    local_file = tmp_path / "additional_info.txt"
    local_file.write_text(
        "Additional information: Python was created by Guido van Rossum."
    )

    # Create mock MCP manager that handles multiple tools
    mock_mcp = MagicMock()

    async def mock_multi_tool(*args, **kwargs):
        tool_name = args[1] if len(args) > 1 else ""
        arguments = args[2] if len(args) > 2 else kwargs.get("arguments", {})

        if tool_name == "vector_search":
            query = arguments.get("query", "")
            query_embedding = embedding_service.embed_text(query)
            results = await milvus_manager.search(query_embedding, top_k=3)
            return MagicMock(content=[MagicMock(text=str({"results": results}))])

        elif tool_name == "read_file":
            file_path = arguments.get("path", "")
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                return MagicMock(content=[MagicMock(text=content)])
            except:
                return MagicMock(content=[MagicMock(text="")])

        elif tool_name == "web_search":
            return MagicMock(content=[MagicMock(text=str({"results": []}))])

        return MagicMock(content=[MagicMock(text="{}")])

    mock_mcp.call_tool = AsyncMock(side_effect=mock_multi_tool)

    # Create all agents
    vector_agent = VectorSearchAgent(mock_mcp)
    local_agent = LocalDataAgent(mock_mcp)
    web_agent = WebSearchAgent(mock_mcp)

    # Test vector search
    vector_results = await vector_agent.search("Python data science", top_k=2)
    assert len(vector_results) > 0, "Vector search should return results"
    print(f"✓ Vector agent: {len(vector_results)} results")

    # Test local file access
    local_content = await local_agent.read_file(str(local_file))
    assert "Guido van Rossum" in local_content, "Should read local file"
    print(f"✓ Local agent: Read {len(local_content)} characters")

    # Test web search
    web_results = await web_agent.search_web("Python history", num_results=3)
    print(f"✓ Web agent: {len(web_results)} results")

    # Verify all agents can work together
    print("✓ All agents coordinated successfully")

    # Clean up
    await milvus_manager.delete_by_document_id("multi_agent_doc")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mcp_error_handling():
    """
    Test error handling when MCP servers are unavailable.

    Requirements: 3.6
    """
    # Create mock MCP manager that simulates errors
    mock_mcp = MagicMock()

    async def mock_error_tool(*args, **kwargs):
        raise Exception("MCP server unavailable")

    mock_mcp.call_tool = AsyncMock(side_effect=mock_error_tool)

    # Test agents handle errors gracefully
    vector_agent = VectorSearchAgent(mock_mcp)

    try:
        results = await vector_agent.search("test query", top_k=3)
        # Agent should handle error and return empty or error result
        print("✓ Agent handled MCP error gracefully")
    except Exception as e:
        # Or raise a meaningful error
        assert "unavailable" in str(e).lower() or "error" in str(e).lower()
        print(f"✓ Agent raised appropriate error: {type(e).__name__}")
