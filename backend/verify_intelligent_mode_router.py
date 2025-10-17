"""
Verification script for IntelligentModeRouter.

Tests routing logic, mode selection, user preferences, and error handling.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from backend.services.intelligent_mode_router import (
    IntelligentModeRouter,
    CacheStrategy,
)
from backend.services.adaptive_rag_service import AdaptiveRAGService, QueryComplexity
from backend.models.hybrid import QueryMode


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"  → {details}")


async def test_simple_query_routing():
    """Test routing of simple queries to FAST mode."""
    print_section("Test 1: Simple Query Routing")

    router = IntelligentModeRouter()

    # Test simple queries
    simple_queries = [
        "What is RAG?",
        "Define machine learning",
        "Who invented Python?",
        "When was AI created?",
    ]

    all_passed = True
    for query in simple_queries:
        decision = await router.route_query(query, "test_session")

        passed = (
            decision.mode == QueryMode.FAST
            and decision.complexity == QueryComplexity.SIMPLE
            and decision.top_k == 5
            and decision.cache_strategy == CacheStrategy.L1_ONLY
        )

        all_passed = all_passed and passed

        print_result(
            f"Simple query: '{query}'",
            passed,
            f"Mode={decision.mode.value}, Complexity={decision.complexity.value}, "
            f"Score={decision.complexity_score:.3f}, Confidence={decision.routing_confidence:.3f}",
        )

    return all_passed


async def test_medium_query_routing():
    """Test routing of medium queries to BALANCED mode."""
    print_section("Test 2: Medium Query Routing")

    router = IntelligentModeRouter()

    # Test medium queries
    medium_queries = [
        "Compare RAG and fine-tuning approaches",
        "What are the benefits of vector databases?",
        "How does semantic search work in practice?",
        "Explain the differences between embeddings and keywords",
    ]

    all_passed = True
    for query in medium_queries:
        decision = await router.route_query(query, "test_session")

        passed = (
            decision.mode == QueryMode.BALANCED
            and decision.complexity == QueryComplexity.MEDIUM
            and decision.top_k == 10
            and decision.cache_strategy == CacheStrategy.L1_L2
        )

        all_passed = all_passed and passed

        print_result(
            f"Medium query: '{query[:50]}...'",
            passed,
            f"Mode={decision.mode.value}, Complexity={decision.complexity.value}, "
            f"Score={decision.complexity_score:.3f}",
        )

    return all_passed


async def test_complex_query_routing():
    """Test routing of complex queries to DEEP mode."""
    print_section("Test 3: Complex Query Routing")

    router = IntelligentModeRouter()

    # Test complex queries
    complex_queries = [
        "Analyze the evolution of RAG systems from 2020 to 2024 and explain why certain approaches became dominant",
        "Compare and contrast three different vector database architectures, considering scalability, performance, and cost",
        "Evaluate the trade-offs between different chunking strategies and their impact on retrieval quality",
    ]

    all_passed = True
    for query in complex_queries:
        decision = await router.route_query(query, "test_session")

        passed = (
            decision.mode == QueryMode.DEEP
            and decision.complexity == QueryComplexity.COMPLEX
            and decision.top_k == 15
            and decision.cache_strategy == CacheStrategy.ALL_LEVELS
        )

        all_passed = all_passed and passed

        print_result(
            f"Complex query: '{query[:50]}...'",
            passed,
            f"Mode={decision.mode.value}, Complexity={decision.complexity.value}, "
            f"Score={decision.complexity_score:.3f}",
        )

    return all_passed


async def test_forced_mode():
    """Test forced mode override."""
    print_section("Test 4: Forced Mode Override")

    router = IntelligentModeRouter()

    # Test forcing FAST mode on medium query
    decision = await router.route_query(
        "Compare RAG and fine-tuning", "test_session", forced_mode=QueryMode.FAST
    )

    test1_passed = (
        decision.mode == QueryMode.FAST
        and decision.forced is True
        and decision.routing_confidence == 1.0
    )

    print_result(
        "Force FAST mode on medium query",
        test1_passed,
        f"Mode={decision.mode.value}, Forced={decision.forced}, "
        f"Suboptimal={decision.reasoning.get('suboptimal', False)}",
    )

    # Test forcing DEEP mode on simple query
    decision = await router.route_query(
        "What is RAG?", "test_session", forced_mode=QueryMode.DEEP
    )

    test2_passed = (
        decision.mode == QueryMode.DEEP
        and decision.forced is True
        and decision.reasoning.get("suboptimal", False) is True
    )

    print_result(
        "Force DEEP mode on simple query",
        test2_passed,
        f"Mode={decision.mode.value}, Warning={decision.reasoning.get('warning') is not None}",
    )

    return test1_passed and test2_passed


async def test_user_preferences():
    """Test user preference handling."""
    print_section("Test 5: User Preferences")

    router = IntelligentModeRouter()

    # Test preferred mode
    decision = await router.route_query(
        "Compare RAG and fine-tuning",
        "test_session",
        user_prefs={"preferred_mode": "deep"},
    )

    test1_passed = decision.mode == QueryMode.DEEP
    print_result("Preferred mode override", test1_passed, f"Mode={decision.mode.value}")

    # Test prefer_speed
    decision = await router.route_query(
        "Compare RAG and fine-tuning", "test_session", user_prefs={"prefer_speed": True}
    )

    test2_passed = decision.mode == QueryMode.FAST
    print_result(
        "Prefer speed (downgrade to FAST)", test2_passed, f"Mode={decision.mode.value}"
    )

    # Test prefer_quality
    decision = await router.route_query(
        "Compare RAG and fine-tuning",
        "test_session",
        user_prefs={"prefer_quality": True},
    )

    test3_passed = decision.mode == QueryMode.DEEP
    print_result(
        "Prefer quality (upgrade to DEEP)", test3_passed, f"Mode={decision.mode.value}"
    )

    return test1_passed and test2_passed and test3_passed


async def test_routing_confidence():
    """Test routing confidence calculation."""
    print_section("Test 6: Routing Confidence")

    router = IntelligentModeRouter()

    # Test high confidence (far from threshold)
    decision = await router.route_query("What is RAG?", "test_session")  # Very simple

    test1_passed = decision.routing_confidence >= 0.75
    print_result(
        "High confidence for clear simple query",
        test1_passed,
        f"Confidence={decision.routing_confidence:.3f}",
    )

    # Test confidence for complex query
    decision = await router.route_query(
        "Analyze the evolution of RAG systems from 2020 to 2024", "test_session"
    )

    test2_passed = decision.routing_confidence >= 0.75
    print_result(
        "High confidence for clear complex query",
        test2_passed,
        f"Confidence={decision.routing_confidence:.3f}",
    )

    return test1_passed and test2_passed


async def test_reasoning_generation():
    """Test reasoning generation."""
    print_section("Test 7: Reasoning Generation")

    router = IntelligentModeRouter()

    decision = await router.route_query("What is RAG?", "test_session")

    # Check reasoning structure
    has_complexity = "complexity" in decision.reasoning
    has_mode_params = "mode_parameters" in decision.reasoning
    has_decision_factors = "decision_factors" in decision.reasoning
    has_expected_perf = "expected_performance" in decision.reasoning

    all_passed = (
        has_complexity
        and has_mode_params
        and has_decision_factors
        and has_expected_perf
    )

    print_result(
        "Reasoning includes complexity details",
        has_complexity,
        f"Complexity level: {decision.reasoning.get('complexity', {}).get('level', 'N/A')}",
    )

    print_result(
        "Reasoning includes mode parameters",
        has_mode_params,
        f"Top-k: {decision.reasoning.get('mode_parameters', {}).get('top_k', 'N/A')}",
    )

    print_result(
        "Reasoning includes decision factors",
        has_decision_factors,
        f"Factors: {len(decision.reasoning.get('decision_factors', []))}",
    )

    print_result(
        "Reasoning includes expected performance",
        has_expected_perf,
        f"Target latency: {decision.reasoning.get('expected_performance', {}).get('target_latency', 'N/A')}",
    )

    return all_passed


async def test_korean_language_support():
    """Test Korean language support."""
    print_section("Test 8: Korean Language Support")

    router = IntelligentModeRouter()

    # Test Korean queries
    korean_queries = [
        ("RAG가 무엇인가요?", QueryMode.FAST),
        ("RAG와 파인튜닝을 비교해주세요", QueryMode.BALANCED),
        (
            "2020년부터 2024년까지 RAG 시스템의 발전 과정을 분석하고 특정 접근 방식이 지배적이 된 이유를 설명해주세요",
            QueryMode.DEEP,
        ),
    ]

    all_passed = True
    for query, expected_mode in korean_queries:
        decision = await router.route_query(query, "test_session", language="ko")

        passed = decision.mode == expected_mode
        all_passed = all_passed and passed

        print_result(
            f"Korean query: '{query[:30]}...'",
            passed,
            f"Mode={decision.mode.value}, Expected={expected_mode.value}, "
            f"Language={decision.reasoning.get('complexity', {}).get('language', 'N/A')}",
        )

    return all_passed


async def test_mode_parameters():
    """Test mode parameter management."""
    print_section("Test 9: Mode Parameter Management")

    router = IntelligentModeRouter()

    # Get FAST mode parameters
    params = router.get_mode_parameters(QueryMode.FAST)

    test1_passed = (
        params["top_k"] == 5
        and params["cache_strategy"] == CacheStrategy.L1_ONLY
        and params["timeout"] == 1.0
    )

    print_result(
        "Get FAST mode parameters",
        test1_passed,
        f"top_k={params['top_k']}, timeout={params['timeout']}s",
    )

    # Update parameters
    router.update_mode_parameters(QueryMode.FAST, top_k=7, timeout=1.5)
    updated_params = router.get_mode_parameters(QueryMode.FAST)

    test2_passed = updated_params["top_k"] == 7 and updated_params["timeout"] == 1.5

    print_result(
        "Update mode parameters",
        test2_passed,
        f"Updated top_k={updated_params['top_k']}, timeout={updated_params['timeout']}s",
    )

    return test1_passed and test2_passed


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  INTELLIGENT MODE ROUTER VERIFICATION")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Simple Query Routing", await test_simple_query_routing()))
    results.append(("Medium Query Routing", await test_medium_query_routing()))
    results.append(("Complex Query Routing", await test_complex_query_routing()))
    results.append(("Forced Mode Override", await test_forced_mode()))
    results.append(("User Preferences", await test_user_preferences()))
    results.append(("Routing Confidence", await test_routing_confidence()))
    results.append(("Reasoning Generation", await test_reasoning_generation()))
    results.append(("Korean Language Support", await test_korean_language_support()))
    results.append(("Mode Parameter Management", await test_mode_parameters()))

    # Print summary
    print_section("TEST SUMMARY")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'='*70}")
    print(f"  Results: {passed_count}/{total_count} tests passed")
    print(f"{'='*70}\n")

    if passed_count == total_count:
        print("✓ All tests passed! IntelligentModeRouter is working correctly.")
        return 0
    else:
        print(f"✗ {total_count - passed_count} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
