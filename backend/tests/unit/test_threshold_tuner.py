"""
Unit tests for ThresholdTuner service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.threshold_tuner import (
    ThresholdTuner,
    PerformanceAnalysis,
    ThresholdRecommendation,
    TuningResult,
    TuningStatus,
)
from backend.services.query_pattern_learner import QueryPatternLearner
from backend.core.metrics_collector import MetricsCollector
from backend.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.COMPLEXITY_THRESHOLD_SIMPLE = 0.35
    settings.COMPLEXITY_THRESHOLD_COMPLEX = 0.70
    return settings


@pytest.fixture
def mock_pattern_learner():
    """Create mock pattern learner."""
    return AsyncMock(spec=QueryPatternLearner)


@pytest.fixture
def mock_metrics_collector():
    """Create mock metrics collector."""
    return AsyncMock(spec=MetricsCollector)


@pytest.fixture
def threshold_tuner(mock_pattern_learner, mock_metrics_collector, mock_settings):
    """Create ThresholdTuner instance."""
    return ThresholdTuner(
        pattern_learner=mock_pattern_learner,
        metrics_collector=mock_metrics_collector,
        settings=mock_settings,
    )


@pytest.mark.asyncio
async def test_analyze_performance_success(threshold_tuner, mock_metrics_collector):
    """Test successful performance analysis."""
    # Mock metrics data
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

    analysis = await threshold_tuner.analyze_performance(time_range_hours=24)

    assert analysis.total_queries == 1000
    assert analysis.mode_distribution["FAST"] == 0.45
    assert analysis.mode_distribution["BALANCED"] == 0.35
    assert analysis.mode_distribution["DEEP"] == 0.20
    assert analysis.avg_latency["FAST"] == 0.8
    assert analysis.p95_latency["BALANCED"] == 2.9
    assert analysis.user_satisfaction == 4.5
    assert analysis.escalation_rate == 0.12


@pytest.mark.asyncio
async def test_analyze_performance_no_queries(threshold_tuner, mock_metrics_collector):
    """Test performance analysis with no queries."""
    mock_metrics_collector.get_metrics.return_value = {
        "fast_queries": 0,
        "balanced_queries": 0,
        "deep_queries": 0,
    }

    analysis = await threshold_tuner.analyze_performance()

    assert analysis.total_queries == 0
    assert analysis.mode_distribution["FAST"] == 0.0


@pytest.mark.asyncio
async def test_recommend_thresholds_too_few_fast(threshold_tuner):
    """Test threshold recommendation when FAST mode is underutilized."""
    analysis = PerformanceAnalysis(
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

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should increase simple threshold to route more to FAST
    assert recommendation.simple_threshold > 0.35
    assert "FAST mode at 30.0%" in recommendation.reasoning
    assert recommendation.confidence > 0.0


@pytest.mark.asyncio
async def test_recommend_thresholds_too_many_fast(threshold_tuner):
    """Test threshold recommendation when FAST mode is overutilized."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.60, "BALANCED": 0.25, "DEEP": 0.15},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should decrease simple threshold to route fewer to FAST
    assert recommendation.simple_threshold < 0.35
    assert "FAST mode at 60.0%" in recommendation.reasoning


@pytest.mark.asyncio
async def test_recommend_thresholds_too_few_deep(threshold_tuner):
    """Test threshold recommendation when DEEP mode is underutilized."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.45, "BALANCED": 0.45, "DEEP": 0.10},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should decrease complex threshold to route more to DEEP
    assert recommendation.complex_threshold < 0.70
    assert "DEEP mode at 10.0%" in recommendation.reasoning


@pytest.mark.asyncio
async def test_recommend_thresholds_too_many_deep(threshold_tuner):
    """Test threshold recommendation when DEEP mode is overutilized."""
    analysis = PerformanceAnalysis(
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

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should increase complex threshold to route fewer to DEEP
    assert recommendation.complex_threshold > 0.70
    assert "DEEP mode at 35.0%" in recommendation.reasoning


@pytest.mark.asyncio
async def test_recommend_thresholds_optimal(threshold_tuner):
    """Test threshold recommendation when distribution is optimal."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should keep current thresholds
    assert recommendation.simple_threshold == 0.35
    assert recommendation.complex_threshold == 0.70
    assert "optimal" in recommendation.reasoning.lower()


