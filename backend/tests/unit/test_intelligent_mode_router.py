"""
Unit tests for IntelligentModeRouter.

Tests routing logic, mode selection, user preferences, forced modes,
and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.services.intelligent_mode_router import (
    IntelligentModeRouter,
    RoutingDecision,
    CacheStrategy,
    get_intelligent_mode_router,
)
from backend.services.adaptive_rag_service import (
    AdaptiveRAGService,
    QueryComplexity,
    ComplexityAnalysis,
)
from backend.models.hybrid import QueryMode
from backend.config import Settings


@pytest.fixture
def mock_adaptive_service():
    """Create mock AdaptiveRAGService."""
    service = Mock(spec=AdaptiveRAGService)
    return service


@pytest.fixture
def mock_settings():
    """Create mock Settings."""
    settings = Mock(spec=Settings)
    settings.DEBUG = False
    return settings


@pytest.fixture
def router(mock_adaptive_service, mock_settings):
    """Create IntelligentModeRouter instance."""
    return IntelligentModeRouter(
        adaptive_service=mock_adaptive_service, settings=mock_settings
    )


class TestModeSelection:
    """Test mode selection based on complexity."""

    @pytest.mark.asyncio
    async def test_simple_query_routes_to_fast(self, router, mock_adaptive_service):
        """Test that simple queries route to FAST mode."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={"word_count": {"score": 0.25, "value": 8}},
                reasoning="Simple factual question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route query
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session"
        )

        # Assertions
        assert decision.mode == QueryMode.FAST
        assert decision.complexity == QueryComplexity.SIMPLE
        assert decision.complexity_score == 0.25
        assert decision.top_k == 5
        assert decision.cache_strategy == CacheStrategy.L1_ONLY
        assert not decision.forced
        assert decision.routing_confidence > 0.7

    @pytest.mark.asyncio
    async def test_medium_query_routes_to_balanced(self, router, mock_adaptive_service):
        """Test that medium queries route to BALANCED mode."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={"word_count": {"score": 0.5, "value": 20}},
                reasoning="Comparative question",
                language="en",
                word_count=20,
                question_type="comparative",
            )
        )

        # Route query
        decision = await router.route_query(
            query="Compare RAG and fine-tuning approaches", session_id="test_session"
        )

        # Assertions
        assert decision.mode == QueryMode.BALANCED
        assert decision.complexity == QueryComplexity.MEDIUM
        assert decision.complexity_score == 0.55
        assert decision.top_k == 10
        assert decision.cache_strategy == CacheStrategy.L1_L2
        assert not decision.forced

    @pytest.mark.asyncio
    async def test_complex_query_routes_to_deep(self, router, mock_adaptive_service):
        """Test that complex queries route to DEEP mode."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.COMPLEX,
                score=0.85,
                confidence=0.90,
                factors={"word_count": {"score": 1.0, "value": 45}},
                reasoning="Analytical multi-step question",
                language="en",
                word_count=45,
                question_type="analytical",
            )
        )

        # Route query
        decision = await router.route_query(
            query="Analyze the evolution of RAG systems from 2020 to 2024 and explain why certain approaches became dominant",
            session_id="test_session",
        )

        # Assertions
        assert decision.mode == QueryMode.DEEP
        assert decision.complexity == QueryComplexity.COMPLEX
        assert decision.complexity_score == 0.85
        assert decision.top_k == 15
        assert decision.cache_strategy == CacheStrategy.ALL_LEVELS
        assert not decision.forced


