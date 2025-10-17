"""
Unit tests for EmbeddingService.

Tests cover:
- Single text embedding generation
- Batch text embedding generation
- Embedding dimension consistency
- Error handling for invalid inputs
- Model caching behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.embedding import EmbeddingService


class TestEmbeddingServiceInitialization:
    """Test EmbeddingService initialization and model loading."""

    def test_init_with_default_model(self):
        """Test initialization with default model."""
        service = EmbeddingService()

        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert service.dimension > 0
        assert service.model is not None

    def test_init_with_custom_model(self):
        """Test initialization with custom model name."""
        # Use a small model for testing
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert service.dimension > 0

    def test_init_with_empty_model_name(self):
        """Test initialization fails with empty model name."""
        with pytest.raises(ValueError, match="model_name must be a non-empty string"):
            EmbeddingService(model_name="")

    def test_init_with_invalid_model_name_type(self):
        """Test initialization fails with non-string model name."""
        with pytest.raises(ValueError, match="model_name must be a non-empty string"):
            EmbeddingService(model_name=123)

    def test_model_caching(self):
        """Test that models are cached across instances."""
        # Clear cache first
        EmbeddingService.clear_cache()

        # Create first instance
        service1 = EmbeddingService()
        model1 = service1.model

        # Create second instance with same model
        service2 = EmbeddingService()
        model2 = service2.model

        # Should be the same cached instance
        assert model1 is model2

    def test_dimension_property(self):
        """Test dimension property returns correct value."""
        service = EmbeddingService()

        dimension = service.dimension
        assert isinstance(dimension, int)
        assert dimension > 0
        # all-MiniLM-L6-v2 has 384 dimensions
        assert dimension == 384


class TestEmbeddingServiceSingleText:
    """Test single text embedding generation."""

    def test_embed_text_success(self):
        """Test successful embedding generation for single text."""
        service = EmbeddingService()
        text = "This is a test sentence for embedding."

        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == service.dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_consistency(self):
        """Test that same text produces same embedding."""
        service = EmbeddingService()
        text = "Consistent text for testing."

        embedding1 = service.embed_text(text)
        embedding2 = service.embed_text(text)

        # Should be identical
        assert embedding1 == embedding2

    def test_embed_text_different_texts(self):
        """Test that different texts produce different embeddings."""
        service = EmbeddingService()
        text1 = "This is the first text."
        text2 = "This is a completely different text."

        embedding1 = service.embed_text(text1)
        embedding2 = service.embed_text(text2)

        # Should be different
        assert embedding1 != embedding2

    def test_embed_text_empty_string(self):
        """Test that empty string raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="text must be a non-empty string"):
            service.embed_text("")

    def test_embed_text_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="text cannot be only whitespace"):
            service.embed_text("   \n\t  ")

    def test_embed_text_invalid_type(self):
        """Test that non-string input raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="text must be a non-empty string"):
            service.embed_text(123)

    def test_embed_text_none(self):
        """Test that None input raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="text must be a non-empty string"):
            service.embed_text(None)

    def test_embed_text_long_text(self):
        """Test embedding generation for long text."""
        service = EmbeddingService()
        # Create a long text
        text = "This is a sentence. " * 100

        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == service.dimension

    def test_embed_text_special_characters(self):
        """Test embedding generation with special characters."""
        service = EmbeddingService()
        text = "Text with special chars: @#$%^&*()_+-=[]{}|;:',.<>?/~`"

        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == service.dimension

    def test_embed_text_unicode(self):
        """Test embedding generation with unicode characters."""
        service = EmbeddingService()
        text = "Unicode text: 你好世界 مرحبا العالم Привет мир"

        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == service.dimension


