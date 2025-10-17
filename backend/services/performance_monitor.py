"""
Performance monitoring service for hybrid RAG system.

Tracks timing metrics, confidence scores, error rates, and provides
analytics for path effectiveness and system performance.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis

from backend.models.hybrid import QueryMode, PathSource

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked by the performance monitor."""

    TIMING = "timing"
    CONFIDENCE = "confidence"
    ERROR = "error"
    CACHE = "cache"
    MODE_USAGE = "mode_usage"


@dataclass
class TimingMetrics:
    """Timing metrics for a query execution.

    Requirements: 11.1, 11.3
    """

    query_id: str
    mode: str
    speculative_time: Optional[float] = None  # seconds
    agentic_time: Optional[float] = None  # seconds
    total_time: float = 0.0  # seconds
    first_response_time: Optional[float] = None  # Time to first chunk
    path_completed_first: Optional[str] = None  # "speculative" or "agentic"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        # Determine which path completed first
        if self.speculative_time and self.agentic_time:
            self.path_completed_first = (
                "speculative"
                if self.speculative_time < self.agentic_time
                else "agentic"
            )
        elif self.speculative_time:
            self.path_completed_first = "speculative"
        elif self.agentic_time:
            self.path_completed_first = "agentic"


@dataclass
class ConfidenceMetrics:
    """Confidence score tracking for responses.

    Requirements: 11.2
    """

    query_id: str
    mode: str
    initial_speculative_confidence: Optional[float] = None
    final_agentic_confidence: Optional[float] = None
    confidence_improvement: Optional[float] = None  # final - initial
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        # Calculate improvement
        if (
            self.initial_speculative_confidence is not None
            and self.final_agentic_confidence is not None
        ):
            self.confidence_improvement = (
                self.final_agentic_confidence - self.initial_speculative_confidence
            )


