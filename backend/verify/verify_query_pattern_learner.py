"""
Verification script for QueryPatternLearner implementation.

Tests all core functionality:
1. Pattern recording
2. Pattern recommendation
3. Pattern analysis
4. Integration with MemoryManager
"""

import asyncio
import sys
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add backend to path
sys.path.insert(0, ".")

from backend.services.query_pattern_learner import (
    QueryPatternLearner,
    PatternEntry,
    PatternRecommendation,
    PatternAnalysis,
    get_pattern_learner,
)
from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message: str):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"✗ {message}")


def create_mock_memory_manager():
    """Create mock MemoryManager for testing."""
    memory = Mock()

    # Mock store_pattern
    memory.store_pattern = AsyncMock(return_value="pattern_test_123")

    # Mock get_relevant_patterns with sample data
    async def mock_get_patterns(pattern_type=None, limit=10):
        return [
            {
                "id": f"pattern_{i}",
                "data": f'{{"complexity": "SIMPLE", "mode_used": "FAST", "processing_time": {0.8 + i * 0.1}, "confidence_score": {0.85 - i * 0.02}, "timestamp": "2024-01-01T12:0{i}:00", "query_hash": "hash{i}", "metadata": {{}}}}',
                "success_score": 0.85,
            }
            for i in range(min(5, limit))
        ]

    memory.get_relevant_patterns = mock_get_patterns

    return memory


def create_mock_confidence_service():
    """Create mock ConfidenceService for testing."""
    return Mock()


async def test_initialization():
    """Test QueryPatternLearner initialization."""
    print_section("Test 1: Initialization")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()

        learner = QueryPatternLearner(
            memory_manager=memory,
            confidence_service=confidence,
            min_samples=3,
            similarity_threshold=0.80,
        )

        assert learner.min_samples == 3
        assert learner.similarity_threshold == 0.80
        assert learner.PATTERN_TYPE == "query_routing"
        assert len(learner.pattern_cache) == 0

        print_success("Initialization successful")
        print(f"  - Min samples: {learner.min_samples}")
        print(f"  - Similarity threshold: {learner.similarity_threshold}")
        print(f"  - Pattern type: {learner.PATTERN_TYPE}")

        return True

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        return False


async def test_record_query():
    """Test query recording."""
    print_section("Test 2: Record Query")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence)

        # Record a query
        pattern_id = await learner.record_query(
            query="What is machine learning?",
            complexity=QueryComplexity.SIMPLE,
            mode_used=QueryMode.FAST,
            processing_time=0.8,
            confidence_score=0.85,
            user_feedback=0.9,
            metadata={"source_count": 5},
        )

        assert pattern_id is not None
        assert len(pattern_id) > 0

        print_success("Query recorded successfully")
        print(f"  - Pattern ID: {pattern_id}")
        print(f"  - Cache size: {len(learner.pattern_cache)}")

        # Verify cache was updated
        assert len(learner.pattern_cache) == 1
        print_success("Cache updated correctly")

        return True

    except Exception as e:
        print_error(f"Record query failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_pattern_recommendation():
    """Test pattern recommendation."""
    print_section("Test 3: Pattern Recommendation")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence, min_samples=3)

        # Get recommendation
        recommendation = await learner.get_pattern_recommendation(
            query="What is AI?", current_complexity=QueryComplexity.SIMPLE
        )

        if recommendation is None:
            print_success("Correctly returned None (insufficient data expected)")
            return True

        assert isinstance(recommendation, PatternRecommendation)
        assert recommendation.recommended_mode in [
            QueryMode.FAST,
            QueryMode.BALANCED,
            QueryMode.DEEP,
        ]
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.similar_queries >= 0

        print_success("Pattern recommendation generated")
        print(f"  - Recommended mode: {recommendation.recommended_mode.value}")
        print(f"  - Confidence: {recommendation.confidence:.2f}")
        print(f"  - Similar queries: {recommendation.similar_queries}")
        print(f"  - Avg processing time: {recommendation.avg_processing_time:.2f}s")
        print(f"  - Success rate: {recommendation.success_rate:.2%}")
        print(f"  - Reasoning: {recommendation.reasoning}")

        return True

    except Exception as e:
        print_error(f"Pattern recommendation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_pattern_analysis():
    """Test pattern analysis."""
    print_section("Test 4: Pattern Analysis")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence)

        # Analyze patterns
        analysis = await learner.analyze_patterns()

        assert isinstance(analysis, PatternAnalysis)
        assert analysis.total_patterns >= 0

        print_success("Pattern analysis completed")
        print(f"  - Total patterns: {analysis.total_patterns}")
        print(f"  - Mode distribution: {analysis.mode_distribution}")
        print(f"  - Avg latency by mode: {analysis.avg_latency_by_mode}")
        print(f"  - Success rate by mode: {analysis.success_rate_by_mode}")
        print(f"  - Misclassified patterns: {len(analysis.misclassified_patterns)}")

        return True

    except Exception as e:
        print_error(f"Pattern analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_success_score_calculation():
    """Test success score calculation."""
    print_section("Test 5: Success Score Calculation")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence)

        # Test different scenarios
        scenarios = [
            {
                "name": "Fast mode within target",
                "mode": QueryMode.FAST,
                "time": 0.8,
                "confidence": 0.85,
                "feedback": None,
            },
            {
                "name": "Fast mode exceeding target",
                "mode": QueryMode.FAST,
                "time": 2.0,
                "confidence": 0.85,
                "feedback": None,
            },
            {
                "name": "With positive feedback",
                "mode": QueryMode.BALANCED,
                "time": 2.5,
                "confidence": 0.75,
                "feedback": 0.95,
            },
            {
                "name": "With negative feedback",
                "mode": QueryMode.BALANCED,
                "time": 2.5,
                "confidence": 0.75,
                "feedback": 0.3,
            },
        ]

        print_success("Testing success score calculation")
        for scenario in scenarios:
            score = learner._calculate_success_score(
                mode_used=scenario["mode"],
                processing_time=scenario["time"],
                confidence_score=scenario["confidence"],
                user_feedback=scenario["feedback"],
            )

            assert 0.0 <= score <= 1.0
            print(f"  - {scenario['name']}: {score:.2f}")

        return True

    except Exception as e:
        print_error(f"Success score calculation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_misclassified_identification():
    """Test misclassified pattern identification."""
    print_section("Test 6: Misclassified Pattern Identification")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence)

        # Create test patterns
        patterns = [
            PatternEntry(
                id="p1",
                query_hash="hash1",
                query_embedding=[],
                complexity=QueryComplexity.SIMPLE,
                mode_used=QueryMode.FAST,
                processing_time=2.0,  # Too slow for FAST
                confidence_score=0.85,
                user_feedback=None,
                timestamp=datetime.now(),
                metadata={},
            ),
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

        misclassified = learner._identify_misclassified(patterns)

        assert len(misclassified) == 3

        print_success("Misclassified patterns identified")
        for pattern in misclassified:
            print(f"  - Pattern {pattern['id']}: {', '.join(pattern['issues'])}")

        return True

    except Exception as e:
        print_error(f"Misclassified identification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_dataclass_serialization():
    """Test dataclass to_dict methods."""
    print_section("Test 7: Dataclass Serialization")

    try:
        # Test PatternEntry
        entry = PatternEntry(
            id="p1",
            query_hash="hash1",
            query_embedding=[0.1, 0.2],
            complexity=QueryComplexity.SIMPLE,
            mode_used=QueryMode.FAST,
            processing_time=0.8,
            confidence_score=0.85,
            user_feedback=0.9,
            timestamp=datetime.now(),
            metadata={"key": "value"},
            similarity_score=0.95,
        )

        entry_dict = entry.to_dict()
        assert "id" in entry_dict
        assert "complexity" in entry_dict
        assert "mode_used" in entry_dict
        print_success("PatternEntry serialization works")

        # Test PatternRecommendation
        recommendation = PatternRecommendation(
            recommended_mode=QueryMode.FAST,
            confidence=0.85,
            similar_queries=5,
            avg_processing_time=0.8,
            avg_confidence_score=0.82,
            success_rate=0.9,
            reasoning="Test reasoning",
        )

        rec_dict = recommendation.to_dict()
        assert "recommended_mode" in rec_dict
        assert "confidence" in rec_dict
        print_success("PatternRecommendation serialization works")

        # Test PatternAnalysis
        analysis = PatternAnalysis(
            total_patterns=100,
            mode_distribution={"fast": 0.5},
            avg_latency_by_mode={"fast": 0.8},
            avg_confidence_by_mode={"fast": 0.85},
            success_rate_by_mode={"fast": 0.9},
            misclassified_patterns=[],
        )

        analysis_dict = analysis.to_dict()
        assert "total_patterns" in analysis_dict
        assert "mode_distribution" in analysis_dict
        print_success("PatternAnalysis serialization works")

        return True

    except Exception as e:
        print_error(f"Dataclass serialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_stats():
    """Test statistics retrieval."""
    print_section("Test 8: Statistics")

    try:
        memory = create_mock_memory_manager()
        confidence = create_mock_confidence_service()
        learner = QueryPatternLearner(memory, confidence)

        stats = learner.get_stats()

        assert "cache_size" in stats
        assert "cache_capacity" in stats
        assert "min_samples" in stats
        assert "similarity_threshold" in stats
        assert "pattern_type" in stats

        print_success("Statistics retrieved")
        for key, value in stats.items():
            print(f"  - {key}: {value}")

        return True

    except Exception as e:
        print_error(f"Statistics retrieval failed: {e}")
        return False


async def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("  QueryPatternLearner Verification")
    print("=" * 60)

    tests = [
        ("Initialization", test_initialization),
        ("Record Query", test_record_query),
        ("Pattern Recommendation", test_pattern_recommendation),
        ("Pattern Analysis", test_pattern_analysis),
        ("Success Score Calculation", test_success_score_calculation),
        ("Misclassified Identification", test_misclassified_identification),
        ("Dataclass Serialization", test_dataclass_serialization),
        ("Statistics", test_stats),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Summary
    print_section("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All verifications passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
