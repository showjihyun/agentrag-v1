"""
Verification script for enhanced query complexity analysis.

Tests all requirements from Task 1:
- Weighted factor analysis
- Confidence scoring
- Korean language support
- ComplexityAnalysis object structure
"""

import sys
from backend.services.adaptive_rag_service import (
    AdaptiveRAGService,
    QueryComplexity,
    ComplexityAnalysis,
)


def test_simple_queries():
    """Test simple query classification."""
    print("\n=== Testing Simple Queries ===")
    service = AdaptiveRAGService()

    test_cases = [
        ("What is RAG?", "en"),
        ("Define machine learning", "en"),
        ("RAG가 무엇인가요?", "ko"),
    ]

    for query, lang in test_cases:
        analysis = service.analyze_query_complexity(query, language=lang)
        print(f"\nQuery: {query}")
        print(f"  Complexity: {analysis.complexity.value}")
        print(f"  Score: {analysis.score:.3f}")
        print(f"  Confidence: {analysis.confidence:.3f}")
        print(f"  Language: {analysis.language}")
        print(f"  Question Type: {analysis.question_type}")
        print(f"  Reasoning: {analysis.reasoning}")

        assert isinstance(analysis, ComplexityAnalysis)
        assert analysis.complexity == QueryComplexity.SIMPLE
        assert 0.0 <= analysis.score <= 1.0
        assert 0.0 <= analysis.confidence <= 1.0

    print("\n✓ Simple queries test passed")


def test_medium_queries():
    """Test medium complexity queries."""
    print("\n=== Testing Medium Complexity Queries ===")
    service = AdaptiveRAGService()

    test_cases = [
        ("Compare RAG and fine-tuning approaches for language models", "en"),
        (
            "Explain how semantic search works and why it's better than keyword search",
            "en",
        ),
        ("RAG와 파인튜닝의 차이점을 비교하고 각각의 장단점을 설명해주세요", "ko"),
    ]

    for query, lang in test_cases:
        analysis = service.analyze_query_complexity(query, language=lang)
        print(f"\nQuery: {query}")
        print(f"  Complexity: {analysis.complexity.value}")
        print(f"  Score: {analysis.score:.3f}")
        print(f"  Confidence: {analysis.confidence:.3f}")
        print(f"  Language: {analysis.language}")
        print(f"  Question Type: {analysis.question_type}")
        print(f"  Word Count: {analysis.word_count}")

        assert isinstance(analysis, ComplexityAnalysis)
        # Should be at least MEDIUM complexity (score >= 0.35)
        assert analysis.score >= 0.35, f"Expected score >= 0.35, got {analysis.score}"
        assert 0.0 <= analysis.score <= 1.0

    print("\n✓ Medium queries test passed")


def test_complex_queries():
    """Test complex query classification."""
    print("\n=== Testing Complex Queries ===")
    service = AdaptiveRAGService()

    test_cases = [
        (
            "Analyze and compare the historical evolution of RAG systems from 2020 to 2024, "
            "explaining why certain approaches like dense retrieval and hybrid search became dominant, "
            "while evaluating their performance characteristics, cost implications, and scalability trade-offs "
            "across different use cases and deployment scenarios",
            "en",
        ),
        (
            "2020년부터 2024년까지 RAG 시스템의 역사적 발전 과정을 분석하고 비교하면서, "
            "밀집 검색과 하이브리드 검색 같은 특정 접근 방식이 왜 지배적이 되었는지 설명하고, "
            "다양한 사용 사례와 배포 시나리오에서 성능 특성, 비용 영향, 확장성 트레이드오프를 평가해주세요",
            "ko",
        ),
    ]

    for query, lang in test_cases:
        analysis = service.analyze_query_complexity(query, language=lang)
        print(f"\nQuery: {query[:80]}...")
        print(f"  Complexity: {analysis.complexity.value}")
        print(f"  Score: {analysis.score:.3f}")
        print(f"  Confidence: {analysis.confidence:.3f}")
        print(f"  Language: {analysis.language}")
        print(f"  Question Type: {analysis.question_type}")
        print(f"  Word Count: {analysis.word_count}")

        assert isinstance(analysis, ComplexityAnalysis)
        # Should be COMPLEX (score > 0.70)
        assert analysis.score > 0.70, f"Expected score > 0.70, got {analysis.score}"

    print("\n✓ Complex queries test passed")


