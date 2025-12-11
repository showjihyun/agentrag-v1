"""Mock object creation utilities."""

from unittest.mock import MagicMock, AsyncMock
from typing import Any, Dict, List, Optional


def create_mock_llm_response(
    content: str = "This is a mock response.",
    model: str = "gpt-4",
    tokens: int = 100,
) -> Dict[str, Any]:
    """Create a mock LLM response."""
    return {
        "content": content,
        "model": model,
        "usage": {
            "prompt_tokens": tokens // 2,
            "completion_tokens": tokens // 2,
            "total_tokens": tokens,
        },
    }


def create_mock_embedding(
    dimension: int = 768,
    value: float = 0.1,
) -> List[float]:
    """Create a mock embedding vector."""
    return [value] * dimension


def create_mock_search_result(
    chunk_id: str = "chunk-1",
    content: str = "Sample content",
    score: float = 0.95,
    document_id: str = "doc-1",
) -> Dict[str, Any]:
    """Create a mock search result."""
    return {
        "chunk_id": chunk_id,
        "content": content,
        "score": score,
        "document_id": document_id,
        "metadata": {"page": 1},
    }


def create_mock_embedding_service() -> MagicMock:
    """Create a mock embedding service."""
    mock = MagicMock()
    mock.embed_text = AsyncMock(return_value=create_mock_embedding())
    mock.embed_batch = AsyncMock(
        return_value=[create_mock_embedding() for _ in range(5)]
    )
    return mock


def create_mock_llm_manager() -> MagicMock:
    """Create a mock LLM manager."""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value=create_mock_llm_response())
    mock.stream = AsyncMock()
    return mock


def create_mock_milvus_service() -> MagicMock:
    """Create a mock Milvus service."""
    mock = MagicMock()
    mock.search = AsyncMock(
        return_value=[create_mock_search_result() for _ in range(3)]
    )
    mock.insert = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


def create_mock_redis_client() -> MagicMock:
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock
