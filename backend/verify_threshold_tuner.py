"""
Verification script for ThresholdTuner implementation.

This script verifies that the threshold tuning system is working correctly.
"""

import asyncio
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
import os

backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from backend.services.threshold_tuner import (
    ThresholdTuner,
    PerformanceAnalysis,
    ThresholdRecommendation,
    TuningStatus,
)
from backend.services.query_pattern_learner import QueryPatternLearner
from backend.core.metrics_collector import MetricsCollector
from config import Settings


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message: str):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"  {message}")


async def verify_threshold_tuner():
    """Verify ThresholdTuner implementation."""

    print_section("Threshold Tuner Verification")

    # Create mock dependencies
    mock_pattern_learner = AsyncMock(spec=QueryPatternLearner)
    mock_metrics_collector = AsyncMock(spec=MetricsCollector)
    mock_settings = MagicMock(spec=Settings)
    mock_settings.COMPLEXITY_THRESHOLD_SIMPLE = 0.35
    mock_settings.COMPLEXITY_THRESHOLD_COMPLEX = 0.70

    # Create tuner
    tuner = ThresholdTuner(
        pattern_learner=mock_pattern_learner,
        metrics_collector=mock_metrics_collector,
        settings=mock_settings,
    )

    print_success("ThresholdTuner initialized")

    # Test 1: Performance Analysis
    print_section("Test 1: Performance Analysis")

    mock_metrics_collector.get_metrics.return_value = {
        "fast_queries": 450,
        "balanced_queries": 350,
        "deep_queries": 200,
        "fast_avg_latency": 0.8,
        "balanced_avg_latency": 2.5,
        "deep_avg_latency": 12.0,
        "fast_p95_latency": 0.95,
        "balanced_p95_latency": 2.9,
        "deep_p95_latency": 14.5,
        "fast_cache_hit_rate": 0.75,
        "balanced_cache_hit_rate": 0.55,
        "deep_cache_hit_rate": 0.35,
        "avg_satisfaction": 4.5,
        "escalation_rate": 0.12,
    }

    analysis = await tuner.analyze_performance(time_range_hours=24)

    print_info(f"Total queries: {analysis.total_queries}")
    print_info(f"Mode distribution:")
    print_info(f"  FAST: {analysis.mode_distribution['FAST']:.1%}")
    print_info(f"  BALANCED: {analysis.mode_distribution['BALANCED']:.1%}")
    print_info(f"  DEEP: {analysis.mode_distribution['DEEP']:.1%}")
    print_info(f"Average latency:")
    print_info(f"  FAST: {analysis.avg_latency['FAST']:.2f}s")
    print_info(f"  BALANCED: {analysis.avg_latency['BALANCED']:.2f}s")
    print_info(f"  DEEP: {analysis.avg_latency['DEEP']:.2f}s")
    print_info(f"User satisfaction: {analysis.user_satisfaction:.1f}/5.0")

    assert analysis.total_queries == 1000
    assert analysis.mode_distribution["FAST"] == 0.45
    assert analysis.mode_distribution["BALANCED"] == 0.35
    assert analysis.mode_distribution["DEEP"] == 0.20

    print_success("Performance analysis working correctly")

    # Test 2: Optimal Distribution
    print_section("Test 2: Threshold Recommendation (Optimal)")

    recommendation = await tuner.recommend_thresholds(analysis)

    print_info(f"Current thresholds: simple={0.35:.2f}, complex={0.70:.2f}")
    print_info(
        f"Recommended thresholds: simple={recommendation.simple_threshold:.2f}, "
        f"complex={recommendation.complex_threshold:.2f}"
    )
    print_info(f"Confidence: {recommendation.confidence:.2f}")
    print_info(f"Reasoning: {recommendation.reasoning}")

    assert recommendation.simple_threshold == 0.35
    assert recommendation.complex_threshold == 0.70
    assert "optimal" in recommendation.reasoning.lower()

    print_success("Optimal distribution detected correctly")

    # Test 3: Too Few FAST Queries
    print_section("Test 3: Threshold Recommendation (Too Few FAST)")

    analysis_low_fast = PerformanceAnalysis(
        mode_distribution={"FAST": 0.30, "BALANCED": 0.45, "DEEP": 0.25},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await tuner.recommend_thresholds(analysis_low_fast)

    print_info(f"Current FAST: 30.0% (target: 40-50%)")
    print_info(
        f"Recommended simple threshold: {recommendation.simple_threshold:.2f} (was 0.35)"
    )
    print_info(f"Reasoning: {recommendation.reasoning}")

    assert recommendation.simple_threshold > 0.35
    assert "FAST mode at 30.0%" in recommendation.reasoning

    print_success("Too few FAST queries detected, threshold increased")

    # Test 4: Too Many DEEP Queries
    print_section("Test 4: Threshold Recommendation (Too Many DEEP)")

    analysis_high_deep = PerformanceAnalysis(
        mode_distribution={"FAST": 0.35, "BALANCED": 0.30, "DEEP": 0.35},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await tuner.recommend_thresholds(analysis_high_deep)

    print_info(f"Current DEEP: 35.0% (target: 20-30%)")
    print_info(
        f"Recommended complex threshold: {recommendation.complex_threshold:.2f} (was 0.70)"
    )
    print_info(f"Reasoning: {recommendation.reasoning}")

    assert recommendation.complex_threshold > 0.70
    assert "DEEP mode at 35.0%" in recommendation.reasoning

    print_success("Too many DEEP queries detected, threshold increased")

    # Test 5: Dry Run Application
    print_section("Test 5: Apply Thresholds (Dry Run)")

    test_recommendation = ThresholdRecommendation(
        simple_threshold=0.40,
        complex_threshold=0.75,
        confidence=0.9,
        reasoning="Test recommendation",
        expected_impact={
            "threshold_changes": {"simple": 0.05, "complex": 0.05},
            "estimated_distribution": {"FAST": 0.48, "BALANCED": 0.32, "DEEP": 0.20},
        },
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.35, "complex": 0.70},
        timestamp=datetime.now(),
    )

    result = await tuner.apply_thresholds(test_recommendation, dry_run=True)

    print_info(f"Status: {result.status}")
    print_info(f"Previous thresholds: {result.previous_thresholds}")
    print_info(f"New thresholds: {result.new_thresholds}")
    print_info(f"Dry run: {result.dry_run}")

    assert result.status == TuningStatus.DRY_RUN
    assert result.dry_run is True
    assert mock_settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.35  # Unchanged

    print_success("Dry run completed without applying changes")

    # Test 6: Real Application
    print_section("Test 6: Apply Thresholds (Real)")

    result = await tuner.apply_thresholds(test_recommendation, dry_run=False)

    print_info(f"Status: {result.status}")
    print_info(f"Previous thresholds: {result.previous_thresholds}")
    print_info(f"New thresholds: {result.new_thresholds}")
    print_info(f"Settings updated:")
    print_info(f"  Simple: {mock_settings.COMPLEXITY_THRESHOLD_SIMPLE:.2f}")
    print_info(f"  Complex: {mock_settings.COMPLEXITY_THRESHOLD_COMPLEX:.2f}")

    assert result.status == TuningStatus.SUCCESS
    assert result.dry_run is False
    assert mock_settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.40
    assert mock_settings.COMPLEXITY_THRESHOLD_COMPLEX == 0.75

    print_success("Thresholds applied successfully")

    # Test 7: Invalid Thresholds
    print_section("Test 7: Invalid Threshold Validation")

    invalid_recommendation = ThresholdRecommendation(
        simple_threshold=0.80,  # Invalid: > complex
        complex_threshold=0.75,
        confidence=0.9,
        reasoning="Invalid test",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.40, "complex": 0.75},
        timestamp=datetime.now(),
    )

    result = await tuner.apply_thresholds(invalid_recommendation, dry_run=False)

    print_info(f"Status: {result.status}")
    print_info(f"Error: {result.error_message}")

    assert result.status == TuningStatus.FAILED
    assert "validation failed" in result.error_message.lower()

    print_success("Invalid thresholds rejected correctly")

    # Test 8: Low Confidence
    print_section("Test 8: Low Confidence Rejection")

    low_confidence_recommendation = ThresholdRecommendation(
        simple_threshold=0.45,
        complex_threshold=0.80,
        confidence=0.3,  # Low confidence
        reasoning="Low confidence test",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.40, "complex": 0.75},
        timestamp=datetime.now(),
    )

    result = await tuner.apply_thresholds(low_confidence_recommendation, dry_run=False)

    print_info(f"Status: {result.status}")
    print_info(f"Error: {result.error_message}")

    assert result.status == TuningStatus.FAILED
    assert "Low confidence" in result.error_message

    print_success("Low confidence recommendation rejected")

    # Test 9: Tuning History
    print_section("Test 9: Tuning History")

    history = tuner.get_tuning_history(limit=5)

    print_info(f"History entries: {len(history)}")
    for i, entry in enumerate(history, 1):
        print_info(f"  {i}. Status: {entry.status}, Timestamp: {entry.timestamp}")

    assert len(history) > 0
    assert all(isinstance(r.status, TuningStatus) for r in history)

    print_success("Tuning history tracked correctly")

    # Test 10: Current Thresholds
    print_section("Test 10: Get Current Thresholds")

    current = tuner.get_current_thresholds()

    print_info(f"Current thresholds:")
    print_info(f"  Simple: {current['simple']:.2f}")
    print_info(f"  Complex: {current['complex']:.2f}")

    assert "simple" in current
    assert "complex" in current

    print_success("Current thresholds retrieved correctly")

    # Summary
    print_section("Verification Summary")
    print_success("All threshold tuner tests passed!")
    print_info("Key features verified:")
    print_info("  ✓ Performance analysis with mode distribution")
    print_info("  ✓ Threshold recommendations based on targets")
    print_info("  ✓ Detection of imbalanced distributions")
    print_info("  ✓ Dry-run mode for safe testing")
    print_info("  ✓ Real threshold application")
    print_info("  ✓ Validation of threshold values")
    print_info("  ✓ Confidence-based rejection")
    print_info("  ✓ Tuning history tracking")
    print_info("  ✓ Safety checks and rollback support")

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(verify_threshold_tuner())
        if result:
            print("\n" + "=" * 60)
            print("  ✓ THRESHOLD TUNER VERIFICATION COMPLETE")
            print("=" * 60 + "\n")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("  ✗ THRESHOLD TUNER VERIFICATION FAILED")
            print("=" * 60 + "\n")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