def test_weighted_factors():
    """Test weighted factor analysis."""
    print("\n=== Testing Weighted Factor Analysis ===")
    service = AdaptiveRAGService()

    query = "Compare and analyze the evolution of RAG systems"
    analysis = service.analyze_query_complexity(query)

    print(f"\nQuery: {query}")
    print(f"Complexity Score: {analysis.score:.3f}")
    print("\nFactor Breakdown:")

    required_factors = [
        "word_count",
        "question_type",
        "multiple_questions",
        "comparison",
        "temporal",
        "entity",
    ]

    for factor_name in required_factors:
        assert factor_name in analysis.factors, f"Missing factor: {factor_name}"
        factor = analysis.factors[factor_name]
        assert "score" in factor
        assert "weight" in factor
        print(f"  {factor_name}:")
        print(f"    Score: {factor['score']:.3f}")
        print(f"    Weight: {factor['weight']:.2f}")

    # Verify weights sum to 1.0
    total_weight = sum(f["weight"] for f in analysis.factors.values())
    print(f"\nTotal Weight: {total_weight:.2f}")
    assert abs(total_weight - 1.0) < 0.01, "Weights should sum to 1.0"

    print("\n✓ Weighted factors test passed")


def test_confidence_scoring():
    """Test confidence scoring."""
    print("\n=== Testing Confidence Scoring ===")
    service = AdaptiveRAGService()

    # Clear SIMPLE case
    simple_query = "What is AI?"
    simple_analysis = service.analyze_query_complexity(simple_query)

    # Boundary case
    boundary_query = "What is AI and how does it work?"
    boundary_analysis = service.analyze_query_complexity(boundary_query)

    # Clear COMPLEX case
    complex_query = (
        "Analyze and compare the historical evolution of artificial intelligence "
        "from 1950 to 2024, explaining why certain paradigms became dominant "
        "and evaluating their impact on modern machine learning systems"
    )
    complex_analysis = service.analyze_query_complexity(complex_query)

    print(f"\nSimple Query Confidence: {simple_analysis.confidence:.3f}")
    print(f"Boundary Query Confidence: {boundary_analysis.confidence:.3f}")
    print(f"Complex Query Confidence: {complex_analysis.confidence:.3f}")

    # Clear cases should have higher confidence
    assert simple_analysis.confidence > 0.6
    assert complex_analysis.confidence > 0.6

    print("\n✓ Confidence scoring test passed")


def test_korean_language_support():
    """Test Korean language support."""
    print("\n=== Testing Korean Language Support ===")
    service = AdaptiveRAGService()

    test_cases = [
        ("RAG가 무엇인가요?", "factual"),
        ("RAG와 파인튜닝을 비교해주세요", "comparative"),
        ("RAG 시스템의 발전을 분석해주세요", "analytical"),
    ]

    for query, expected_type in test_cases:
        analysis = service.analyze_query_complexity(query, language="ko")
        print(f"\nQuery: {query}")
        print(f"  Language: {analysis.language}")
        print(f"  Question Type: {analysis.question_type}")
        print(f"  Complexity: {analysis.complexity.value}")

        assert analysis.language == "ko"
        assert isinstance(analysis.complexity, QueryComplexity)

    print("\n✓ Korean language support test passed")