@pytest.mark.asyncio
async def test_recommend_thresholds_insufficient_data(threshold_tuner):
    """Test threshold recommendation with insufficient data."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=50,  # Below MIN_QUERIES_FOR_TUNING
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    assert recommendation.confidence == 0.0
    assert "Insufficient data" in recommendation.reasoning


@pytest.mark.asyncio
async def test_recommend_thresholds_high_latency(threshold_tuner):
    """Test threshold recommendation with high latency."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        avg_latency={"FAST": 1.5, "BALANCED": 4.0, "DEEP": 12.0},
        p95_latency={"FAST": 2.0, "BALANCED": 5.0, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    recommendation = await threshold_tuner.recommend_thresholds(analysis)

    # Should note latency issues and reduce confidence
    assert recommendation.confidence < 1.0
    assert "exceeds target" in recommendation.reasoning


@pytest.mark.asyncio
async def test_apply_thresholds_dry_run(threshold_tuner):
    """Test applying thresholds in dry-run mode."""
    recommendation = ThresholdRecommendation(
        simple_threshold=0.40,
        complex_threshold=0.75,
        confidence=0.9,
        reasoning="Test recommendation",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.35, "complex": 0.70},
        timestamp=datetime.now(),
    )

    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=True)

    assert result.status == TuningStatus.DRY_RUN
    assert result.dry_run is True
    assert result.previous_thresholds["simple"] == 0.35
    assert result.new_thresholds["simple"] == 0.40
    # Settings should not be changed
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.35


@pytest.mark.asyncio
async def test_apply_thresholds_success(threshold_tuner):
    """Test successfully applying thresholds."""
    recommendation = ThresholdRecommendation(
        simple_threshold=0.40,
        complex_threshold=0.75,
        confidence=0.9,
        reasoning="Test recommendation",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.35, "complex": 0.70},
        timestamp=datetime.now(),
    )

    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=False)

    assert result.status == TuningStatus.SUCCESS
    assert result.dry_run is False
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.40
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_COMPLEX == 0.75


@pytest.mark.asyncio
async def test_apply_thresholds_invalid(threshold_tuner):
    """Test applying invalid thresholds."""
    recommendation = ThresholdRecommendation(
        simple_threshold=0.80,  # Invalid: > complex
        complex_threshold=0.75,
        confidence=0.9,
        reasoning="Test recommendation",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.35, "complex": 0.70},
        timestamp=datetime.now(),
    )

    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=False)

    assert result.status == TuningStatus.FAILED
    assert "validation failed" in result.error_message.lower()
    # Settings should not be changed
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.35


@pytest.mark.asyncio
async def test_apply_thresholds_low_confidence(threshold_tuner):
    """Test applying thresholds with low confidence."""
    recommendation = ThresholdRecommendation(
        simple_threshold=0.40,
        complex_threshold=0.75,
        confidence=0.3,  # Low confidence
        reasoning="Test recommendation",
        expected_impact={},
        current_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        target_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        current_thresholds={"simple": 0.35, "complex": 0.70},
        timestamp=datetime.now(),
    )

    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=False)

    assert result.status == TuningStatus.FAILED
    assert "Low confidence" in result.error_message
    # Settings should not be changed
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_SIMPLE == 0.35


def test_validate_thresholds_valid(threshold_tuner):
    """Test threshold validation with valid values."""
    assert threshold_tuner._validate_thresholds(0.35, 0.70) is True
    assert threshold_tuner._validate_thresholds(0.20, 0.80) is True
    assert threshold_tuner._validate_thresholds(0.10, 0.90) is True


