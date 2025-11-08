"""
Threshold Tuning System for Adaptive RAG

This module provides automatic threshold tuning based on system performance metrics.
It analyzes mode distribution, latency, and user satisfaction to recommend optimal
complexity thresholds.

Target Distribution:
- FAST mode: 40-50%
- BALANCED mode: 30-40%
- DEEP mode: 20-30%
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    from backend.config import Settings
    from backend.services.query_pattern_learner import QueryPatternLearner
    from backend.core.metrics_collector import MetricsCollector
except ImportError:
    from config import Settings
    from services.query_pattern_learner import QueryPatternLearner
    from backend.core.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class TuningStatus(str, Enum):
    """Status of threshold tuning operation."""

    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    DRY_RUN = "dry_run"


@dataclass
class PerformanceAnalysis:
    """Analysis of current system performance."""

    mode_distribution: Dict[str, float]  # Percentage by mode
    avg_latency: Dict[str, float]  # Average latency by mode
    p95_latency: Dict[str, float]  # 95th percentile latency by mode
    user_satisfaction: float  # Average satisfaction score
    escalation_rate: float  # Percentage of queries escalated
    cache_hit_rate: Dict[str, float]  # Cache hit rate by mode
    total_queries: int
    time_range: str
    timestamp: datetime


@dataclass
class ThresholdRecommendation:
    """Recommendation for threshold adjustments."""

    simple_threshold: float  # Recommended SIMPLE threshold
    complex_threshold: float  # Recommended COMPLEX threshold
    confidence: float  # Confidence in recommendation (0-1)
    reasoning: str  # Explanation of recommendation
    expected_impact: Dict[str, Any]  # Expected changes
    current_distribution: Dict[str, float]
    target_distribution: Dict[str, float]
    current_thresholds: Dict[str, float]
    timestamp: datetime


@dataclass
class TuningResult:
    """Result of threshold tuning operation."""

    status: TuningStatus
    previous_thresholds: Dict[str, float]
    new_thresholds: Optional[Dict[str, float]]
    recommendation: ThresholdRecommendation
    dry_run: bool
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ThresholdTuner:
    """
    Automatic threshold tuning system.

    Analyzes system performance and recommends threshold adjustments
    to maintain optimal mode distribution and performance.
    """

    # Target distribution ranges
    TARGET_FAST_MIN = 0.40
    TARGET_FAST_MAX = 0.50
    TARGET_BALANCED_MIN = 0.30
    TARGET_BALANCED_MAX = 0.40
    TARGET_DEEP_MIN = 0.20
    TARGET_DEEP_MAX = 0.30

    # Performance targets
    TARGET_FAST_LATENCY = 1.0  # seconds
    TARGET_BALANCED_LATENCY = 3.0  # seconds
    TARGET_DEEP_LATENCY = 15.0  # seconds

    # Tuning parameters
    THRESHOLD_ADJUSTMENT_STEP = 0.05
    MIN_THRESHOLD = 0.10
    MAX_THRESHOLD = 0.90
    MIN_QUERIES_FOR_TUNING = 100

    def __init__(
        self,
        pattern_learner: QueryPatternLearner,
        metrics_collector: MetricsCollector,
        settings: Settings,
    ):
        """
        Initialize threshold tuner.

        Args:
            pattern_learner: Query pattern learning service
            metrics_collector: Metrics collection service
            settings: Application settings
        """
        self.patterns = pattern_learner
        self.metrics = metrics_collector
        self.settings = settings
        self.tuning_history: List[TuningResult] = []

        logger.info("ThresholdTuner initialized")

    async def analyze_performance(
        self, time_range_hours: int = 24
    ) -> PerformanceAnalysis:
        """
        Analyze current system performance.

        Args:
            time_range_hours: Hours of data to analyze

        Returns:
            PerformanceAnalysis with current metrics
        """
        logger.info(
            "Analyzing performance",
            extra={"time_range_hours": time_range_hours}
        )

        try:
            # Get metrics from collector
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)

            metrics = await self.metrics.get_metrics(
                start_time=start_time, end_time=end_time
            )

            # Calculate mode distribution
            total_queries = sum(
                [
                    metrics.get("fast_queries", 0),
                    metrics.get("balanced_queries", 0),
                    metrics.get("deep_queries", 0),
                ]
            )

            if total_queries == 0:
                logger.warning("No queries found in time range")
                return self._create_empty_analysis(time_range_hours)

            mode_distribution = {
                "FAST": metrics.get("fast_queries", 0) / total_queries,
                "BALANCED": metrics.get("balanced_queries", 0) / total_queries,
                "DEEP": metrics.get("deep_queries", 0) / total_queries,
            }

            # Get latency metrics
            avg_latency = {
                "FAST": metrics.get("fast_avg_latency", 0.0),
                "BALANCED": metrics.get("balanced_avg_latency", 0.0),
                "DEEP": metrics.get("deep_avg_latency", 0.0),
            }

            p95_latency = {
                "FAST": metrics.get("fast_p95_latency", 0.0),
                "BALANCED": metrics.get("balanced_p95_latency", 0.0),
                "DEEP": metrics.get("deep_p95_latency", 0.0),
            }

            # Get cache hit rates
            cache_hit_rate = {
                "FAST": metrics.get("fast_cache_hit_rate", 0.0),
                "BALANCED": metrics.get("balanced_cache_hit_rate", 0.0),
                "DEEP": metrics.get("deep_cache_hit_rate", 0.0),
            }

            analysis = PerformanceAnalysis(
                mode_distribution=mode_distribution,
                avg_latency=avg_latency,
                p95_latency=p95_latency,
                user_satisfaction=metrics.get("avg_satisfaction", 0.0),
                escalation_rate=metrics.get("escalation_rate", 0.0),
                cache_hit_rate=cache_hit_rate,
                total_queries=total_queries,
                time_range=f"{time_range_hours}h",
                timestamp=datetime.now(),
            )

            logger.info(
                f"Performance analysis complete: {total_queries} queries analyzed"
            )
            logger.info(
                f"Mode distribution: FAST={mode_distribution['FAST']:.1%}, "
                f"BALANCED={mode_distribution['BALANCED']:.1%}, "
                f"DEEP={mode_distribution['DEEP']:.1%}"
            )

            return analysis

        except Exception as e:
            logger.error(
                "Error analyzing performance",
                extra={
                    "time_range_hours": time_range_hours,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return self._create_empty_analysis(time_range_hours)

    async def recommend_thresholds(
        self, analysis: PerformanceAnalysis
    ) -> ThresholdRecommendation:
        """
        Recommend threshold adjustments based on performance analysis.

        Args:
            analysis: Current performance analysis

        Returns:
            ThresholdRecommendation with suggested adjustments
        """
        logger.info("Generating threshold recommendations")

        # Get current thresholds
        current_simple = self.settings.COMPLEXITY_THRESHOLD_SIMPLE
        current_complex = self.settings.COMPLEXITY_THRESHOLD_COMPLEX

        current_thresholds = {"simple": current_simple, "complex": current_complex}

        # Initialize recommendations with current values
        recommended_simple = current_simple
        recommended_complex = current_complex

        reasoning_parts = []
        confidence = 1.0

        # Check if we have enough data
        if analysis.total_queries < self.MIN_QUERIES_FOR_TUNING:
            reasoning_parts.append(
                f"Insufficient data ({analysis.total_queries} queries, "
                f"need {self.MIN_QUERIES_FOR_TUNING})"
            )
            confidence = 0.0
        else:
            # Analyze FAST mode distribution
            fast_pct = analysis.mode_distribution.get("FAST", 0.0)
            if fast_pct < self.TARGET_FAST_MIN:
                # Too few FAST queries - increase simple threshold
                adjustment = self.THRESHOLD_ADJUSTMENT_STEP
                recommended_simple = min(
                    current_simple + adjustment, self.MAX_THRESHOLD
                )
                reasoning_parts.append(
                    f"FAST mode at {fast_pct:.1%} (target: {self.TARGET_FAST_MIN:.0%}-"
                    f"{self.TARGET_FAST_MAX:.0%}). Increasing simple threshold to "
                    f"route more queries to FAST mode."
                )
            elif fast_pct > self.TARGET_FAST_MAX:
                # Too many FAST queries - decrease simple threshold
                adjustment = self.THRESHOLD_ADJUSTMENT_STEP
                recommended_simple = max(
                    current_simple - adjustment, self.MIN_THRESHOLD
                )
                reasoning_parts.append(
                    f"FAST mode at {fast_pct:.1%} (target: {self.TARGET_FAST_MIN:.0%}-"
                    f"{self.TARGET_FAST_MAX:.0%}). Decreasing simple threshold to "
                    f"route fewer queries to FAST mode."
                )

            # Analyze DEEP mode distribution
            deep_pct = analysis.mode_distribution.get("DEEP", 0.0)
            if deep_pct < self.TARGET_DEEP_MIN:
                # Too few DEEP queries - decrease complex threshold
                adjustment = self.THRESHOLD_ADJUSTMENT_STEP
                recommended_complex = max(
                    current_complex - adjustment, recommended_simple + 0.1
                )  # Maintain gap
                reasoning_parts.append(
                    f"DEEP mode at {deep_pct:.1%} (target: {self.TARGET_DEEP_MIN:.0%}-"
                    f"{self.TARGET_DEEP_MAX:.0%}). Decreasing complex threshold to "
                    f"route more queries to DEEP mode."
                )
            elif deep_pct > self.TARGET_DEEP_MAX:
                # Too many DEEP queries - increase complex threshold
                adjustment = self.THRESHOLD_ADJUSTMENT_STEP
                recommended_complex = min(
                    current_complex + adjustment, self.MAX_THRESHOLD
                )
                reasoning_parts.append(
                    f"DEEP mode at {deep_pct:.1%} (target: {self.TARGET_DEEP_MIN:.0%}-"
                    f"{self.TARGET_DEEP_MAX:.0%}). Increasing complex threshold to "
                    f"route fewer queries to DEEP mode."
                )

            # Check latency performance
            if analysis.p95_latency.get("FAST", 0.0) > self.TARGET_FAST_LATENCY:
                reasoning_parts.append(
                    f"FAST mode p95 latency ({analysis.p95_latency['FAST']:.2f}s) "
                    f"exceeds target ({self.TARGET_FAST_LATENCY}s). Consider "
                    f"infrastructure scaling."
                )
                confidence *= 0.8

            if analysis.p95_latency.get("BALANCED", 0.0) > self.TARGET_BALANCED_LATENCY:
                reasoning_parts.append(
                    f"BALANCED mode p95 latency ({analysis.p95_latency['BALANCED']:.2f}s) "
                    f"exceeds target ({self.TARGET_BALANCED_LATENCY}s). Consider "
                    f"infrastructure scaling."
                )
                confidence *= 0.8

            # Check if thresholds are unchanged
            if (
                recommended_simple == current_simple
                and recommended_complex == current_complex
            ):
                reasoning_parts.append(
                    "Current thresholds are optimal. No adjustments needed."
                )

        # Calculate expected impact
        expected_impact = self._estimate_impact(
            analysis,
            current_simple,
            current_complex,
            recommended_simple,
            recommended_complex,
        )

        # Create recommendation
        recommendation = ThresholdRecommendation(
            simple_threshold=recommended_simple,
            complex_threshold=recommended_complex,
            confidence=confidence,
            reasoning=(
                " ".join(reasoning_parts)
                if reasoning_parts
                else "No adjustments needed."
            ),
            expected_impact=expected_impact,
            current_distribution=analysis.mode_distribution,
            target_distribution={
                "FAST": (self.TARGET_FAST_MIN + self.TARGET_FAST_MAX) / 2,
                "BALANCED": (self.TARGET_BALANCED_MIN + self.TARGET_BALANCED_MAX) / 2,
                "DEEP": (self.TARGET_DEEP_MIN + self.TARGET_DEEP_MAX) / 2,
            },
            current_thresholds=current_thresholds,
            timestamp=datetime.now(),
        )

        logger.info(
            f"Threshold recommendation: simple={recommended_simple:.2f}, "
            f"complex={recommended_complex:.2f}, confidence={confidence:.2f}"
        )

        return recommendation

    async def apply_thresholds(
        self, recommendation: ThresholdRecommendation, dry_run: bool = True
    ) -> TuningResult:
        """
        Apply threshold adjustments.

        Args:
            recommendation: Threshold recommendation to apply
            dry_run: If True, simulate without applying changes

        Returns:
            TuningResult with operation status
        """
        logger.info(
            "Applying thresholds",
            extra={"dry_run": dry_run, "new_thresholds": new_thresholds}
        )

        # Store previous thresholds for rollback
        previous_thresholds = {
            "simple": self.settings.COMPLEXITY_THRESHOLD_SIMPLE,
            "complex": self.settings.COMPLEXITY_THRESHOLD_COMPLEX,
        }

        new_thresholds = {
            "simple": recommendation.simple_threshold,
            "complex": recommendation.complex_threshold,
        }

        # Safety checks
        if not self._validate_thresholds(
            recommendation.simple_threshold, recommendation.complex_threshold
        ):
            error_msg = "Threshold validation failed"
            logger.error(error_msg)
            result = TuningResult(
                status=TuningStatus.FAILED,
                previous_thresholds=previous_thresholds,
                new_thresholds=None,
                recommendation=recommendation,
                dry_run=dry_run,
                error_message=error_msg,
            )
            self.tuning_history.append(result)
            return result

        # Check confidence threshold
        if recommendation.confidence < 0.5:
            error_msg = (
                f"Low confidence ({recommendation.confidence:.2f}), skipping tuning"
            )
            logger.warning(error_msg)
            result = TuningResult(
                status=TuningStatus.FAILED,
                previous_thresholds=previous_thresholds,
                new_thresholds=None,
                recommendation=recommendation,
                dry_run=dry_run,
                error_message=error_msg,
            )
            self.tuning_history.append(result)
            return result

        if dry_run:
            logger.info(
                "DRY RUN: Would update thresholds",
                extra={"new_thresholds": new_thresholds}
            )
            result = TuningResult(
                status=TuningStatus.DRY_RUN,
                previous_thresholds=previous_thresholds,
                new_thresholds=new_thresholds,
                recommendation=recommendation,
                dry_run=True,
            )
            self.tuning_history.append(result)
            return result

        try:
            # Apply new thresholds
            self.settings.COMPLEXITY_THRESHOLD_SIMPLE = recommendation.simple_threshold
            self.settings.COMPLEXITY_THRESHOLD_COMPLEX = (
                recommendation.complex_threshold
            )

            logger.info(
                "Thresholds updated successfully",
                extra={"new_thresholds": new_thresholds}
            )

            # Notify administrators
            await self._notify_administrators(
                previous_thresholds, new_thresholds, recommendation
            )

            result = TuningResult(
                status=TuningStatus.SUCCESS,
                previous_thresholds=previous_thresholds,
                new_thresholds=new_thresholds,
                recommendation=recommendation,
                dry_run=False,
            )
            self.tuning_history.append(result)
            return result

        except Exception as e:
            error_msg = f"Error applying thresholds: {e}"
            logger.error(error_msg, exc_info=True)

            # Attempt rollback
            try:
                self.settings.COMPLEXITY_THRESHOLD_SIMPLE = previous_thresholds[
                    "simple"
                ]
                self.settings.COMPLEXITY_THRESHOLD_COMPLEX = previous_thresholds[
                    "complex"
                ]
                logger.info("Thresholds rolled back successfully")
                status = TuningStatus.ROLLED_BACK
            except Exception as rollback_error:
                logger.error(
                    "Rollback failed",
                    extra={"error_type": type(rollback_error).__name__},
                    exc_info=True
                )
                status = TuningStatus.FAILED

            result = TuningResult(
                status=status,
                previous_thresholds=previous_thresholds,
                new_thresholds=None,
                recommendation=recommendation,
                dry_run=False,
                error_message=error_msg,
            )
            self.tuning_history.append(result)
            return result

    def _validate_thresholds(
        self, simple_threshold: float, complex_threshold: float
    ) -> bool:
        """
        Validate threshold values.

        Args:
            simple_threshold: Simple complexity threshold
            complex_threshold: Complex complexity threshold

        Returns:
            True if valid, False otherwise
        """
        # Check range
        if not (self.MIN_THRESHOLD <= simple_threshold <= self.MAX_THRESHOLD):
            logger.error(
                "Simple threshold out of range",
                extra={
                    "threshold": simple_threshold,
                    "min": self.MIN_THRESHOLD,
                    "max": self.MAX_THRESHOLD
                }
            )
            return False

        if not (self.MIN_THRESHOLD <= complex_threshold <= self.MAX_THRESHOLD):
            logger.error(
                "Complex threshold out of range",
                extra={
                    "threshold": complex_threshold,
                    "min": self.MIN_THRESHOLD,
                    "max": self.MAX_THRESHOLD
                }
            )
            return False

        # Check ordering (simple < complex)
        if simple_threshold >= complex_threshold:
            logger.error(
                f"Simple threshold {simple_threshold} >= complex threshold {complex_threshold}"
            )
            return False

        # Check minimum gap
        if complex_threshold - simple_threshold < 0.1:
            logger.error(
                f"Insufficient gap between thresholds: {complex_threshold - simple_threshold}"
            )
            return False

        return True

    def _estimate_impact(
        self,
        analysis: PerformanceAnalysis,
        current_simple: float,
        current_complex: float,
        new_simple: float,
        new_complex: float,
    ) -> Dict[str, Any]:
        """
        Estimate impact of threshold changes.

        Args:
            analysis: Current performance analysis
            current_simple: Current simple threshold
            current_complex: Current complex threshold
            new_simple: New simple threshold
            new_complex: New complex threshold

        Returns:
            Dictionary with estimated impact
        """
        # Calculate threshold changes
        simple_change = new_simple - current_simple
        complex_change = new_complex - current_complex

        # Estimate distribution changes (simplified model)
        current_dist = analysis.mode_distribution
        estimated_dist = {
            "FAST": current_dist.get("FAST", 0.0),
            "BALANCED": current_dist.get("BALANCED", 0.0),
            "DEEP": current_dist.get("DEEP", 0.0),
        }

        # Adjust based on threshold changes
        if simple_change != 0:
            # Simple threshold affects FAST/BALANCED split
            shift = simple_change * 0.5  # Simplified model
            estimated_dist["FAST"] = max(0, min(1, estimated_dist["FAST"] + shift))
            estimated_dist["BALANCED"] = max(
                0, min(1, estimated_dist["BALANCED"] - shift)
            )

        if complex_change != 0:
            # Complex threshold affects BALANCED/DEEP split
            shift = complex_change * 0.5  # Simplified model
            estimated_dist["BALANCED"] = max(
                0, min(1, estimated_dist["BALANCED"] + shift)
            )
            estimated_dist["DEEP"] = max(0, min(1, estimated_dist["DEEP"] - shift))

        # Normalize
        total = sum(estimated_dist.values())
        if total > 0:
            estimated_dist = {k: v / total for k, v in estimated_dist.items()}

        return {
            "threshold_changes": {"simple": simple_change, "complex": complex_change},
            "estimated_distribution": estimated_dist,
            "distribution_changes": {
                "FAST": estimated_dist["FAST"] - current_dist.get("FAST", 0.0),
                "BALANCED": estimated_dist["BALANCED"]
                - current_dist.get("BALANCED", 0.0),
                "DEEP": estimated_dist["DEEP"] - current_dist.get("DEEP", 0.0),
            },
        }

    async def _notify_administrators(
        self,
        previous_thresholds: Dict[str, float],
        new_thresholds: Dict[str, float],
        recommendation: ThresholdRecommendation,
    ):
        """
        Notify administrators of threshold changes.

        Args:
            previous_thresholds: Previous threshold values
            new_thresholds: New threshold values
            recommendation: Threshold recommendation
        """
        notification = {
            "event": "threshold_tuning",
            "timestamp": datetime.now().isoformat(),
            "previous_thresholds": previous_thresholds,
            "new_thresholds": new_thresholds,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "expected_impact": recommendation.expected_impact,
        }

        logger.info(
            "Administrator notification",
            extra={"notification": notification}
        )

        # TODO: Implement actual notification mechanism (email, Slack, etc.)
        # For now, just log the notification

    def _create_empty_analysis(self, time_range_hours: int) -> PerformanceAnalysis:
        """Create empty performance analysis for error cases."""
        return PerformanceAnalysis(
            mode_distribution={"FAST": 0.0, "BALANCED": 0.0, "DEEP": 0.0},
            avg_latency={"FAST": 0.0, "BALANCED": 0.0, "DEEP": 0.0},
            p95_latency={"FAST": 0.0, "BALANCED": 0.0, "DEEP": 0.0},
            user_satisfaction=0.0,
            escalation_rate=0.0,
            cache_hit_rate={"FAST": 0.0, "BALANCED": 0.0, "DEEP": 0.0},
            total_queries=0,
            time_range=f"{time_range_hours}h",
            timestamp=datetime.now(),
        )

    def get_tuning_history(self, limit: int = 10) -> List[TuningResult]:
        """
        Get recent tuning history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent tuning results
        """
        return self.tuning_history[-limit:]

    def get_current_thresholds(self) -> Dict[str, float]:
        """
        Get current threshold values.

        Returns:
            Dictionary with current thresholds
        """
        return {
            "simple": self.settings.COMPLEXITY_THRESHOLD_SIMPLE,
            "complex": self.settings.COMPLEXITY_THRESHOLD_COMPLEX,
        }
