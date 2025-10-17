"""
Utility functions for testing.
"""

import asyncio
from typing import List, Dict, Any
from pathlib import Path


def create_test_document(content: str, filename: str = "test.txt") -> Dict[str, Any]:
    """Create a test document dictionary."""
    return {
        "filename": filename,
        "content": content,
        "metadata": {"source": "test", "type": "text"},
    }


def create_test_chunks(num_chunks: int = 3) -> List[Dict[str, Any]]:
    """Create test text chunks."""
    chunks = []
    for i in range(num_chunks):
        chunks.append(
            {
                "text": f"This is test chunk number {i+1}. It contains sample text for testing purposes.",
                "metadata": {"chunk_id": i, "document_id": "test_doc_001"},
            }
        )
    return chunks


async def wait_for_service(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for a service to become available."""
    import socket

    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return True
        except Exception:
            pass

        await asyncio.sleep(1)

    return False


def assert_valid_embedding(embedding: List[float], expected_dim: int = 384):
    """Assert that an embedding is valid."""
    assert isinstance(embedding, list), "Embedding should be a list"
    assert (
        len(embedding) == expected_dim
    ), f"Embedding dimension should be {expected_dim}"
    assert all(
        isinstance(x, float) for x in embedding
    ), "All embedding values should be floats"


def assert_valid_search_result(result: Dict[str, Any]):
    """Assert that a search result has required fields."""
    required_fields = ["id", "score", "text"]
    for field in required_fields:
        assert field in result, f"Search result missing required field: {field}"

    assert isinstance(result["score"], float), "Score should be a float"
    assert 0 <= result["score"] <= 1, "Score should be between 0 and 1"


class MockLLMResponse:
    """Mock LLM response for testing."""

    def __init__(self, content: str):
        self.content = content

    def __str__(self):
        return self.content


class AsyncMock:
    """Simple async mock for testing."""

    def __init__(self, return_value=None):
        self.return_value = return_value
        self.call_count = 0
        self.call_args_list = []

    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args_list.append((args, kwargs))
        return self.return_value
