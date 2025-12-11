"""Query-related test fixtures."""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_query_data() -> Dict[str, Any]:
    """Sample query data for testing."""
    return {
        "query": "What is machine learning?",
        "mode": "balanced",
    }


@pytest.fixture
def simple_query_data() -> Dict[str, Any]:
    """Simple query for fast mode testing."""
    return {
        "query": "Hello",
        "mode": "fast",
    }


@pytest.fixture
def complex_query_data() -> Dict[str, Any]:
    """Complex query for deep mode testing."""
    return {
        "query": "Compare and contrast the architectural differences between transformer-based models and traditional RNN architectures, focusing on attention mechanisms and their impact on long-range dependencies.",
        "mode": "deep",
    }


@pytest.fixture
def korean_query_data() -> Dict[str, Any]:
    """Korean language query for testing."""
    return {
        "query": "머신러닝이란 무엇인가요?",
        "mode": "balanced",
    }


@pytest.fixture
def query_with_context() -> Dict[str, Any]:
    """Query with session context."""
    return {
        "query": "Tell me more about that",
        "mode": "balanced",
        "session_id": "test-session-123",
    }


@pytest.fixture
def batch_queries() -> list[Dict[str, Any]]:
    """Multiple queries for batch testing."""
    return [
        {"query": "What is AI?", "mode": "fast"},
        {"query": "Explain neural networks", "mode": "balanced"},
        {"query": "How does backpropagation work?", "mode": "balanced"},
        {"query": "Compare CNN and RNN", "mode": "deep"},
    ]


@pytest.fixture
def expected_search_results() -> list[Dict[str, Any]]:
    """Expected search results for mocking."""
    return [
        {
            "chunk_id": "chunk-1",
            "content": "Machine learning is a subset of artificial intelligence...",
            "score": 0.95,
            "document_id": "doc-1",
            "metadata": {"page": 1},
        },
        {
            "chunk_id": "chunk-2",
            "content": "Deep learning uses neural networks with multiple layers...",
            "score": 0.87,
            "document_id": "doc-2",
            "metadata": {"page": 5},
        },
    ]