class TestForcedMode:
    """Test forced mode override functionality."""

    @pytest.mark.asyncio
    async def test_forced_fast_mode(self, router, mock_adaptive_service):
        """Test forcing FAST mode."""
        # Mock complexity analysis (would normally be MEDIUM)
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={},
                reasoning="Medium complexity",
                language="en",
                word_count=20,
                question_type="comparative",
            )
        )

        # Route with forced mode
        decision = await router.route_query(
            query="Compare RAG and fine-tuning",
            session_id="test_session",
            forced_mode=QueryMode.FAST,
        )

        # Assertions
        assert decision.mode == QueryMode.FAST
        assert decision.forced is True
        assert decision.routing_confidence == 1.0
        assert decision.reasoning["forced"] is True
        assert decision.reasoning["suboptimal"] is True

    @pytest.mark.asyncio
    async def test_forced_deep_mode(self, router, mock_adaptive_service):
        """Test forcing DEEP mode."""
        # Mock complexity analysis (would normally be SIMPLE)
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={},
                reasoning="Simple question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route with forced mode
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session", forced_mode=QueryMode.DEEP
        )

        # Assertions
        assert decision.mode == QueryMode.DEEP
        assert decision.forced is True
        assert decision.reasoning["suboptimal"] is True
        assert "warning" in decision.reasoning

    @pytest.mark.asyncio
    async def test_forced_mode_optimal(self, router, mock_adaptive_service):
        """Test forcing mode that matches recommendation."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={},
                reasoning="Simple question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route with forced mode that matches recommendation
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session", forced_mode=QueryMode.FAST
        )

        # Assertions
        assert decision.mode == QueryMode.FAST
        assert decision.forced is True
        assert decision.reasoning["suboptimal"] is False
        assert decision.reasoning["warning"] is None


class TestUserPreferences:
    """Test user preference handling."""

    @pytest.mark.asyncio
    async def test_preferred_mode_override(self, router, mock_adaptive_service):
        """Test user preferred mode override."""
        # Mock complexity analysis (would be BALANCED)
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={},
                reasoning="Medium complexity",
                language="en",
                word_count=20,
                question_type="comparative",
            )
        )

        # Route with user preference
        decision = await router.route_query(
            query="Compare RAG and fine-tuning",
            session_id="test_session",
            user_prefs={"preferred_mode": "deep"},
        )

        # Assertions
        assert decision.mode == QueryMode.DEEP
        assert "user_preferences" in decision.reasoning

    @pytest.mark.asyncio
    async def test_prefer_speed(self, router, mock_adaptive_service):
        """Test prefer_speed downgrade."""
        # Mock complexity analysis (MEDIUM)
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={},
                reasoning="Medium complexity",
                language="en",
                word_count=20,
                question_type="comparative",
            )
        )

        # Route with speed preference
        decision = await router.route_query(
            query="Compare RAG and fine-tuning",
            session_id="test_session",
            user_prefs={"prefer_speed": True},
        )

        # Assertions
        assert decision.mode == QueryMode.FAST

    @pytest.mark.asyncio
    async def test_prefer_quality(self, router, mock_adaptive_service):
        """Test prefer_quality upgrade."""
        # Mock complexity analysis (MEDIUM)
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={},
                reasoning="Medium complexity",
                language="en",
                word_count=20,
                question_type="comparative",
            )
        )

        # Route with quality preference
        decision = await router.route_query(
            query="Compare RAG and fine-tuning",
            session_id="test_session",
            user_prefs={"prefer_quality": True},
        )

        # Assertions
        assert decision.mode == QueryMode.DEEP


class TestRoutingConfidence:
    """Test routing confidence calculation."""

    @pytest.mark.asyncio
    async def test_high_confidence_routing(self, router, mock_adaptive_service):
        """Test high confidence routing."""
        # Mock high confidence complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.15,  # Far from threshold
                confidence=0.90,
                factors={},
                reasoning="Very simple question",
                language="en",
                word_count=5,
                question_type="factual",
            )
        )

        # Route query
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session"
        )

        # Assertions
        assert decision.routing_confidence >= 0.85

    @pytest.mark.asyncio
    async def test_lower_confidence_near_boundary(self, router, mock_adaptive_service):
        """Test lower confidence near complexity boundary."""
        # Mock complexity analysis near threshold
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.36,  # Just above SIMPLE threshold
                confidence=0.65,
                factors={},
                reasoning="Near boundary",
                language="en",
                word_count=15,
                question_type="general",
            )
        )

        # Route query
        decision = await router.route_query(
            query="Explain RAG systems", session_id="test_session"
        )

        # Assertions
        assert decision.routing_confidence < 0.85


class TestReasoning:
    """Test reasoning generation."""

    @pytest.mark.asyncio
    async def test_reasoning_includes_complexity(self, router, mock_adaptive_service):
        """Test that reasoning includes complexity details."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={"word_count": {"score": 0.25, "value": 8}},
                reasoning="Simple factual question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route query
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session"
        )

        # Assertions
        assert "complexity" in decision.reasoning
        assert decision.reasoning["complexity"]["level"] == "simple"
        assert decision.reasoning["complexity"]["score"] == 0.25
        assert decision.reasoning["complexity"]["word_count"] == 8

    @pytest.mark.asyncio
    async def test_reasoning_includes_mode_parameters(
        self, router, mock_adaptive_service
    ):
        """Test that reasoning includes mode parameters."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={},
                reasoning="Simple question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route query
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session"
        )

        # Assertions
        assert "mode_parameters" in decision.reasoning
        assert decision.reasoning["mode_parameters"]["top_k"] == 5
        assert decision.reasoning["mode_parameters"]["cache_strategy"] == "l1_only"

    @pytest.mark.asyncio
    async def test_reasoning_includes_expected_performance(
        self, router, mock_adaptive_service
    ):
        """Test that reasoning includes expected performance."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.DEEP,
                score=0.85,
                confidence=0.90,
                factors={},
                reasoning="Complex question",
                language="en",
                word_count=45,
                question_type="analytical",
            )
        )

        # Route query
        decision = await router.route_query(
            query="Analyze RAG evolution", session_id="test_session"
        )

        # Assertions
        assert "expected_performance" in decision.reasoning
        assert "target_latency" in decision.reasoning["expected_performance"]
        assert "cache_levels" in decision.reasoning["expected_performance"]