@dataclass
class ErrorMetrics:
    """Error tracking for path failures.

    Requirements: 11.4, 11.5
    """

    query_id: str
    mode: str
    path: str  # "speculative", "agentic", or "both"
    error_type: str
    error_message: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceMonitor:
    """
    Performance monitoring service for hybrid RAG system.

    Features:
    - Timing metrics collection for both paths
    - Confidence score tracking and improvement analysis
    - Error rate monitoring per path
    - Mode usage pattern tracking
    - Performance analytics and reporting
    - Alert triggering for degraded performance

    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        metrics_ttl: int = 86400 * 7,  # 7 days
        alert_threshold_error_rate: float = 0.1,  # 10% error rate
        alert_threshold_slow_response: float = 5.0,  # 5 seconds
        metrics_prefix: str = "metrics:",
    ):
        """
        Initialize PerformanceMonitor.

        Args:
            redis_client: Redis client for storing metrics
            metrics_ttl: Time-to-live for metrics in seconds (default: 7 days)
            alert_threshold_error_rate: Error rate threshold for alerts (0-1)
            alert_threshold_slow_response: Response time threshold for alerts (seconds)
            metrics_prefix: Prefix for Redis keys
        """
        self.redis_client = redis_client
        self.metrics_ttl = metrics_ttl
        self.alert_threshold_error_rate = alert_threshold_error_rate
        self.alert_threshold_slow_response = alert_threshold_slow_response
        self.metrics_prefix = metrics_prefix

        logger.info(
            f"PerformanceMonitor initialized with "
            f"metrics_ttl={metrics_ttl}s, "
            f"error_rate_threshold={alert_threshold_error_rate}, "
            f"slow_response_threshold={alert_threshold_slow_response}s"
        )

    def _get_key(self, metric_type: MetricType, suffix: str = "") -> str:
        """Generate Redis key for metric storage."""
        key = f"{self.metrics_prefix}{metric_type.value}"
        if suffix:
            key = f"{key}:{suffix}"
        return key

    async def log_timing_metrics(
        self,
        query_id: str,
        mode: QueryMode,
        speculative_time: Optional[float] = None,
        agentic_time: Optional[float] = None,
        total_time: float = 0.0,
        first_response_time: Optional[float] = None,
    ) -> None:
        """
        Log timing metrics for a query execution.

        Tracks:
        - Speculative path completion time
        - Agentic path completion time
        - Which path completed first
        - End-to-end query processing time
        - Time to first response

        Args:
            query_id: Query identifier
            mode: Query processing mode
            speculative_time: Time taken by speculative path (seconds)
            agentic_time: Time taken by agentic path (seconds)
            total_time: Total end-to-end processing time (seconds)
            first_response_time: Time to first response chunk (seconds)

        Requirements: 11.1, 11.3
        """
        try:
            metrics = TimingMetrics(
                query_id=query_id,
                mode=mode.value,
                speculative_time=speculative_time,
                agentic_time=agentic_time,
                total_time=total_time,
                first_response_time=first_response_time,
            )

            # Store in Redis as sorted set (by timestamp)
            key = self._get_key(MetricType.TIMING)
            timestamp_score = time.time()

            await self.redis_client.zadd(
                key, {json.dumps(asdict(metrics), default=str): timestamp_score}
            )

            # Set TTL
            await self.redis_client.expire(key, self.metrics_ttl)

            # Update aggregated stats
            await self._update_timing_stats(metrics)

            # Check for performance degradation
            await self._check_timing_alerts(metrics)

            logger.info(
                f"Logged timing metrics for {query_id}: "
                f"mode={mode.value}, total={total_time:.2f}s, "
                f"spec={speculative_time:.2f}s if speculative_time else 'N/A', "
                f"agent={agentic_time:.2f}s if agentic_time else 'N/A', "
                f"first_completed={metrics.path_completed_first or 'N/A'}"
            )

        except Exception as e:
            logger.error(f"Failed to log timing metrics: {e}")

    async def log_confidence_metrics(
        self,
        query_id: str,
        mode: QueryMode,
        initial_speculative_confidence: Optional[float] = None,
        final_agentic_confidence: Optional[float] = None,
    ) -> None:
        """
        Log confidence score metrics for a query.

        Tracks:
        - Initial speculative confidence
        - Final agentic confidence
        - Confidence improvement over time

        Args:
            query_id: Query identifier
            mode: Query processing mode
            initial_speculative_confidence: Initial confidence from speculative path
            final_agentic_confidence: Final confidence from agentic path

        Requirements: 11.2
        """
        try:
            metrics = ConfidenceMetrics(
                query_id=query_id,
                mode=mode.value,
                initial_speculative_confidence=initial_speculative_confidence,
                final_agentic_confidence=final_agentic_confidence,
            )

            # Store in Redis
            key = self._get_key(MetricType.CONFIDENCE)
            timestamp_score = time.time()

            await self.redis_client.zadd(
                key, {json.dumps(asdict(metrics), default=str): timestamp_score}
            )

            # Set TTL
            await self.redis_client.expire(key, self.metrics_ttl)

            # Update aggregated stats
            await self._update_confidence_stats(metrics)

            logger.info(
                f"Logged confidence metrics for {query_id}: "
                f"initial={initial_speculative_confidence:.3f if initial_speculative_confidence else 'N/A'}, "
                f"final={final_agentic_confidence:.3f if final_agentic_confidence else 'N/A'}, "
                f"improvement={metrics.confidence_improvement:.3f if metrics.confidence_improvement else 'N/A'}"
            )

        except Exception as e:
            logger.error(f"Failed to log confidence metrics: {e}")

    async def log_error_metrics(
        self,
        query_id: str,
        mode: QueryMode,
        path: PathSource,
        error_type: str,
        error_message: str,
    ) -> None:
        """
        Log error metrics for path failures.

        Tracks:
        - Failure rates per path
        - Error types and frequencies
        - Error patterns over time

        Args:
            query_id: Query identifier
            mode: Query processing mode
            path: Path that failed (speculative/agentic/hybrid)
            error_type: Type of error (e.g., "timeout", "llm_error", "search_error")
            error_message: Error message

        Requirements: 11.4, 11.5
        """
        try:
            metrics = ErrorMetrics(
                query_id=query_id,
                mode=mode.value,
                path=path.value,
                error_type=error_type,
                error_message=error_message[:200],  # Truncate long messages
            )

            # Store in Redis
            key = self._get_key(MetricType.ERROR)
            timestamp_score = time.time()

            await self.redis_client.zadd(
                key, {json.dumps(asdict(metrics), default=str): timestamp_score}
            )

            # Set TTL
            await self.redis_client.expire(key, self.metrics_ttl)

            # Update error rate stats
            await self._update_error_stats(metrics)

            # Check for high error rates
            await self._check_error_alerts(metrics)

            logger.warning(
                f"Logged error metrics for {query_id}: "
                f"path={path.value}, type={error_type}"
            )

        except Exception as e:
            logger.error(f"Failed to log error metrics: {e}")

    async def log_mode_usage(
        self, mode: QueryMode, session_id: Optional[str] = None
    ) -> None:
        """
        Log mode usage patterns.

        Tracks which modes are being used most frequently.

        Args:
            mode: Query processing mode used
            session_id: Optional session identifier

        Requirements: 11.6
        """
        try:
            key = self._get_key(MetricType.MODE_USAGE)

            # Increment counter for this mode
            await self.redis_client.hincrby(key, mode.value, 1)

            # Set TTL
            await self.redis_client.expire(key, self.metrics_ttl)

            logger.debug(f"Logged mode usage: {mode.value}")

        except Exception as e:
            logger.error(f"Failed to log mode usage: {e}")

    async def _update_timing_stats(self, metrics: TimingMetrics) -> None:
        """Update aggregated timing statistics."""
        try:
            stats_key = self._get_key(MetricType.TIMING, "stats")

            # Update counters and sums for averages
            pipe = self.redis_client.pipeline()

            # Total queries
            pipe.hincrby(stats_key, "total_queries", 1)

            # Mode-specific counters
            pipe.hincrby(stats_key, f"{metrics.mode}_count", 1)

            # Sum of times for averages
            if metrics.speculative_time:
                pipe.hincrbyfloat(
                    stats_key, "speculative_time_sum", metrics.speculative_time
                )
                pipe.hincrby(stats_key, "speculative_count", 1)

            if metrics.agentic_time:
                pipe.hincrbyfloat(stats_key, "agentic_time_sum", metrics.agentic_time)
                pipe.hincrby(stats_key, "agentic_count", 1)

            pipe.hincrbyfloat(stats_key, "total_time_sum", metrics.total_time)

            # Path completion tracking
            if metrics.path_completed_first:
                pipe.hincrby(
                    stats_key, f"{metrics.path_completed_first}_first_count", 1
                )

            await pipe.execute()
            await self.redis_client.expire(stats_key, self.metrics_ttl)

        except Exception as e:
            logger.error(f"Failed to update timing stats: {e}")

    async def _update_confidence_stats(self, metrics: ConfidenceMetrics) -> None:
        """Update aggregated confidence statistics."""
        try:
            stats_key = self._get_key(MetricType.CONFIDENCE, "stats")

            pipe = self.redis_client.pipeline()

            if metrics.initial_speculative_confidence is not None:
                pipe.hincrbyfloat(
                    stats_key,
                    "speculative_confidence_sum",
                    metrics.initial_speculative_confidence,
                )
                pipe.hincrby(stats_key, "speculative_confidence_count", 1)

            if metrics.final_agentic_confidence is not None:
                pipe.hincrbyfloat(
                    stats_key,
                    "agentic_confidence_sum",
                    metrics.final_agentic_confidence,
                )
                pipe.hincrby(stats_key, "agentic_confidence_count", 1)

            if metrics.confidence_improvement is not None:
                pipe.hincrbyfloat(
                    stats_key,
                    "confidence_improvement_sum",
                    metrics.confidence_improvement,
                )
                pipe.hincrby(stats_key, "confidence_improvement_count", 1)

            await pipe.execute()
            await self.redis_client.expire(stats_key, self.metrics_ttl)

        except Exception as e:
            logger.error(f"Failed to update confidence stats: {e}")

    async def _update_error_stats(self, metrics: ErrorMetrics) -> None:
        """Update aggregated error statistics."""
        try:
            stats_key = self._get_key(MetricType.ERROR, "stats")

            pipe = self.redis_client.pipeline()

            # Total errors
            pipe.hincrby(stats_key, "total_errors", 1)

            # Per-path errors
            pipe.hincrby(stats_key, f"{metrics.path}_errors", 1)

            # Per-type errors
            pipe.hincrby(stats_key, f"type_{metrics.error_type}", 1)

            # Per-mode errors
            pipe.hincrby(stats_key, f"{metrics.mode}_errors", 1)

            await pipe.execute()
            await self.redis_client.expire(stats_key, self.metrics_ttl)

        except Exception as e:
            logger.error(f"Failed to update error stats: {e}")

    async def _check_timing_alerts(self, metrics: TimingMetrics) -> None:
        """
        Check for timing-based performance degradation and trigger alerts.

        Requirements: 11.5
        """
        try:
            # Check if response time exceeds threshold
            if metrics.total_time > self.alert_threshold_slow_response:
                logger.warning(
                    f"PERFORMANCE ALERT: Slow response detected for query {metrics.query_id} - "
                    f"total_time={metrics.total_time:.2f}s exceeds threshold "
                    f"of {self.alert_threshold_slow_response}s"
                )

                # Store alert
                alert_key = self._get_key(MetricType.TIMING, "alerts")
                alert_data = {
                    "query_id": metrics.query_id,
                    "alert_type": "slow_response",
                    "total_time": metrics.total_time,
                    "threshold": self.alert_threshold_slow_response,
                    "timestamp": datetime.now().isoformat(),
                }

                await self.redis_client.zadd(
                    alert_key, {json.dumps(alert_data): time.time()}
                )
                await self.redis_client.expire(alert_key, self.metrics_ttl)

        except Exception as e:
            logger.error(f"Failed to check timing alerts: {e}")

    async def _check_error_alerts(self, metrics: ErrorMetrics) -> None:
        """
        Check for high error rates and trigger alerts.

        Requirements: 11.5
        """
        try:
            # Get recent error rate for this path
            stats_key = self._get_key(MetricType.ERROR, "stats")
            timing_stats_key = self._get_key(MetricType.TIMING, "stats")

            # Get error count and total query count
            path_errors = await self.redis_client.hget(
                stats_key, f"{metrics.path}_errors"
            )
            total_queries = await self.redis_client.hget(
                timing_stats_key, "total_queries"
            )

            if path_errors and total_queries:
                error_count = int(path_errors)
                query_count = int(total_queries)

                if query_count > 0:
                    error_rate = error_count / query_count

                    if error_rate > self.alert_threshold_error_rate:
                        logger.error(
                            f"PERFORMANCE ALERT: High error rate detected for {metrics.path} path - "
                            f"error_rate={error_rate:.2%} exceeds threshold "
                            f"of {self.alert_threshold_error_rate:.2%} "
                            f"({error_count}/{query_count} queries)"
                        )

                        # Store alert
                        alert_key = self._get_key(MetricType.ERROR, "alerts")
                        alert_data = {
                            "path": metrics.path,
                            "alert_type": "high_error_rate",
                            "error_rate": error_rate,
                            "error_count": error_count,
                            "query_count": query_count,
                            "threshold": self.alert_threshold_error_rate,
                            "timestamp": datetime.now().isoformat(),
                        }

                        await self.redis_client.zadd(
                            alert_key, {json.dumps(alert_data): time.time()}
                        )
                        await self.redis_client.expire(alert_key, self.metrics_ttl)

        except Exception as e:
            logger.error(f"Failed to check error alerts: {e}")

    async def get_timing_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated timing statistics.

        Args:
            time_window_hours: Time window for stats (hours)

        Returns:
            Dictionary with timing statistics

        Requirements: 11.1, 11.3, 11.6
        """
        try:
            stats_key = self._get_key(MetricType.TIMING, "stats")
            stats = await self.redis_client.hgetall(stats_key)

            if not stats:
                return {}

            # Decode and convert to proper types
            decoded_stats = {
                k.decode() if isinstance(k, bytes) else k: (
                    float(v) if b"." in v else int(v)
                )
                for k, v in stats.items()
            }

            # Calculate averages
            result = {
                "total_queries": decoded_stats.get("total_queries", 0),
                "time_window_hours": time_window_hours,
            }

            # Average times
            if decoded_stats.get("speculative_count", 0) > 0:
                result["avg_speculative_time"] = (
                    decoded_stats.get("speculative_time_sum", 0)
                    / decoded_stats["speculative_count"]
                )

            if decoded_stats.get("agentic_count", 0) > 0:
                result["avg_agentic_time"] = (
                    decoded_stats.get("agentic_time_sum", 0)
                    / decoded_stats["agentic_count"]
                )

            if decoded_stats.get("total_queries", 0) > 0:
                result["avg_total_time"] = (
                    decoded_stats.get("total_time_sum", 0)
                    / decoded_stats["total_queries"]
                )

            # Path completion stats
            spec_first = decoded_stats.get("speculative_first_count", 0)
            agent_first = decoded_stats.get("agentic_first_count", 0)
            total_both = spec_first + agent_first

            if total_both > 0:
                result["speculative_first_percentage"] = (spec_first / total_both) * 100
                result["agentic_first_percentage"] = (agent_first / total_both) * 100

            # Mode usage
            for mode in ["fast", "balanced", "deep"]:
                count = decoded_stats.get(f"{mode}_count", 0)
                result[f"{mode}_mode_count"] = count

            return result

        except Exception as e:
            logger.error(f"Failed to get timing stats: {e}")
            return {}

    async def get_confidence_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated confidence statistics.

        Args:
            time_window_hours: Time window for stats (hours)

        Returns:
            Dictionary with confidence statistics

        Requirements: 11.2, 11.6
        """
        try:
            stats_key = self._get_key(MetricType.CONFIDENCE, "stats")
            stats = await self.redis_client.hgetall(stats_key)

            if not stats:
                return {}

            # Decode and convert
            decoded_stats = {
                k.decode() if isinstance(k, bytes) else k: (
                    float(v) if b"." in v else int(v)
                )
                for k, v in stats.items()
            }

            result = {"time_window_hours": time_window_hours}

            # Average confidence scores
            if decoded_stats.get("speculative_confidence_count", 0) > 0:
                result["avg_speculative_confidence"] = (
                    decoded_stats.get("speculative_confidence_sum", 0)
                    / decoded_stats["speculative_confidence_count"]
                )

            if decoded_stats.get("agentic_confidence_count", 0) > 0:
                result["avg_agentic_confidence"] = (
                    decoded_stats.get("agentic_confidence_sum", 0)
                    / decoded_stats["agentic_confidence_count"]
                )

            # Average confidence improvement
            if decoded_stats.get("confidence_improvement_count", 0) > 0:
                result["avg_confidence_improvement"] = (
                    decoded_stats.get("confidence_improvement_sum", 0)
                    / decoded_stats["confidence_improvement_count"]
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get confidence stats: {e}")
            return {}

    async def get_error_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated error statistics.

        Args:
            time_window_hours: Time window for stats (hours)

        Returns:
            Dictionary with error statistics

        Requirements: 11.4, 11.5, 11.6
        """
        try:
            stats_key = self._get_key(MetricType.ERROR, "stats")
            timing_stats_key = self._get_key(MetricType.TIMING, "stats")

            error_stats = await self.redis_client.hgetall(stats_key)
            timing_stats = await self.redis_client.hgetall(timing_stats_key)

            if not error_stats:
                return {"total_errors": 0, "error_rate": 0.0}

            # Decode stats
            decoded_errors = {
                k.decode() if isinstance(k, bytes) else k: int(v)
                for k, v in error_stats.items()
            }

            total_queries = 0
            if timing_stats:
                total_queries_bytes = timing_stats.get(b"total_queries", b"0")
                total_queries = int(total_queries_bytes)

            result = {
                "total_errors": decoded_errors.get("total_errors", 0),
                "total_queries": total_queries,
                "time_window_hours": time_window_hours,
            }

            # Calculate error rate
            if total_queries > 0:
                result["error_rate"] = (
                    decoded_errors.get("total_errors", 0) / total_queries
                )
            else:
                result["error_rate"] = 0.0

            # Per-path error rates
            for path in ["speculative", "agentic", "hybrid"]:
                path_errors = decoded_errors.get(f"{path}_errors", 0)
                result[f"{path}_errors"] = path_errors
                if total_queries > 0:
                    result[f"{path}_error_rate"] = path_errors / total_queries

            # Error types
            error_types = {}
            for key, value in decoded_errors.items():
                if key.startswith("type_"):
                    error_type = key.replace("type_", "")
                    error_types[error_type] = value

            result["error_types"] = error_types

            return result

        except Exception as e:
            logger.error(f"Failed to get error stats: {e}")
            return {}

    async def get_mode_usage_stats(self) -> Dict[str, int]:
        """
        Get mode usage statistics.

        Returns:
            Dictionary with mode usage counts

        Requirements: 11.6
        """
        try:
            key = self._get_key(MetricType.MODE_USAGE)
            stats = await self.redis_client.hgetall(key)

            if not stats:
                return {}

            # Decode and convert
            result = {
                k.decode() if isinstance(k, bytes) else k: int(v)
                for k, v in stats.items()
            }

            return result

        except Exception as e:
            logger.error(f"Failed to get mode usage stats: {e}")
            return {}

    async def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent performance alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts

        Requirements: 11.5
        """
        try:
            alerts = []

            # Get timing alerts
            timing_alert_key = self._get_key(MetricType.TIMING, "alerts")
            timing_alerts = await self.redis_client.zrevrange(
                timing_alert_key, 0, limit - 1, withscores=False
            )

            for alert_json in timing_alerts:
                alert_data = json.loads(alert_json)
                alert_data["category"] = "timing"
                alerts.append(alert_data)

            # Get error alerts
            error_alert_key = self._get_key(MetricType.ERROR, "alerts")
            error_alerts = await self.redis_client.zrevrange(
                error_alert_key, 0, limit - 1, withscores=False
            )

            for alert_json in error_alerts:
                alert_data = json.loads(alert_json)
                alert_data["category"] = "error"
                alerts.append(alert_data)

            # Sort by timestamp and limit
            alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return alerts[:limit]

        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
