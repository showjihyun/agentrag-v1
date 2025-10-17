"""
Unit tests for RerankerService.
"""

import pytest
from unittest.mock import Mock, patch
from backend.services.reranker import RerankerService


@pytest.fixture
def reranker_no_cross_encoder():
    """Create RerankerService without cross-encoder."""
    return RerankerService(use_cross_encoder=False)


@pytest.fixture
def sample_results():
    """Sample search results."""
    return [
        {
            "id": "1",
            "text": "AI is artificial intelligence",
            "score": 0.9,
            "embedding": [0.1, 0.2, 0.3],
        },
        {
            "id": "2",
            "text": "Machine learning is a subset of AI",
            "score": 0.8,
            "embedding": [0.2, 0.3, 0.4],
        },
        {
            "id": "3",
            "text": "Deep learning uses neural networks",
            "score": 0.7,
            "embedding": [0.3, 0.4, 0.5],
        },
    ]


class TestRerankerService:
    """Test RerankerService functionality."""

    def test_initialization_without_cross_encoder(self, reranker_no_cross_encoder):
        """Test initialization without cross-encoder."""
        assert reranker_no_cross_encoder.use_cross_encoder is False
        assert reranker_no_cross_encoder.cross_encoder is None

    def test_score_based_rerank(self, reranker_no_cross_encoder, sample_results):
        """Test score-based reranking."""
        reranked = reranker_no_cross_encoder._score_based_rerank(
            sample_results, top_k=2
        )

        assert len(reranked) == 2
        assert reranked[0]["score"] >= reranked[1]["score"]

    def test_mmr_rerank(self, reranker_no_cross_encoder, sample_results):
        """Test MMR reranking."""
        reranked = reranker_no_cross_encoder._mmr_rerank(
            query="What is AI?", results=sample_results, top_k=2, lambda_param=0.7
        )

        assert len(reranked) == 2
        assert "mmr_score" in reranked[0]

    def test_cosine_similarity(self, reranker_no_cross_encoder):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = reranker_no_cross_encoder._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(1.0, rel=1e-5)

    def test_cosine_similarity_orthogonal(self, reranker_no_cross_encoder):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = reranker_no_cross_encoder._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=1e-5)

    def test_rerank_with_method(self, reranker_no_cross_encoder, sample_results):
        """Test rerank with different methods."""
        # Test MMR method
        reranked_mmr = reranker_no_cross_encoder.rerank(
            query="What is AI?", results=sample_results, top_k=2, method="mmr"
        )

        assert len(reranked_mmr) == 2

        # Test default method (score-based)
        reranked_default = reranker_no_cross_encoder.rerank(
            query="What is AI?", results=sample_results, top_k=2, method="unknown"
        )

        assert len(reranked_default) == 2

    def test_text_based_mmr(self, reranker_no_cross_encoder):
        """Test text-based MMR without embeddings."""
        results = [
            {"id": "1", "text": "AI is great", "score": 0.9},
            {"id": "2", "text": "AI is wonderful", "score": 0.8},
            {"id": "3", "text": "Machine learning rocks", "score": 0.7},
        ]

        reranked = reranker_no_cross_encoder._text_based_mmr(
            query="AI", results=results, top_k=2, lambda_param=0.7
        )

        assert len(reranked) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
