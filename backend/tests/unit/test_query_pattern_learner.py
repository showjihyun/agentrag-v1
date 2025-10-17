"""
Unit tests for QueryPatternLearner
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from backend.services.query_pattern_learner import (
    QueryPatternLearner,
    PatternEntry,
    PatternRecommendation,
    PatternAnalysis,
)
from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity


@pytest.fixture
def mock_memory_manager():
    """Create mock MemoryManager."""
    memory = Mock()
    memory.store_pattern = AsyncMock(return_value="pattern_123")
    memory.get_relevant_patterns = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def mock_confidence_service():
    """Create mock ConfidenceService."""
    return Mock()


@pytest.fixture
def pattern_learner(mock_memory_manager, mock_confidence_service):
    """Create QueryPatternLearner instance."""
    return QueryPatternLearner(
        memory_manager=mock_memory_manager,
        confidence_service=mock_confidence_service,
        min_samples=3,
        similarity_threshold=0.80,
    )


class TestQueryPatternLearner:
    """Test QueryPatternLearner class."""

    def test_initialization(self, pattern_learner):
        """Test proper initialization."""
        assert pattern_learner.min_samples == 3
        assert pattern_learner.similarity_threshold == 0.80
        assert pattern_learner.PATTERN_TYPE == "query_routing"
        assert len(pattern_learner.pattern_cache) == 0

    def test_initialization_validation(
        self, mock_memory_manager, mock_confidence_service
    ):
        """Test initialization parameter validation."""
        # Test None memory_manager
        with pytest.raises(ValueError, match="memory_manager cannot be None"):
            QueryPatternLearner(None, mock_confidence_service)

        # Test None confidence_service
        with pytest.raises(ValueError, match="confidence_service cannot be None"):
            QueryPatternLearner(mock_memory_manager, None)

        # Test invalid min_samples
        with pytest.raises(ValueError, match="min_samples must be at least 1"):
            QueryPatternLearner(
                mock_memory_manager, mock_confidence_service, min_samples=0
            )

        # Test invalid similarity_threshold
        with pytest.raises(
            ValueError, match="similarity_threshold must be between 0 and 1"
        ):
            QueryPatternLearner(
                mock_memory_manager, mock_confidence_service, similarity_threshold=1.5
            )

    def test_hash_query(self, pattern_learner):
        """Test query hashing."""
        query1 = "What is machine learning?"
        query2 = "What is machine learning?"
        query3 = "What is deep learning?"

        hash1 = pattern_learner._hash_query(query1)
        hash2 = pattern_learner._hash_query(query2)
        hash3 = pattern_learner._hash_query(query3)

        # Same query should produce same hash
        assert hash1 == hash2

        # Different query should produce different hash
        assert hash1 != hash3

        # Hash should be 16 characters
        assert len(hash1) == 16

    @pytest.mark.asyncio
    async def test_record_query_success(self, pattern_learner, mock_memory_manager):
        """Test successful query recording."""
        query = "What is RAG?"
        complexity = QueryComplexity.SIMPLE
        mode = QueryMode.FAST
        processing_time = 0.8
        confidence_score = 0.85

        pattern_id = await pattern_learner.record_query(
            query=query,
            complexity=complexity,
            mode_used=mode,
            processing_time=processing_time,
            confidence_score=confidence_score,
        )

        # Should return pattern ID
        assert pattern_id == "pattern_123"

        # Should call memory.store_pattern
        mock_memory_manager.store_pattern.assert_called_once()
        call_args = mock_memory_manager.store_pattern.call_args

        assert call_args[1]["pattern_type"] == "query_routing"
        assert "complexity" in call_args[1]["pattern_data"]
        assert "mode_used" in call_args[1]["pattern_data"]

        # Should update cache
        assert len(pattern_learner.pattern_cache) == 1

    @pytest.mark.asyncio
    async def test_record_query_with_feedback(self, pattern_learner):
        """Test recording query with user feedback."""
        pattern_id = await pattern_learner.record_query(
            query="Compare RAG and fine-tuning",
            complexity=QueryComplexity.MEDIUM,
            mode_used=QueryMode.BALANCED,
            processing_time=2.5,
            confidence_score=0.75,
            user_feedback=0.9,
        )

        assert pattern_id is not None

    @pytest.mark.asyncio
    async def test_record_query_validation(self, pattern_learner):
        """Test query recording parameter validation."""
        # Empty query
        with pytest.raises(ValueError, match="query cannot be empty"):
            await pattern_learner.record_query(
                query="",
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=1.0,
                confidence_score=0.8,
            )

        # Negative processing time
        with pytest.raises(ValueError, match="processing_time must be non-negative"):
            await pattern_learner.record_query(
                query="test",
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=-1.0,
                confidence_score=0.8,
            )

        # Invalid confidence score
        with pytest.raises(
            ValueError, match="confidence_score must be between 0 and 1"
        ):
            await pattern_learner.record_query(
                query="test",
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=1.0,
                confidence_score=1.5,
            )

        # Invalid user feedback
        with pytest.raises(ValueError, match="user_feedback must be between 0 and 1"):
            await pattern_learner.record_query(
                query="test",
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=1.0,
                confidence_score=0.8,
                user_feedback=2.0,
            )

    def test_calculate_success_score(self, pattern_learner):
        """Test success score calculation."""
        # Fast mode within target
        score1 = pattern_learner._calculate_success_score(
            mode_used=QueryMode.FAST,
            processing_time=0.8,
            confidence_score=0.85,
            user_feedback=None,
        )
        assert 0.0 <= score1 <= 1.0
        assert score1 > 0.7  # Should be high

        # Fast mode exceeding target
        score2 = pattern_learner._calculate_success_score(
            mode_used=QueryMode.FAST,
            processing_time=2.0,
            confidence_score=0.85,
            user_feedback=None,
        )
        assert score2 < score1  # Should be lower

        # With positive user feedback
        score3 = pattern_learner._calculate_success_score(
            mode_used=QueryMode.BALANCED,
            processing_time=2.5,
            confidence_score=0.75,
            user_feedback=0.95,
        )
        assert score3 > 0.8  # Should be high with good feedback

        # With negative user feedback
        score4 = pattern_learner._calculate_success_score(
            mode_used=QueryMode.BALANCED,
            processing_time=2.5,
            confidence_score=0.75,
            user_feedback=0.3,
        )
        assert score4 < score3  # Should be lower

    @pytest.mark.asyncio
    async def test_get_pattern_recommendation_insufficient_data(
        self, pattern_learner, mock_memory_manager
    ):
        """Test recommendation with insufficient data."""
        # Return only 2 patterns (less than min_samples=3)
        mock_memory_manager.get_relevant_patterns.return_value = [
            {
                "id": "p1",
                "data": '{"complexity": "SIMPLE", "mode_used": "FAST", "processing_time": 0.8, "confidence_score": 0.85, "timestamp": "2024-01-01T12:00:00"}',
                "success_score": 0.9,
            },
            {
                "id": "p2",
                "data": '{"complexity": "SIMPLE", "mode_used": "FAST", "processing_time": 0.9, "confidence_score": 0.82, "timestamp": "2024-01-01T12:01:00"}',
                "success_score": 0.88,
            },
        ]

        recommendation = await pattern_learner.get_pattern_recommendation(
            query="What is AI?", current_complexity=QueryComplexity.SIMPLE
        )

        # Should return None due to insufficient data
        assert recommendation is None

    @pytest.mark.asyncio
    async def test_get_pattern_recommendation_success(
        self, pattern_learner, mock_memory_manager
    ):
        """Test successful pattern recommendation."""
        # Return sufficient patterns
        mock_memory_manager.get_relevant_patterns.return_value = [
            {
                "id": f"p{i}",
                "data": f'{{"complexity": "SIMPLE", "mode_used": "FAST", "processing_time": 0.{8+i}, "confidence_score": 0.8{i}, "timestamp": "2024-01-01T12:0{i}:00", "query_hash": "hash{i}", "metadata": {{}}}}',
                "success_score": 0.85,
            }
            for i in range(5)
        ]

        recommendation = await pattern_learner.get_pattern_recommendation(
            query="What is AI?", current_complexity=QueryComplexity.SIMPLE
        )

        # Should return recommendation
        assert recommendation is not None
        assert isinstance(recommendation, PatternRecommendation)
        assert recommendation.recommended_mode in [
            QueryMode.FAST,
            QueryMode.BALANCED,
            QueryMode.DEEP,
        ]
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.similar_queries >= 3
        assert recommendation.reasoning != ""

    def test_analyze_mode_performance(self, pattern_learner):
        """Test mode performance analysis."""
        patterns = [
            PatternEntry(
                id=f"p{i}",
                query_hash=f"hash{i}",
                query_embedding=[],
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=0.8 + i * 0.1,
                confidence_score=0.85 - i * 0.05,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
            )
            for i in range(3)
        ]

        performance = pattern_learner._analyze_mode_performance(patterns)

        assert QueryMode.FAST in performance
        assert performance[QueryMode.FAST]["count"] == 3
        assert "avg_time" in performance[QueryMode.FAST]
        assert "avg_confidence" in performance[QueryMode.FAST]
        assert "success_rate" in performance[QueryMode.FAST]

    def test_calculate_mode_score(self, pattern_learner):
        """Test mode score calculation."""
        performance = {
            "count": 5,
            "avg_time": 1.0,
            "avg_confidence": 0.85,
            "success_rate": 0.9,
            "patterns": [],
        }

        score = pattern_learner._calculate_mode_score(performance)

        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high for good performance

    def test_calculate_recommendation_confidence(self, pattern_learner):
        """Test recommendation confidence calculation."""
        similar_patterns = [
            PatternEntry(
                id=f"p{i}",
                query_hash=f"hash{i}",
                query_embedding=[],
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=0.8,
                confidence_score=0.85,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
                similarity_score=0.9,
            )
            for i in range(10)
        ]

        best_performance = {
            "count": 10,
            "avg_time": 0.8,
            "avg_confidence": 0.85,
            "success_rate": 0.95,
        }

        all_performance = {QueryMode.FAST: best_performance}

        confidence = pattern_learner._calculate_recommendation_confidence(
            similar_patterns=similar_patterns,
            best_performance=best_performance,
            all_performance=all_performance,
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high with good data

    def test_generate_reasoning(self, pattern_learner):
        """Test reasoning generation."""
        performance = {
            "count": 5,
            "avg_time": 1.2,
            "avg_confidence": 0.85,
            "success_rate": 0.9,
        }

        reasoning = pattern_learner._generate_reasoning(
            best_mode=QueryMode.FAST,
            performance=performance,
            similar_count=5,
            current_complexity=QueryComplexity.SIMPLE,
        )

        assert "5 similar queries" in reasoning
        assert "fast mode" in reasoning.lower()
        assert "90.0%" in reasoning or "90%" in reasoning
        assert "SIMPLE" in reasoning

    @pytest.mark.asyncio
    async def test_analyze_patterns(self, pattern_learner, mock_memory_manager):
        """Test pattern analysis."""
        # Mock patterns
        mock_memory_manager.get_relevant_patterns.return_value = [
            {
                "id": f"p{i}",
                "data": f'{{"complexity": "SIMPLE", "mode_used": "FAST", "processing_time": 0.8, "confidence_score": 0.85, "timestamp": "2024-01-01T12:00:00", "query_hash": "hash{i}", "metadata": {{}}}}',
                "success_score": 0.85,
            }
            for i in range(10)
        ]

        analysis = await pattern_learner.analyze_patterns()

        assert isinstance(analysis, PatternAnalysis)
        assert analysis.total_patterns == 10
        assert len(analysis.mode_distribution) > 0
        assert "fast" in analysis.mode_distribution

    def test_identify_misclassified(self, pattern_learner):
        """Test misclassified pattern identification."""
        patterns = [
            # FAST mode that took too long
            PatternEntry(
                id="p1",
                query_hash="hash1",
                query_embedding=[],
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=2.0,  # Exceeds MAX_PROCESSING_TIME_FAST
                confidence_score=0.85,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
            ),
            # DEEP mode that was too fast
            PatternEntry(
                id="p2",
                query_hash="hash2",
                query_embedding=[],
                complexity=QueryComplexity.COMPLEX,
                mode_used=QueryMode.DEEP,
                processing_time=2.0,  # Too fast for DEEP
                confidence_score=0.85,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
            ),
            # High confidence but low feedback
            PatternEntry(
                id="p3",
                query_hash="hash3",
                query_embedding=[],
                complexity=QueryComplexity.MEDIUM,
                mode_used=QueryMode.BALANCED,
                processing_time=2.5,
                confidence_score=0.85,
                user_feedback=0.3,  # Low feedback
                timestamp=datetime.now(),
                metadata={},
            ),
        ]

        misclassified = pattern_learner._identify_misclassified(patterns)

        assert len(misclassified) == 3
        assert all("issues" in m for m in misclassified)

    def test_update_cache(self, pattern_learner):
        """Test cache update."""
        pattern = PatternEntry(
            id="p1",
            query_hash="hash1",
            query_embedding=[],
            complexity=QueryComplexity.SIMPLE,
            mode_used=QueryMode.FAST,
            processing_time=0.8,
            confidence_score=0.85,
            user_feedback=None,
            timestamp=datetime.now(),
            metadata={},
        )

        pattern_learner._update_cache("p1", pattern)

        assert len(pattern_learner.pattern_cache) == 1
        assert "p1" in pattern_learner.pattern_cache

    def test_cache_eviction(self, pattern_learner):
        """Test cache eviction when full."""
        # Set small cache size
        pattern_learner.cache_size = 3

        # Add patterns
        for i in range(5):
            pattern = PatternEntry(
                id=f"p{i}",
                query_hash=f"hash{i}",
                query_embedding=[],
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=0.8,
                confidence_score=0.85,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
            )
            pattern_learner._update_cache(f"p{i}", pattern)

        # Cache should not exceed size
        assert len(pattern_learner.pattern_cache) <= pattern_learner.cache_size

    def test_get_stats(self, pattern_learner):
        """Test statistics retrieval."""
        stats = pattern_learner.get_stats()

        assert "cache_size" in stats
        assert "cache_capacity" in stats
        assert "min_samples" in stats
        assert "similarity_threshold" in stats
        assert "pattern_type" in stats

        assert stats["min_samples"] == 3
        assert stats["similarity_threshold"] == 0.80
        assert stats["pattern_type"] == "query_routing"

    def test_repr(self, pattern_learner):
        """Test string representation."""
        repr_str = repr(pattern_learner)

        assert "QueryPatternLearner" in repr_str
        assert "min_samples=3" in repr_str
        assert "similarity_threshold=0.8" in repr_str


class TestPatternEntry:
    """Test PatternEntry dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = PatternEntry(
            id="p1",
            query_hash="hash1",
            query_embedding=[0.1, 0.2],
            complexity=QueryComplexity.SIMPLE,
            mode_used=QueryMode.FAST,
            processing_time=0.8,
            confidence_score=0.85,
            user_feedback=0.9,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            metadata={"key": "value"},
            similarity_score=0.95,
        )

        data = entry.to_dict()

        assert data["id"] == "p1"
        assert data["query_hash"] == "hash1"
        assert data["complexity"] == "SIMPLE"
        assert data["mode_used"] == "fast"
        assert data["processing_time"] == 0.8
        assert data["confidence_score"] == 0.85
        assert data["user_feedback"] == 0.9
        assert data["similarity_score"] == 0.95
        assert "metadata" in data