def test_validate_thresholds_invalid_range(threshold_tuner):
    """Test threshold validation with out-of-range values."""
    assert threshold_tuner._validate_thresholds(0.05, 0.70) is False  # Too low
    assert threshold_tuner._validate_thresholds(0.35, 0.95) is False  # Too high
    assert threshold_tuner._validate_thresholds(-0.1, 0.70) is False  # Negative


def test_validate_thresholds_invalid_ordering(threshold_tuner):
    """Test threshold validation with invalid ordering."""
    assert threshold_tuner._validate_thresholds(0.70, 0.35) is False  # Reversed
    assert threshold_tuner._validate_thresholds(0.50, 0.50) is False  # Equal


def test_validate_thresholds_insufficient_gap(threshold_tuner):
    """Test threshold validation with insufficient gap."""
    assert threshold_tuner._validate_thresholds(0.35, 0.40) is False  # Gap < 0.1


def test_estimate_impact(threshold_tuner):
    """Test impact estimation."""
    analysis = PerformanceAnalysis(
        mode_distribution={"FAST": 0.45, "BALANCED": 0.35, "DEEP": 0.20},
        avg_latency={"FAST": 0.8, "BALANCED": 2.5, "DEEP": 12.0},
        p95_latency={"FAST": 0.95, "BALANCED": 2.9, "DEEP": 14.5},
        user_satisfaction=4.5,
        escalation_rate=0.12,
        cache_hit_rate={"FAST": 0.75, "BALANCED": 0.55, "DEEP": 0.35},
        total_queries=1000,
        time_range="24h",
        timestamp=datetime.now(),
    )

    impact = threshold_tuner._estimate_impact(
        analysis,
        current_simple=0.35,
        current_complex=0.70,
        new_simple=0.40,
        new_complex=0.75,
    )

    assert "threshold_changes" in impact
    assert "estimated_distribution" in impact
    assert "distribution_changes" in impact
    assert impact["threshold_changes"]["simple"] == 0.05
    assert impact["threshold_changes"]["complex"] == 0.05


def test_get_tuning_history(threshold_tuner):
    """Test getting tuning history."""
    # Add some history
    for i in range(15):
        result = TuningResult(
            status=TuningStatus.SUCCESS,
            previous_thresholds={"simple": 0.35, "complex": 0.70},
            new_thresholds={"simple": 0.40, "complex": 0.75},
            recommendation=MagicMock(),
            dry_run=False,
        )
        threshold_tuner.tuning_history.append(result)

    history = threshold_tuner.get_tuning_history(limit=10)

    assert len(history) == 10
    assert all(isinstance(r, TuningResult) for r in history)


def test_get_current_thresholds(threshold_tuner):
    """Test getting current thresholds."""
    thresholds = threshold_tuner.get_current_thresholds()

    assert thresholds["simple"] == 0.35
    assert thresholds["complex"] == 0.70


@pytest.mark.asyncio
async def test_end_to_end_tuning_flow(threshold_tuner, mock_metrics_collector):
    """Test complete tuning flow from analysis to application."""
    # Setup metrics
    mock_metrics_collector.get_metrics.return_value = {
        "fast_queries": 300,  # 30% - too low
        "balanced_queries": 400,  # 40%
        "deep_queries": 300,  # 30% - too high
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

    # Step 1: Analyze performance
    analysis = await threshold_tuner.analyze_performance()
    assert analysis.total_queries == 1000
    assert analysis.mode_distribution["FAST"] == 0.30

    # Step 2: Get recommendation
    recommendation = await threshold_tuner.recommend_thresholds(analysis)
    assert recommendation.simple_threshold > 0.35  # Should increase
    assert recommendation.complex_threshold > 0.70  # Should increase

    # Step 3: Apply (dry run)
    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=True)
    assert result.status == TuningStatus.DRY_RUN

    # Step 4: Apply (real)
    result = await threshold_tuner.apply_thresholds(recommendation, dry_run=False)
    assert result.status == TuningStatus.SUCCESS
    assert threshold_tuner.settings.COMPLEXITY_THRESHOLD_SIMPLE > 0.35