class TestEmbeddingServiceBatch:
    """Test batch embedding generation."""

    def test_embed_batch_success(self):
        """Test successful batch embedding generation."""
        service = EmbeddingService()
        texts = [
            "First text for embedding.",
            "Second text for embedding.",
            "Third text for embedding.",
        ]

        embeddings = service.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == service.dimension for emb in embeddings)

    def test_embed_batch_dimension_consistency(self):
        """Test that all embeddings in batch have same dimension."""
        service = EmbeddingService()
        texts = ["Text one", "Text two", "Text three", "Text four"]

        embeddings = service.embed_batch(texts)

        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1  # All same dimension
        assert dimensions[0] == service.dimension

    def test_embed_batch_single_text(self):
        """Test batch embedding with single text."""
        service = EmbeddingService()
        texts = ["Single text in batch"]

        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == service.dimension

    def test_embed_batch_large_batch(self):
        """Test batch embedding with many texts."""
        service = EmbeddingService()
        texts = [f"Text number {i}" for i in range(100)]

        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 100
        assert all(len(emb) == service.dimension for emb in embeddings)

    def test_embed_batch_custom_batch_size(self):
        """Test batch embedding with custom batch size."""
        service = EmbeddingService()
        texts = [f"Text {i}" for i in range(20)]

        embeddings = service.embed_batch(texts, batch_size=5)

        assert len(embeddings) == 20
        assert all(len(emb) == service.dimension for emb in embeddings)

    def test_embed_batch_empty_list(self):
        """Test that empty list raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="texts must be a non-empty list"):
            service.embed_batch([])

    def test_embed_batch_invalid_type(self):
        """Test that non-list input raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="texts must be a non-empty list"):
            service.embed_batch("not a list")

    def test_embed_batch_none(self):
        """Test that None input raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="texts must be a non-empty list"):
            service.embed_batch(None)

    def test_embed_batch_contains_empty_string(self):
        """Test that list with empty string raises ValueError."""
        service = EmbeddingService()
        texts = ["Valid text", "", "Another valid text"]

        with pytest.raises(ValueError, match="All texts must be non-empty strings"):
            service.embed_batch(texts)

    def test_embed_batch_contains_whitespace_only(self):
        """Test that list with whitespace-only string raises ValueError."""
        service = EmbeddingService()
        texts = ["Valid text", "   \n  ", "Another valid text"]

        with pytest.raises(ValueError, match="All texts must be non-empty strings"):
            service.embed_batch(texts)

    def test_embed_batch_contains_non_string(self):
        """Test that list with non-string raises ValueError."""
        service = EmbeddingService()
        texts = ["Valid text", 123, "Another valid text"]

        with pytest.raises(ValueError, match="All texts must be non-empty strings"):
            service.embed_batch(texts)

    def test_embed_batch_invalid_batch_size(self):
        """Test that invalid batch size raises ValueError."""
        service = EmbeddingService()
        texts = ["Text one", "Text two"]

        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            service.embed_batch(texts, batch_size=0)

    def test_embed_batch_consistency(self):
        """Test that batch embedding produces same results as individual."""
        service = EmbeddingService()
        texts = ["First text", "Second text", "Third text"]

        # Get batch embeddings
        batch_embeddings = service.embed_batch(texts)

        # Get individual embeddings
        individual_embeddings = [service.embed_text(text) for text in texts]

        # Should be identical
        for batch_emb, ind_emb in zip(batch_embeddings, individual_embeddings):
            assert batch_emb == ind_emb


class TestEmbeddingServiceDimensionConsistency:
    """Test embedding dimension consistency across different scenarios."""

    def test_dimension_consistency_across_texts(self):
        """Test that dimension is consistent for different texts."""
        service = EmbeddingService()

        texts = [
            "Short text",
            "This is a medium length text with more words.",
            "This is a very long text " * 50,
        ]

        embeddings = [service.embed_text(text) for text in texts]
        dimensions = [len(emb) for emb in embeddings]

        # All should have same dimension
        assert len(set(dimensions)) == 1
        assert dimensions[0] == service.dimension

    def test_dimension_consistency_single_vs_batch(self):
        """Test that dimension is consistent between single and batch."""
        service = EmbeddingService()
        text = "Test text for dimension consistency"

        single_embedding = service.embed_text(text)
        batch_embeddings = service.embed_batch([text])

        assert len(single_embedding) == len(batch_embeddings[0])
        assert len(single_embedding) == service.dimension

    def test_dimension_matches_model_spec(self):
        """Test that dimension matches model specification."""
        service = EmbeddingService()

        # all-MiniLM-L6-v2 should have 384 dimensions
        assert service.dimension == 384

        # Verify actual embeddings match
        embedding = service.embed_text("Test")
        assert len(embedding) == 384


class TestEmbeddingServiceModelInfo:
    """Test model information retrieval."""

    def test_get_model_info(self):
        """Test getting model information."""
        service = EmbeddingService()

        info = service.get_model_info()

        assert isinstance(info, dict)
        assert "model_name" in info
        assert "dimension" in info
        assert "max_seq_length" in info
        assert "cached" in info

        assert info["model_name"] == service.model_name
        assert info["dimension"] == service.dimension
        assert isinstance(info["max_seq_length"], int)
        assert isinstance(info["cached"], bool)


class TestEmbeddingServiceCaching:
    """Test model caching functionality."""

    def test_clear_cache(self):
        """Test clearing model cache."""
        # Create service to populate cache
        service = EmbeddingService()
        assert len(EmbeddingService._model_cache) > 0

        # Clear cache
        EmbeddingService.clear_cache()

        assert len(EmbeddingService._model_cache) == 0

    def test_cache_reuse(self):
        """Test that cache is reused for same model."""
        EmbeddingService.clear_cache()

        service1 = EmbeddingService()
        info1 = service1.get_model_info()

        service2 = EmbeddingService()
        info2 = service2.get_model_info()

        # Both should report as cached (second one definitely)
        assert info2["cached"] is True


class TestEmbeddingServiceErrorHandling:
    """Test error handling in various scenarios."""

    @patch("backend.services.embedding.SentenceTransformer")
    def test_model_load_failure(self, mock_transformer):
        """Test handling of model load failure."""
        mock_transformer.side_effect = Exception("Model load failed")

        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            EmbeddingService(model_name="test-model")

    @patch.object(EmbeddingService, "model")
    def test_embed_text_runtime_error(self, mock_model):
        """Test handling of runtime error during embedding."""
        service = EmbeddingService()
        mock_model.encode = Mock(side_effect=Exception("Encoding failed"))

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            service.embed_text("Test text")

    @patch.object(EmbeddingService, "model")
    def test_embed_batch_runtime_error(self, mock_model):
        """Test handling of runtime error during batch embedding."""
        service = EmbeddingService()
        mock_model.encode = Mock(side_effect=Exception("Batch encoding failed"))

        with pytest.raises(RuntimeError, match="Failed to generate batch embeddings"):
            service.embed_batch(["Text 1", "Text 2"])


class TestEmbeddingServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_short_text(self):
        """Test embedding generation for very short text."""
        service = EmbeddingService()
        text = "Hi"

        embedding = service.embed_text(text)

        assert len(embedding) == service.dimension

    def test_text_with_numbers(self):
        """Test embedding generation with numbers."""
        service = EmbeddingService()
        text = "The year 2024 has 365 days and 12 months."

        embedding = service.embed_text(text)

        assert len(embedding) == service.dimension

    def test_text_with_mixed_content(self):
        """Test embedding with mixed content types."""
        service = EmbeddingService()
        text = (
            "Email: test@example.com, Phone: +1-234-567-8900, URL: https://example.com"
        )

        embedding = service.embed_text(text)

        assert len(embedding) == service.dimension

    def test_batch_with_varying_lengths(self):
        """Test batch with texts of varying lengths."""
        service = EmbeddingService()
        texts = ["Short", "Medium length text here", "This is a much longer text " * 20]

        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == service.dimension for emb in embeddings)