class TestPatternRecommendation:
    """Test PatternRecommendation dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        recommendation = PatternRecommendation(
            recommended_mode=QueryMode.FAST,
            confidence=0.85,
            similar_queries=5,
            avg_processing_time=0.8,
            avg_confidence_score=0.82,
            success_rate=0.9,
            reasoning="Based on 5 similar queries",
        )

        data = recommendation.to_dict()

        assert data["recommended_mode"] == "fast"
        assert data["confidence"] == 0.85
        assert data["similar_queries"] == 5
        assert data["avg_processing_time"] == 0.8
        assert data["avg_confidence_score"] == 0.82
        assert data["success_rate"] == 0.9
        assert data["reasoning"] == "Based on 5 similar queries"


class TestPatternAnalysis:
    """Test PatternAnalysis dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        analysis = PatternAnalysis(
            total_patterns=100,
            mode_distribution={"fast": 0.5, "balanced": 0.3, "deep": 0.2},
            avg_latency_by_mode={"fast": 0.8, "balanced": 2.5, "deep": 10.0},
            avg_confidence_by_mode={"fast": 0.75, "balanced": 0.82, "deep": 0.90},
            success_rate_by_mode={"fast": 0.85, "balanced": 0.88, "deep": 0.92},
            misclassified_patterns=[],
        )

        data = analysis.to_dict()

        assert data["total_patterns"] == 100
        assert "mode_distribution" in data
        assert "avg_latency_by_mode" in data
        assert "avg_confidence_by_mode" in data
        assert "success_rate_by_mode" in data
        assert "misclassified_patterns" in data
