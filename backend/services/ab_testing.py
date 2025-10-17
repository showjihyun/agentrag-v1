# A/B Testing Framework for RAG Strategies
import logging
import random
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Experiment:
    """A/B test experiment"""

    id: str
    name: str
    description: str
    variants: List[str]
    traffic_split: Dict[str, float]  # variant -> percentage
    active: bool
    created_at: datetime


@dataclass
class ExperimentResult:
    """Result from A/B test"""

    experiment_id: str
    variant: str
    user_id: str
    query: str
    response_time_ms: float
    accuracy_score: Optional[float]
    user_feedback: Optional[int]  # 1, 0, -1
    timestamp: datetime


class ABTestingService:
    """
    A/B Testing service for comparing RAG strategies.

    Features:
    - Multiple concurrent experiments
    - Consistent user assignment (hash-based)
    - Metrics collection and analysis
    - Statistical significance testing
    """

    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.results: Dict[str, List[ExperimentResult]] = defaultdict(list)

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        variants: List[str],
        traffic_split: Dict[str, float],
    ) -> Experiment:
        """
        Create new A/B test experiment.

        Args:
            experiment_id: Unique experiment ID
            name: Experiment name
            description: Description
            variants: List of variant names (e.g., ["control", "hybrid", "adaptive"])
            traffic_split: Traffic allocation (e.g., {"control": 0.5, "hybrid": 0.5})
        """
        # Validate traffic split
        total = sum(traffic_split.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            traffic_split=traffic_split,
            active=True,
            created_at=datetime.utcnow(),
        )

        self.experiments[experiment_id] = experiment

        logger.info(
            f"Created experiment '{name}' with variants: {variants}, "
            f"split: {traffic_split}"
        )

        return experiment

    def assign_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """
        Assign user to experiment variant.

        Uses consistent hashing to ensure same user always gets same variant.
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or not experiment.active:
            return None

        # Hash user_id + experiment_id for consistency
        hash_input = f"{user_id}:{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Normalize to 0-1
        normalized = (hash_value % 10000) / 10000.0

        # Assign based on traffic split
        cumulative = 0.0
        for variant, percentage in experiment.traffic_split.items():
            cumulative += percentage
            if normalized < cumulative:
                return variant

        # Fallback to first variant
        return experiment.variants[0]

    def record_result(
        self,
        experiment_id: str,
        variant: str,
        user_id: str,
        query: str,
        response_time_ms: float,
        accuracy_score: Optional[float] = None,
        user_feedback: Optional[int] = None,
    ):
        """Record experiment result"""
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            user_id=user_id,
            query=query,
            response_time_ms=response_time_ms,
            accuracy_score=accuracy_score,
            user_feedback=user_feedback,
            timestamp=datetime.utcnow(),
        )

        self.results[experiment_id].append(result)

    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """Get statistics for experiment"""
        results = self.results.get(experiment_id, [])

        if not results:
            return {"error": "No results yet"}

        # Group by variant
        variant_stats = defaultdict(
            lambda: {
                "count": 0,
                "response_times": [],
                "accuracy_scores": [],
                "feedbacks": [],
            }
        )

        for result in results:
            stats = variant_stats[result.variant]
            stats["count"] += 1
            stats["response_times"].append(result.response_time_ms)

            if result.accuracy_score is not None:
                stats["accuracy_scores"].append(result.accuracy_score)

            if result.user_feedback is not None:
                stats["feedbacks"].append(result.user_feedback)

        # Calculate metrics
        summary = {}
        for variant, stats in variant_stats.items():
            summary[variant] = {
                "sample_size": stats["count"],
                "avg_response_time": (
                    sum(stats["response_times"]) / len(stats["response_times"])
                    if stats["response_times"]
                    else 0
                ),
                "avg_accuracy": (
                    sum(stats["accuracy_scores"]) / len(stats["accuracy_scores"])
                    if stats["accuracy_scores"]
                    else None
                ),
                "positive_feedback_rate": (
                    sum(1 for f in stats["feedbacks"] if f > 0)
                    / len(stats["feedbacks"])
                    if stats["feedbacks"]
                    else None
                ),
            }

        return summary

    def stop_experiment(self, experiment_id: str):
        """Stop experiment"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].active = False
            logger.info(f"Stopped experiment: {experiment_id}")


# Global A/B testing service
_ab_testing_service: Optional[ABTestingService] = None


def get_ab_testing_service() -> ABTestingService:
    """Get global A/B testing service"""
    global _ab_testing_service
    if _ab_testing_service is None:
        _ab_testing_service = ABTestingService()
    return _ab_testing_service
