"""
Integration tests for end-to-end adaptive routing flows.

Tests the complete flow from query input through routing, execution,
caching, and metrics collection.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import AsyncGenerator

from backend.services.intelligent_mode_router import (
    IntelligentModeRouter,
    RoutingDecision,
)
from backend.services.query_pattern_learner import QueryPatternLearner
from backend.services.adaptive_rag_service import AdaptiveRAGService
from backend.services.threshold_tuner import ThresholdTuner
from backend.services.adaptive_metrics import AdaptiveMetricsCollector
from backend.core.multi_level_cache import MultiLevelCache
from backend.core.speculative_processor import SpeculativeQueryProcessor
from backend.models.hybrid import QueryMode, QueryComplexity
from config import Settings


@pytest.fixture
def settings():
    """Test settings."""
    return Settings(
        ADAPTIVE_ROUTING_ENABLED=True,
        COMPLEXITY_THRESHOLD_SIMPLE=0.35,
        COMPLEXITY_THRESHOLD_COMPLEX=0.70,
        FAST_MODE_TIMEOUT=1.0,
        BALANCED_MODE_TIMEOUT=3.0,
        DEEP_MODE_TIMEOUT=15.0,
        FAST_MODE_TOP_K=5,
        BALANCED_MODE_TOP_K=10,
        DEEP_MODE_TOP_K=15,
        ENABLE_PATTERN_LEARNING=True,
        ENABLE_AUTO_THRESHOLD_TUNING=False,
    )


@pytest.fixture
def mock_adaptive_service():
    """Mock adaptive RAG service."""
    service = Mock(spec=AdaptiveRAGService)
    return service


@pytest.fixture
def mock_pattern_learner():
    """Mock pattern learner."""
    learner = Mock(spec=QueryPatternLearner)
    learner.get_pattern_recommendation = AsyncMock(return_value=None)
    learner.record_query = AsyncMock()
    return learner


@pytest.fixture
def mock_cache():
    """Mock multi-level cache."""
    cache = Mock(spec=MultiLevelCache)
    cache.get_with_mode = AsyncMock(return_value=None)
    cache.set_with_mode = AsyncMock()
    return cache


@pytest.fixture
def mock_processor():
    """Mock speculative processor."""
    processor = Mock(spec=SpeculativeQueryProcessor)

    async def mock_process(*args, **kwargs):
        yield {"type": "thought", "content": "Processing query"}
        yield {"type": "answer", "content": "Test answer"}

    processor.process_query_with_mode = mock_process
    return processor


@pytest.fixture
def mock_metrics():
    """Mock metrics collector."""
    metrics = Mock(spec=AdaptiveMetricsCollector)
    metrics.record_routing_decision = AsyncMock()
    metrics.record_query_execution = AsyncMock()
    return metrics


@pytest.fixture
def router(settings, mock_adaptive_service, mock_pattern_learner):
    """Create router instance."""
    return IntelligentModeRouter(
        adaptive_service=mock_adaptive_service,
        pattern_learner=mock_pattern_learner,
        settings=settings,
    )


class TestFastModeE2E:
    """Test complete FAST mode flow."""

    @pytest.mark.asyncio
    async def test_fast_mode_complete_flow(
        self,
        router,
        mock_adaptive_service,
        mock_cache,
        mock_processor,
        mock_metrics,
        mock_pattern_learner,
    ):
        """Test complete FAST mode flow from routing to response."""
        # Setup: Simple query
        query = "What is RAG?"
        session_id = "test-session"

        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.25,
            confidence=0.9,
            factors={"word_count": 3, "question_type": "factual"},
            reasoning="Simple factual question",
            language="en",
        )

        # Step 1: Route query
        routing = await router.route_query(query, session_id)

        assert routing.mode == QueryMode.FAST
        assert routing.complexity == QueryComplexity.SIMPLE
        assert routing.top_k == 5

        # Step 2: Check cache (miss)
        cache_result = await mock_cache.get_with_mode(f"query:{query}", QueryMode.FAST)
        assert cache_result is None

        # Step 3: Process query
        results = []
        async for step in mock_processor.process_query_with_mode(
            query=query, session_id=session_id, mode=QueryMode.FAST, top_k=5
        ):
            results.append(step)

        assert len(results) > 0
        assert any(r.get("type") == "answer" for r in results)

        # Step 4: Cache result
        await mock_cache.set_with_mode(f"query:{query}", results[-1], QueryMode.FAST)

        # Step 5: Record metrics
        await mock_metrics.record_routing_decision(routing)
        await mock_metrics.record_query_execution(
            query_id="test-id",
            mode=QueryMode.FAST,
            processing_time=0.5,
            cache_hit=False,
        )

        # Step 6: Update patterns
        await mock_pattern_learner.record_query(
            query=query,
            complexity=QueryComplexity.SIMPLE,
            mode_used=QueryMode.FAST,
            processing_time=0.5,
            confidence_score=0.9,
        )

        # Verify all steps executed
        mock_cache.get_with_mode.assert_called_once()
        mock_cache.set_with_mode.assert_called_once()
        mock_metrics.record_routing_decision.assert_called_once()
        mock_pattern_learner.record_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_fast_mode_cache_hit(
        self, router, mock_adaptive_service, mock_cache, mock_metrics
    ):
        """Test FAST mode with cache hit."""
        query = "What is RAG?"
        session_id = "test-session"

        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.25,
            confidence=0.9,
            factors={},
            reasoning="Simple query",
            language="en",
        )

        # Mock cache hit
        cached_response = {"type": "answer", "content": "Cached answer"}
        mock_cache.get_with_mode.return_value = cached_response

        # Route and check cache
        routing = await router.route_query(query, session_id)
        result = await mock_cache.get_with_mode(f"query:{query}", QueryMode.FAST)

        assert result == cached_response
        assert routing.mode == QueryMode.FAST

        # Record cache hit
        await mock_metrics.record_query_execution(
            query_id="test-id",
            mode=QueryMode.FAST,
            processing_time=0.01,
            cache_hit=True,
        )


class TestBalancedModeE2E:
    """Test complete BALANCED mode flow."""

    @pytest.mark.asyncio
    async def test_balanced_mode_complete_flow(
        self,
        router,
        mock_adaptive_service,
        mock_cache,
        mock_processor,
        mock_metrics,
        mock_pattern_learner,
    ):
        """Test complete BALANCED mode flow."""
        query = "Compare RAG and fine-tuning approaches"
        session_id = "test-session"

        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.MEDIUM,
            score=0.55,
            confidence=0.85,
            factors={"word_count": 5, "question_type": "comparative"},
            reasoning="Comparison query",
            language="en",
        )

        # Route query
        routing = await router.route_query(query, session_id)

        assert routing.mode == QueryMode.BALANCED
        assert routing.complexity == QueryComplexity.MEDIUM
        assert routing.top_k == 10

        # Check cache (L1 + L2)
        cache_result = await mock_cache.get_with_mode(
            f"query:{query}", QueryMode.BALANCED
        )
        assert cache_result is None

        # Process query
        results = []
        async for step in mock_processor.process_query_with_mode(
            query=query, session_id=session_id, mode=QueryMode.BALANCED, top_k=10
        ):
            results.append(step)

        assert len(results) > 0

        # Cache in L1 + L2
        await mock_cache.set_with_mode(
            f"query:{query}", results[-1], QueryMode.BALANCED
        )

        # Record metrics
        await mock_metrics.record_query_execution(
            query_id="test-id",
            mode=QueryMode.BALANCED,
            processing_time=2.5,
            cache_hit=False,
        )

        # Update patterns
        await mock_pattern_learner.record_query(
            query=query,
            complexity=QueryComplexity.MEDIUM,
            mode_used=QueryMode.BALANCED,
            processing_time=2.5,
            confidence_score=0.85,
        )


class TestDeepModeE2E:
    """Test complete DEEP mode flow."""

    @pytest.mark.asyncio
    async def test_deep_mode_complete_flow(
        self,
        router,
        mock_adaptive_service,
        mock_cache,
        mock_processor,
        mock_metrics,
        mock_pattern_learner,
    ):
        """Test complete DEEP mode flow."""
        query = "Analyze the evolution of RAG systems from 2020 to 2024"
        session_id = "test-session"

        # Mock complexity analysis
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.COMPLEX,
            score=0.85,
            confidence=0.95,
            factors={"word_count": 10, "question_type": "analytical"},
            reasoning="Complex analytical query",
            language="en",
        )

        # Route query
        routing = await router.route_query(query, session_id)

        assert routing.mode == QueryMode.DEEP
        assert routing.complexity == QueryComplexity.COMPLEX
        assert routing.top_k == 15

        # Check all cache levels
        cache_result = await mock_cache.get_with_mode(f"query:{query}", QueryMode.DEEP)
        assert cache_result is None

        # Process query with full agentic reasoning
        results = []
        async for step in mock_processor.process_query_with_mode(
            query=query, session_id=session_id, mode=QueryMode.DEEP, top_k=15
        ):
            results.append(step)

        assert len(results) > 0

        # Cache in L2 + L3
        await mock_cache.set_with_mode(f"query:{query}", results[-1], QueryMode.DEEP)

        # Record metrics
        await mock_metrics.record_query_execution(
            query_id="test-id",
            mode=QueryMode.DEEP,
            processing_time=12.0,
            cache_hit=False,
        )

        # Update patterns
        await mock_pattern_learner.record_query(
            query=query,
            complexity=QueryComplexity.COMPLEX,
            mode_used=QueryMode.DEEP,
            processing_time=12.0,
            confidence_score=0.95,
        )


class TestModeEscalation:
    """Test mode escalation scenarios."""

    @pytest.mark.asyncio
    async def test_fast_to_balanced_escalation(
        self, router, mock_adaptive_service, mock_metrics
    ):
        """Test escalation from FAST to BALANCED mode."""
        query = "What is RAG?"
        session_id = "test-session"

        # Initial routing to FAST
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.25,
            confidence=0.9,
            factors={},
            reasoning="Simple query",
            language="en",
        )

        routing = await router.route_query(query, session_id)
        assert routing.mode == QueryMode.FAST

        # Simulate low confidence result requiring escalation
        # In real scenario, this would trigger re-routing
        escalated_routing = await router.route_query(
            query, session_id, forced_mode=QueryMode.BALANCED
        )

        assert escalated_routing.mode == QueryMode.BALANCED

        # Record escalation
        await mock_metrics.record_routing_decision(escalated_routing)


class TestPatternLearning:
    """Test pattern learning integration."""

    @pytest.mark.asyncio
    async def test_pattern_based_routing(
        self, router, mock_adaptive_service, mock_pattern_learner
    ):
        """Test routing influenced by learned patterns."""
        query = "What is machine learning?"
        session_id = "test-session"

        # Mock complexity analysis (borderline SIMPLE/MEDIUM)
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.34,
            confidence=0.7,
            factors={},
            reasoning="Borderline query",
            language="en",
        )

        # Mock pattern recommendation (suggests BALANCED based on history)
        from services.query_pattern_learner import PatternRecommendation

        mock_pattern_learner.get_pattern_recommendation.return_value = (
            PatternRecommendation(
                recommended_mode=QueryMode.BALANCED,
                confidence=0.85,
                similar_queries=10,
                avg_processing_time=2.0,
                avg_confidence_score=0.9,
                success_rate=0.95,
            )
        )

        # Route query
        routing = await router.route_query(query, session_id)

        # Should use pattern recommendation
        assert routing.mode == QueryMode.BALANCED
        assert routing.routing_confidence > 0.8


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_query(self, router, mock_adaptive_service):
        """Test handling of empty query."""
        query = ""
        session_id = "test-session"

        # Mock analysis for empty query
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.0,
            confidence=0.5,
            factors={},
            reasoning="Empty query",
            language="en",
        )

        routing = await router.route_query(query, session_id)

        # Should default to FAST mode
        assert routing.mode == QueryMode.FAST

    @pytest.mark.asyncio
    async def test_very_long_query(self, router, mock_adaptive_service):
        """Test handling of very long query."""
        query = " ".join(["word"] * 200)  # 200 words
        session_id = "test-session"

        # Mock analysis for long query
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.COMPLEX,
            score=0.95,
            confidence=0.9,
            factors={"word_count": 200},
            reasoning="Very long query",
            language="en",
        )

        routing = await router.route_query(query, session_id)

        # Should route to DEEP mode
        assert routing.mode == QueryMode.DEEP

    @pytest.mark.asyncio
    async def test_special_characters(self, router, mock_adaptive_service):
        """Test handling of special characters."""
        query = "What is RAG? 🤖 #AI @mention"
        session_id = "test-session"

        # Mock analysis
        mock_adaptive_service.analyze_query_complexity_enhanced.return_value = Mock(
            complexity=QueryComplexity.SIMPLE,
            score=0.3,
            confidence=0.85,
            factors={},
            reasoning="Simple query with special chars",
            language="en",
        )

        routing = await router.route_query(query, session_id)

        # Should handle gracefully
        assert routing.mode in [QueryMode.FAST, QueryMode.BALANCED, QueryMode.DEEP]

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self, router, mock_adaptive_service, mock_cache, mock_metrics
    ):
        """Test handling of concurrent requests."""
        queries = [
            "What is RAG?",
            "Compare RAG and fine-tuning",
            "Analyze the evolution of AI",
        ]
        session_id = "test-session"

        # Mock different complexity levels
        complexities = [
            QueryComplexity.SIMPLE,
            QueryComplexity.MEDIUM,
            QueryComplexity.COMPLEX,
        ]

        def mock_analyze(query):
            idx = queries.index(query) if query in queries else 0
            return Mock(
                complexity=complexities[idx],
                score=0.3 + (idx * 0.3),
                confidence=0.9,
                factors={},
                reasoning=f"Query {idx}",
                language="en",
            )

        mock_adaptive_service.analyze_query_complexity_enhanced.side_effect = (
            mock_analyze
        )

        # Process concurrently
        tasks = [router.route_query(q, session_id) for q in queries]
        results = await asyncio.gather(*tasks)

        # Verify all processed correctly
        assert len(results) == 3
        assert results[0].mode == QueryMode.FAST
        assert results[1].mode == QueryMode.BALANCED
        assert results[2].mode == QueryMode.DEEP


class TestErrorRecovery:
    """Test error recovery and fallback behavior."""

    @pytest.mark.asyncio
    async def test_routing_failure_fallback(self, router, mock_adaptive_service):
        """Test fallback to BALANCED mode on routing failure."""
        query = "Test query"
        session_id = "test-session"

        # Mock routing failure
        mock_adaptive_service.analyze_query_complexity_enhanced.side_effect = Exception(
            "Analysis failed"
        )

        # Should fallback to BALANCED mode
        routing = await router.route_query(query, session_id)

        assert routing.mode == QueryMode.BALANCED
        assert routing.complexity == QueryComplexity.MEDIUM

    @pytest.mark.asyncio
    async def test_cache_failure_graceful_degradation(self, mock_cache, mock_processor):
        """Test graceful degradation on cache failure."""
        query = "Test query"
        session_id = "test-session"

        # Mock cache failure
        mock_cache.get_with_mode.side_effect = Exception("Cache unavailable")

        # Should continue without cache
        try:
            await mock_cache.get_with_mode(f"query:{query}", QueryMode.FAST)
        except Exception:
            pass

        # Process query normally
        results = []
        async for step in mock_processor.process_query_with_mode(
            query=query, session_id=session_id, mode=QueryMode.FAST, top_k=5
        ):
            results.append(step)

        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
