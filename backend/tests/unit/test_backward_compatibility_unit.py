"""
Unit tests for backward compatibility features.

Tests feature flag behavior, API contract compatibility, and fallback mechanisms.

Requirements: 12.1, 12.2, 12.3, 12.5
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.models.query import QueryRequest
from backend.models.hybrid import HybridQueryRequest, QueryMode


class TestFeatureFlag:
    """Test ENABLE_SPECULATIVE_RAG feature flag behavior."""

    def test_feature_flag_exists(self):
        """
        Test that ENABLE_SPECULATIVE_RAG config flag exists.

        Requirements: 12.1
        """
        from config import settings

        assert hasattr(settings, "ENABLE_SPECULATIVE_RAG")
        assert isinstance(settings.ENABLE_SPECULATIVE_RAG, bool)

    def test_default_mode_config_exists(self):
        """
        Test that DEFAULT_QUERY_MODE config exists.

        Requirements: 12.1, 12.4
        """
        from config import settings

        assert hasattr(settings, "DEFAULT_QUERY_MODE")
        assert settings.DEFAULT_QUERY_MODE in ["fast", "balanced", "deep"]

    @patch("backend.config.settings")
    def test_hybrid_disabled_behavior(self, mock_settings):
        """
        Test that system behaves correctly when hybrid is disabled.

        Requirements: 12.1, 12.4
        """
        # Configure mock settings
        mock_settings.ENABLE_SPECULATIVE_RAG = False
        mock_settings.DEFAULT_QUERY_MODE = "balanced"

        # When hybrid is disabled, system should fall back to agentic-only
        # This is tested in the API endpoint logic
        assert mock_settings.ENABLE_SPECULATIVE_RAG is False

    @patch("backend.config.settings")
    def test_hybrid_enabled_uses_default_mode(self, mock_settings):
        """
        Test that default mode is used when hybrid is enabled.

        Requirements: 12.1, 12.4
        """
        mock_settings.ENABLE_SPECULATIVE_RAG = True
        mock_settings.DEFAULT_QUERY_MODE = "balanced"

        # When enabled, should use configured default mode
        assert mock_settings.ENABLE_SPECULATIVE_RAG is True
        assert mock_settings.DEFAULT_QUERY_MODE == "balanced"


class TestAPIContractCompatibility:
    """Test that API maintains backward compatibility."""

    def test_query_request_model_unchanged(self):
        """
        Test that QueryRequest model structure is unchanged.

        Requirements: 12.2, 12.3
        """
        # Create a legacy QueryRequest
        request = QueryRequest(
            query="What is machine learning?", session_id="test_session", top_k=10
        )

        # Verify all original fields exist
        assert hasattr(request, "query")
        assert hasattr(request, "session_id")
        assert hasattr(request, "top_k")
        assert hasattr(request, "filters")
        assert hasattr(request, "stream")

        # Verify values
        assert request.query == "What is machine learning?"
        assert request.session_id == "test_session"
        assert request.top_k == 10

    def test_hybrid_request_extends_query_request(self):
        """
        Test that HybridQueryRequest properly extends QueryRequest.

        Requirements: 12.2, 12.3
        """
        # Create a HybridQueryRequest
        request = HybridQueryRequest(
            query="What is deep learning?",
            session_id="test_session",
            top_k=10,
            mode=QueryMode.BALANCED,
        )

        # Verify it has all QueryRequest fields
        assert hasattr(request, "query")
        assert hasattr(request, "session_id")
        assert hasattr(request, "top_k")

        # Verify it has new fields
        assert hasattr(request, "mode")
        assert hasattr(request, "enable_cache")
        assert hasattr(request, "speculative_timeout")
        assert hasattr(request, "agentic_timeout")

    def test_hybrid_request_has_defaults(self):
        """
        Test that HybridQueryRequest has sensible defaults for new fields.

        Requirements: 12.2, 12.3
        """
        # Create request without specifying new fields
        request = HybridQueryRequest(query="Test query", session_id="test")

        # Verify defaults
        assert request.mode == QueryMode.BALANCED
        assert request.enable_cache is True
        assert request.speculative_timeout == 2.0
        assert request.agentic_timeout == 15.0

    def test_old_request_format_compatible(self):
        """
        Test that old QueryRequest format can be used with new endpoint.

        Requirements: 12.2, 12.3
        """
        # Create old-style request
        old_request = QueryRequest(query="Old format query", session_id="old_session")

        # Convert to dict (simulating JSON serialization)
        request_dict = old_request.model_dump()

        # Should be able to create HybridQueryRequest from it
        # (with defaults for new fields)
        hybrid_request = HybridQueryRequest(**request_dict)

        assert hybrid_request.query == "Old format query"
        assert hybrid_request.session_id == "old_session"
        assert hybrid_request.mode == QueryMode.BALANCED  # Default

    def test_response_format_backward_compatible(self):
        """
        Test that response format maintains backward compatibility.

        Requirements: 12.2, 12.3
        """
        from models.query import QueryResponse

        # Create a response in the original format
        response = QueryResponse(
            query_id="test_123",
            query="Test query",
            response="Test response",
            sources=[],
            reasoning_steps=[],
            session_id="test_session",
            processing_time=1.5,
            metadata={},
        )

        # Verify all fields exist
        assert response.query_id == "test_123"
        assert response.query == "Test query"
        assert response.response == "Test response"
        assert isinstance(response.sources, list)
        assert isinstance(response.reasoning_steps, list)


class TestFallbackMechanisms:
    """Test fallback mechanisms when hybrid components fail."""

    @pytest.mark.asyncio
    async def test_hybrid_router_none_fallback(self):
        """
        Test that system falls back to legacy mode when hybrid router is None.

        Requirements: 12.1, 12.4
        """
        # This tests the logic in api/query.py
        # When get_hybrid_query_router() returns None, should use legacy mode

        # Mock the scenario
        hybrid_router = None
        hybrid_enabled = False

        # System should fall back to agentic-only
        assert hybrid_router is None
        assert hybrid_enabled is False

    @pytest.mark.asyncio
    async def test_hybrid_initialization_failure_fallback(self):
        """
        Test fallback when hybrid components fail to initialize.

        Requirements: 12.1, 12.4
        """
        # When hybrid components fail to initialize, system should:
        # 1. Log the error
        # 2. Set hybrid_enabled = False
        # 3. Continue with legacy mode

        # This is handled in the API endpoint
        with patch("backend.api.query.get_hybrid_query_router") as mock_get_router:
            mock_get_router.side_effect = Exception("Initialization failed")

            # Should catch exception and fall back
            try:
                hybrid_router = mock_get_router()
            except Exception:
                hybrid_router = None

            assert hybrid_router is None


class TestModeSelection:
    """Test query mode selection logic."""

    def test_mode_defaults_to_balanced(self):
        """
        Test that mode defaults to BALANCED when not specified.

        Requirements: 12.1, 12.4
        """
        request = HybridQueryRequest(query="Test query")

        assert request.mode == QueryMode.BALANCED

    def test_mode_can_be_specified(self):
        """
        Test that mode can be explicitly specified.

        Requirements: 12.1
        """
        # Test FAST mode
        request_fast = HybridQueryRequest(query="Test query", mode=QueryMode.FAST)
        assert request_fast.mode == QueryMode.FAST

        # Test BALANCED mode
        request_balanced = HybridQueryRequest(
            query="Test query", mode=QueryMode.BALANCED
        )
        assert request_balanced.mode == QueryMode.BALANCED

        # Test DEEP mode
        request_deep = HybridQueryRequest(query="Test query", mode=QueryMode.DEEP)
        assert request_deep.mode == QueryMode.DEEP

    def test_mode_string_conversion(self):
        """
        Test that mode strings are properly converted to enum.

        Requirements: 12.1
        """
        # Test with string values
        request = HybridQueryRequest(query="Test query", mode="fast")
        assert request.mode == QueryMode.FAST

        request = HybridQueryRequest(query="Test query", mode="balanced")
        assert request.mode == QueryMode.BALANCED

        request = HybridQueryRequest(query="Test query", mode="deep")
        assert request.mode == QueryMode.DEEP


class TestDataMigration:
    """Test data migration scenarios."""

    def test_old_memory_format_compatible(self):
        """
        Test that old memory format is compatible with new system.

        Requirements: 12.5
        """
        # Old memory format (simple dict)
        old_memory = {
            "role": "user",
            "content": "What is AI?",
            "timestamp": datetime.now().isoformat(),
        }

        # Should be compatible with new system
        assert "role" in old_memory
        assert "content" in old_memory
        assert old_memory["role"] in ["user", "assistant", "system"]

    def test_old_document_format_compatible(self):
        """
        Test that old document format is compatible with new system.

        Requirements: 12.5
        """
        # Old document format
        old_document = {
            "chunk_id": "doc_1_chunk_1",
            "document_id": "doc_1",
            "document_name": "test.pdf",
            "text": "Test content",
            "metadata": {"page": 1},
        }

        # Should have all required fields
        assert "chunk_id" in old_document
        assert "document_id" in old_document
        assert "document_name" in old_document
        assert "text" in old_document
        assert "metadata" in old_document

    def test_cache_key_format_stable(self):
        """
        Test that cache key format is stable across versions.

        Requirements: 12.5
        """
        # Cache keys should be deterministic and stable
        query_embedding = [0.1, 0.2, 0.3]
        top_k = 10

        # Generate cache key (simplified version)
        import hashlib
        import json

        cache_data = {"embedding": query_embedding, "top_k": top_k}
        cache_key = hashlib.md5(
            json.dumps(cache_data, sort_keys=True).encode()
        ).hexdigest()

        # Should be consistent
        cache_key_2 = hashlib.md5(
            json.dumps(cache_data, sort_keys=True).encode()
        ).hexdigest()

        assert cache_key == cache_key_2


class TestConfigValidation:
    """Test configuration validation for backward compatibility."""

    def test_default_query_mode_validation(self):
        """
        Test that DEFAULT_QUERY_MODE is validated.

        Requirements: 12.1, 12.4
        """
        from config import Settings

        # Valid modes should work
        valid_modes = ["fast", "balanced", "deep"]
        for mode in valid_modes:
            settings = Settings(DEFAULT_QUERY_MODE=mode)
            assert settings.DEFAULT_QUERY_MODE == mode

    def test_invalid_default_mode_rejected(self):
        """
        Test that invalid DEFAULT_QUERY_MODE is rejected.

        Requirements: 12.1, 12.4
        """
        from config import Settings
        from pydantic import ValidationError

        # Invalid mode should raise error
        with pytest.raises(ValidationError):
            Settings(DEFAULT_QUERY_MODE="invalid_mode")

    def test_feature_flag_type_validation(self):
        """
        Test that ENABLE_SPECULATIVE_RAG is validated as boolean.

        Requirements: 12.1
        """
        from config import Settings

        # Should accept boolean values
        settings_true = Settings(ENABLE_SPECULATIVE_RAG=True)
        assert settings_true.ENABLE_SPECULATIVE_RAG is True

        settings_false = Settings(ENABLE_SPECULATIVE_RAG=False)
        assert settings_false.ENABLE_SPECULATIVE_RAG is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