def test_complexity_analysis_object():
    """Test ComplexityAnalysis object structure."""
    print("\n=== Testing ComplexityAnalysis Object Structure ===")
    service = AdaptiveRAGService()

    query = "Compare RAG and fine-tuning"
    analysis = service.analyze_query_complexity(query)

    print(f"\nQuery: {query}")
    print("\nComplexityAnalysis attributes:")

    # Check all required attributes
    required_attrs = [
        "complexity",
        "score",
        "confidence",
        "factors",
        "reasoning",
        "language",
        "word_count",
        "question_type",
        "timestamp",
    ]

    for attr in required_attrs:
        assert hasattr(analysis, attr), f"Missing attribute: {attr}"
        value = getattr(analysis, attr)
        print(f"  {attr}: {value if attr != 'factors' else '...'}")

    # Verify types
    assert isinstance(analysis.complexity, QueryComplexity)
    assert isinstance(analysis.score, float)
    assert isinstance(analysis.confidence, float)
    assert isinstance(analysis.factors, dict)
    assert isinstance(analysis.reasoning, str)
    assert isinstance(analysis.language, str)
    assert isinstance(analysis.word_count, int)
    assert isinstance(analysis.question_type, str)

    print("\n✓ ComplexityAnalysis object structure test passed")


def test_get_adaptive_config():
    """Test get_adaptive_config with enhanced analysis."""
    print("\n=== Testing get_adaptive_config ===")
    service = AdaptiveRAGService()

    query = "Compare RAG and fine-tuning approaches"
    config = service.get_adaptive_config(query)

    print(f"\nQuery: {query}")
    print("\nConfiguration:")
    print(f"  Complexity: {config['complexity']}")
    print(f"  Complexity Score: {config['complexity_score']:.3f}")
    print(f"  Confidence: {config['confidence']:.3f}")
    print(f"  Strategy: {config['strategy']}")

    # Check enhanced fields
    assert "complexity_score" in config
    assert "confidence" in config
    assert "complexity_analysis" in config

    analysis = config["complexity_analysis"]
    assert "factors" in analysis
    assert "reasoning" in analysis
    assert "language" in analysis
    assert "question_type" in analysis

    print("\n✓ get_adaptive_config test passed")


def test_edge_cases():
    """Test edge cases."""
    print("\n=== Testing Edge Cases ===")
    service = AdaptiveRAGService()

    # Empty query
    try:
        analysis = service.analyze_query_complexity("")
        print(f"\nEmpty query: {analysis.complexity.value}")
        assert analysis.word_count == 0
    except Exception as e:
        print(f"\nEmpty query error (acceptable): {e}")

    # Very long query
    long_query = " ".join(["word"] * 50)
    analysis = service.analyze_query_complexity(long_query)
    print(f"Long query (50 words): {analysis.complexity.value}")
    assert analysis.word_count == 50

    # Special characters
    special_query = "What is RAG? (Retrieval-Augmented Generation)"
    analysis = service.analyze_query_complexity(special_query)
    print(f"Special characters: {analysis.complexity.value}")

    # Mixed language
    mixed_query = "What is 머신러닝?"
    analysis = service.analyze_query_complexity(mixed_query)
    print(f"Mixed language: {analysis.language}")
    assert analysis.language == "mixed"

    print("\n✓ Edge cases test passed")


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("ENHANCED QUERY COMPLEXITY ANALYSIS VERIFICATION")
    print("=" * 70)

    try:
        test_simple_queries()
        test_medium_queries()
        test_complex_queries()
        test_weighted_factors()
        test_confidence_scoring()
        test_korean_language_support()
        test_complexity_analysis_object()
        test_get_adaptive_config()
        test_edge_cases()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nTask 1: Enhance Query Complexity Analysis - COMPLETE")
        print("\nImplemented features:")
        print("  ✓ Weighted factor analysis (6 factors)")
        print("  ✓ Confidence scoring for classifications")
        print("  ✓ Korean language support")
        print("  ✓ Detailed ComplexityAnalysis object")
        print("  ✓ Enhanced reasoning generation")
        print("=" * 70)

        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