class TestErrorHandling:
    """Test error handling and fallback."""

    @pytest.mark.asyncio
    async def test_fallback_on_analysis_error(self, router, mock_adaptive_service):
        """Test fallback to BALANCED mode on analysis error."""
        # Mock analysis error
        mock_adaptive_service.analyze_query_complexity.side_effect = Exception(
            "Analysis failed"
        )

        # Route query
        decision = await router.route_query(
            query="What is RAG?", session_id="test_session"
        )

        # Assertions
        assert decision.mode == QueryMode.BALANCED
        assert decision.complexity == QueryComplexity.MEDIUM
        assert decision.reasoning["fallback"] is True
        assert "error" in decision.reasoning

    @pytest.mark.asyncio
    async def test_invalid_preferred_mode(self, router, mock_adaptive_service):
        """Test handling of invalid preferred mode."""
        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.SIMPLE,
                score=0.25,
                confidence=0.85,
                factors={},
                reasoning="Simple question",
                language="en",
                word_count=8,
                question_type="factual",
            )
        )

        # Route with invalid preferred mode
        decision = await router.route_query(
            query="What is RAG?",
            session_id="test_session",
            user_prefs={"preferred_mode": "invalid_mode"},
        )

        # Should ignore invalid preference and use complexity-based routing
        assert decision.mode == QueryMode.FAST


class TestModeParameters:
    """Test mode parameter management."""

    def test_get_mode_parameters(self, router):
        """Test getting mode parameters."""
        # Get FAST mode parameters
        params = router.get_mode_parameters(QueryMode.FAST)

        # Assertions
        assert params["top_k"] == 5
        assert params["cache_strategy"] == CacheStrategy.L1_ONLY
        assert params["enable_web_search"] is False
        assert params["timeout"] == 1.0

    def test_update_mode_parameters(self, router):
        """Test updating mode parameters."""
        # Update FAST mode parameters
        router.update_mode_parameters(QueryMode.FAST, top_k=7, timeout=1.5)

        # Get updated parameters
        params = router.get_mode_parameters(QueryMode.FAST)

        # Assertions
        assert params["top_k"] == 7
        assert params["timeout"] == 1.5


class TestSingleton:
    """Test singleton pattern."""

    def test_get_intelligent_mode_router_singleton(self):
        """Test that get_intelligent_mode_router returns singleton."""
        router1 = get_intelligent_mode_router()
        router2 = get_intelligent_mode_router()

        assert router1 is router2


class TestKoreanLanguageSupport:
    """Test Korean language support."""

    @pytest.mark.asyncio
    async def test_korean_query_routing(self, router, mock_adaptive_service):
        """Test routing Korean query."""
        # Mock Korean complexity analysis
        mock_adaptive_service.analyze_query_complexity.return_value = (
            ComplexityAnalysis(
                complexity=QueryComplexity.MEDIUM,
                score=0.55,
                confidence=0.80,
                factors={},
                reasoning="Korean comparative question",
                language="ko",
                word_count=15,
                question_type="comparative",
            )
        )

        # Route Korean query
        decision = await router.route_query(
            query="RAG와 파인튜닝을 비교해주세요",
            session_id="test_session",
            language="ko",
        )

        # Assertions
        assert decision.mode == QueryMode.BALANCED
        assert decision.reasoning["complexity"]["language"] == "ko"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
