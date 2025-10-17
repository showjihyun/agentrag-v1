"""
A/B Testing Framework for Adaptive Routing

Enables experimentation with different routing strategies, thresholds,
and configurations to optimize system performance.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from backend.db.database import get_db
from backend.services.adaptive_metrics import AdaptiveMetricsCollector

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment status"""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(str, Enum):
    """Variant type"""

    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class Variant:
    """Experiment variant configuration"""

    id: str
    name: str
    type: VariantType
    traffic_percentage: float
    config: Dict[str, Any]
    description: str = ""

    # Metrics
    queries_count: int = 0
    avg_latency: float = 0.0
    avg_satisfaction: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    routing_accuracy: float = 0.0


@dataclass
class Experiment:
    """A/B test experiment"""

    id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: List[Variant]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Configuration
    min_sample_size: int = 1000
    confidence_level: float = 0.95

    # Results
    winner: Optional[str] = None
    statistical_significance: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Experiment analysis result"""

    experiment_id: str
    winner: Optional[str]
    statistical_significance: float
    confidence_level: float
    metrics_comparison: Dict[str, Dict[str, float]]
    recommendation: str
    details: Dict[str, Any]


class ABTestingFramework:
    """
    A/B Testing Framework for routing strategies

    Features:
    - Create and manage experiments
    - Traffic splitting
    - Variant assignment
    - Metrics collection
    - Statistical analysis
    - Winner determination
    """

    def __init__(self, metrics_collector: AdaptiveMetricsCollector):
        self.metrics = metrics_collector
        self.experiments: Dict[str, Experiment] = {}
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant_id

    async def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        min_sample_size: int = 1000,
        confidence_level: float = 0.95,
    ) -> Experiment:
        """
        Create a new A/B test experiment

        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variant configurations
            min_sample_size: Minimum samples per variant
            confidence_level: Statistical confidence level

        Returns:
            Created experiment
        """
        # Validate traffic percentages
        total_traffic = sum(v.get("traffic_percentage", 0) for v in variants)
        if abs(total_traffic - 1.0) > 0.01:
            raise ValueError(
                f"Traffic percentages must sum to 1.0, got {total_traffic}"
            )

        # Create experiment
        experiment_id = self._generate_experiment_id(name)

        variant_objects = []
        for v in variants:
            variant = Variant(
                id=f"{experiment_id}_{v['name']}",
                name=v["name"],
                type=VariantType(v.get("type", "treatment")),
                traffic_percentage=v["traffic_percentage"],
                config=v["config"],
                description=v.get("description", ""),
            )
            variant_objects.append(variant)

        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT,
            variants=variant_objects,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
        )

        self.experiments[experiment_id] = experiment

        logger.info(
            f"Created experiment: {experiment_id} with {len(variants)} variants"
        )
        return experiment

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(
                f"Can only start DRAFT experiments, current: {experiment.status}"
            )

        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.now()
        experiment.updated_at = datetime.now()

        logger.info(f"Started experiment: {experiment_id}")
        return True

    async def pause_experiment(self, experiment_id: str) -> bool:
        """Pause a running experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Can only pause RUNNING experiments")

        experiment.status = ExperimentStatus.PAUSED
        experiment.updated_at = datetime.now()

        logger.info(f"Paused experiment: {experiment_id}")
        return True

    async def resume_experiment(self, experiment_id: str) -> bool:
        """Resume a paused experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.PAUSED:
            raise ValueError(f"Can only resume PAUSED experiments")

        experiment.status = ExperimentStatus.RUNNING
        experiment.updated_at = datetime.now()

        logger.info(f"Resumed experiment: {experiment_id}")
        return True

    async def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.now()
        experiment.updated_at = datetime.now()

        logger.info(f"Stopped experiment: {experiment_id}")
        return True

    async def assign_variant(
        self, user_id: str, experiment_id: str
    ) -> Optional[Variant]:
        """
        Assign user to a variant

        Uses consistent hashing to ensure same user always gets same variant

        Args:
            user_id: User identifier
            experiment_id: Experiment ID

        Returns:
            Assigned variant or None if experiment not running
        """
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        # Check if already assigned
        assignment_key = f"{experiment_id}:{user_id}"
        if assignment_key in self.variant_assignments:
            variant_id = self.variant_assignments[assignment_key]
            return next((v for v in experiment.variants if v.id == variant_id), None)

        # Assign using consistent hashing
        hash_value = self._hash_user(user_id, experiment_id)

        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if hash_value <= cumulative:
                self.variant_assignments[assignment_key] = variant.id
                logger.debug(f"Assigned user {user_id} to variant {variant.name}")
                return variant

        # Fallback to last variant
        last_variant = experiment.variants[-1]
        self.variant_assignments[assignment_key] = last_variant.id
        return last_variant

    async def record_outcome(
        self, experiment_id: str, variant_id: str, metrics: Dict[str, float]
    ):
        """
        Record experiment outcome

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            metrics: Outcome metrics (latency, satisfaction, etc.)
        """
        if experiment_id not in self.experiments:
            return

        experiment = self.experiments[experiment_id]
        variant = next((v for v in experiment.variants if v.id == variant_id), None)

        if not variant:
            return

        # Update variant metrics (running average)
        n = variant.queries_count
        variant.queries_count += 1

        for metric_name, value in metrics.items():
            if metric_name == "latency":
                variant.avg_latency = (variant.avg_latency * n + value) / (n + 1)
            elif metric_name == "satisfaction":
                variant.avg_satisfaction = (variant.avg_satisfaction * n + value) / (
                    n + 1
                )
            elif metric_name == "error_rate":
                variant.error_rate = (variant.error_rate * n + value) / (n + 1)
            elif metric_name == "cache_hit_rate":
                variant.cache_hit_rate = (variant.cache_hit_rate * n + value) / (n + 1)
            elif metric_name == "routing_accuracy":
                variant.routing_accuracy = (variant.routing_accuracy * n + value) / (
                    n + 1
                )

    async def analyze_results(self, experiment_id: str) -> ExperimentResult:
        """
        Analyze experiment results and determine winner

        Uses statistical significance testing (t-test) to compare variants

        Args:
            experiment_id: Experiment ID

        Returns:
            Analysis result with winner and recommendations
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]

        # Check minimum sample size
        for variant in experiment.variants:
            if variant.queries_count < experiment.min_sample_size:
                return ExperimentResult(
                    experiment_id=experiment_id,
                    winner=None,
                    statistical_significance=0.0,
                    confidence_level=experiment.confidence_level,
                    metrics_comparison={},
                    recommendation="Insufficient data - continue experiment",
                    details={
                        "min_sample_size": experiment.min_sample_size,
                        "current_samples": {
                            v.name: v.queries_count for v in experiment.variants
                        },
                    },
                )

        # Compare variants
        control = next(
            (v for v in experiment.variants if v.type == VariantType.CONTROL), None
        )
        treatments = [v for v in experiment.variants if v.type == VariantType.TREATMENT]

        if not control:
            control = experiment.variants[0]
            treatments = experiment.variants[1:]

        # Calculate composite score for each variant
        scores = {}
        for variant in experiment.variants:
            score = self._calculate_variant_score(variant)
            scores[variant.id] = score

        # Find winner
        winner_id = max(scores, key=scores.get)
        winner = next(v for v in experiment.variants if v.id == winner_id)

        # Calculate statistical significance (simplified)
        significance = self._calculate_significance(control, winner)

        # Build metrics comparison
        metrics_comparison = {}
        for variant in experiment.variants:
            metrics_comparison[variant.name] = {
                "latency": variant.avg_latency,
                "satisfaction": variant.avg_satisfaction,
                "error_rate": variant.error_rate,
                "cache_hit_rate": variant.cache_hit_rate,
                "routing_accuracy": variant.routing_accuracy,
                "score": scores[variant.id],
            }

        # Generate recommendation
        if significance >= experiment.confidence_level:
            if winner.type == VariantType.CONTROL:
                recommendation = "Keep current configuration (control wins)"
            else:
                recommendation = f"Deploy variant '{winner.name}' (statistically significant improvement)"
        else:
            recommendation = (
                "No clear winner - continue experiment or increase sample size"
            )

        result = ExperimentResult(
            experiment_id=experiment_id,
            winner=winner.name if significance >= experiment.confidence_level else None,
            statistical_significance=significance,
            confidence_level=experiment.confidence_level,
            metrics_comparison=metrics_comparison,
            recommendation=recommendation,
            details={
                "control": control.name,
                "treatments": [t.name for t in treatments],
                "sample_sizes": {v.name: v.queries_count for v in experiment.variants},
            },
        )

        # Update experiment
        experiment.winner = result.winner
        experiment.statistical_significance = significance
        experiment.results = {
            "metrics_comparison": metrics_comparison,
            "recommendation": recommendation,
        }

        return result

    async def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        return self.experiments.get(experiment_id)

    async def list_experiments(
        self, status: Optional[ExperimentStatus] = None
    ) -> List[Experiment]:
        """List all experiments, optionally filtered by status"""
        experiments = list(self.experiments.values())

        if status:
            experiments = [e for e in experiments if e.status == status]

        return sorted(experiments, key=lambda e: e.created_at, reverse=True)

    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{name}:{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _hash_user(self, user_id: str, experiment_id: str) -> float:
        """Hash user to value between 0 and 1"""
        hash_input = f"{user_id}:{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        return (hash_value % 10000) / 10000.0

    def _calculate_variant_score(self, variant: Variant) -> float:
        """
        Calculate composite score for variant

        Weighted combination of metrics:
        - Latency: 30% (lower is better)
        - Satisfaction: 30% (higher is better)
        - Error rate: 20% (lower is better)
        - Cache hit rate: 10% (higher is better)
        - Routing accuracy: 10% (higher is better)
        """
        # Normalize latency (assume 0-10s range)
        latency_score = max(0, 1 - variant.avg_latency / 10.0)

        # Satisfaction (0-5 scale)
        satisfaction_score = variant.avg_satisfaction / 5.0

        # Error rate (0-1 scale, invert)
        error_score = 1 - variant.error_rate

        # Cache hit rate (0-1 scale)
        cache_score = variant.cache_hit_rate

        # Routing accuracy (0-1 scale)
        routing_score = variant.routing_accuracy

        # Weighted sum
        score = (
            latency_score * 0.30
            + satisfaction_score * 0.30
            + error_score * 0.20
            + cache_score * 0.10
            + routing_score * 0.10
        )

        return score

    def _calculate_significance(self, control: Variant, treatment: Variant) -> float:
        """
        Calculate statistical significance (simplified)

        In production, use proper t-test or chi-square test
        """
        # Simplified significance based on sample size and score difference
        control_score = self._calculate_variant_score(control)
        treatment_score = self._calculate_variant_score(treatment)

        score_diff = abs(treatment_score - control_score)
        min_samples = min(control.queries_count, treatment.queries_count)

        # Simple heuristic: larger difference and more samples = higher significance
        if min_samples < 100:
            return 0.0
        elif min_samples < 500:
            base_significance = 0.70
        elif min_samples < 1000:
            base_significance = 0.85
        else:
            base_significance = 0.95

        # Adjust by score difference
        if score_diff < 0.05:
            return base_significance * 0.5
        elif score_diff < 0.10:
            return base_significance * 0.8
        else:
            return base_significance

    async def get_active_experiments_for_user(
        self, user_id: str
    ) -> List[Tuple[Experiment, Variant]]:
        """Get all active experiments and assigned variants for a user"""
        results = []

        for experiment in self.experiments.values():
            if experiment.status == ExperimentStatus.RUNNING:
                variant = await self.assign_variant(user_id, experiment.id)
                if variant:
                    results.append((experiment, variant))

        return results
