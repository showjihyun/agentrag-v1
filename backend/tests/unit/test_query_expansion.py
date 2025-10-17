"""
Unit tests for QueryExpansionService.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.services.query_expansion import QueryExpansionService


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager."""
    llm_mock = Mock()
    llm_mock.generate = AsyncMock()
    return llm_mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    embedding_mock = Mock()
    embedding_mock.embed_text = Mock(return_value=[0.1, 0.2, 0.3])
    return embedding_mock


@pytest.fixture
def query_expansion(mock_llm_manager, mock_embedding_service):
    """Create QueryExpansionService instance."""
    return QueryExpansionService(
        llm_manager=mock_llm_manager, embedding_service=mock_embedding_service
    )


class TestQueryExpansionService:
    """Test QueryExpansionService functionality."""

    def test_initialization(self, query_expansion):
        """Test service initialization."""
        assert query_expansion.llm is not None
        assert query_expansion.embedding is not None

    def test_language_detection_korean(self, query_expansion):
        """Test Korean language detection."""
        korean_text = "인공지능이란 무엇인가?"
        lang = query_expansion._detect_language(korean_text)
        assert lang == "ko"

    def test_language_detection_english(self, query_expansion):
        """Test English language detection."""
        english_text = "What is artificial intelligence?"
        lang = query_expansion._detect_language(english_text)
        assert lang == "en"

    @pytest.mark.asyncio
    async def test_hyde_expansion(self, query_expansion, mock_llm_manager):
        """Test HyDE query expansion."""
        mock_llm_manager.generate.return_value = "AI is a technology..."

        queries = await query_expansion.hyde_expansion("What is AI?")

        assert len(queries) == 2
        assert queries[0] == "What is AI?"
        assert "AI is a technology" in queries[1]

    @pytest.mark.asyncio
    async def test_multi_query_expansion(self, query_expansion, mock_llm_manager):
        """Test multi-query expansion."""
        mock_llm_manager.generate.return_value = """1. artificial intelligence
2. machine learning
3. AI technology"""

        queries = await query_expansion.multi_query_expansion("AI", num_variations=3)

        assert len(queries) >= 1
        assert queries[0] == "AI"

    @pytest.mark.asyncio
    async def test_semantic_expansion(self, query_expansion, mock_llm_manager):
        """Test semantic expansion."""
        mock_llm_manager.generate.return_value = (
            "machine learning, ML, artificial intelligence"
        )

        queries = await query_expansion.semantic_expansion("AI")

        assert len(queries) >= 1
        assert queries[0] == "AI"

    def test_parse_queries(self, query_expansion):
        """Test query parsing."""
        response = """1. First query
2. Second query
3. Third query"""

        queries = query_expansion._parse_queries(response, 3)

        assert len(queries) == 3
        assert "First query" in queries[0]

    def test_parse_synonyms(self, query_expansion):
        """Test synonym parsing."""
        response = "AI, artificial intelligence, machine learning, ML"

        synonyms = query_expansion._parse_synonyms(response)

        assert len(synonyms) >= 2
        assert "AI" in synonyms or "artificial intelligence" in synonyms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
