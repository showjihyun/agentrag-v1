# Search Quality Monitoring Service
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SearchQualityMonitor:
    """
    Monitor and track search quality metrics.

    Tracks:
    - Result count distribution
    - Score statistics (mean, variance, min, max)
    - Low-quality searches (few results, low scores)
    - Search patterns and trends
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics = defaultdict(list)
        self.low_quality_threshold = 0.5  # Score threshold
        self.min_results_threshold = 3  # Minimum expected results

    async def track_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_mode: str = "hybrid",
        latency_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Track a search query and its results.

        Args:
            query: Search query text
            results: List of search results with scores
            search_mode: Search mode used (hybrid, vector, keyword)
            latency_ms: Search latency in milliseconds

        Returns:
            Quality metrics for this search
        """
        try:
            # Extract scores
            scores = [r.get("score", 0.0) for r in results]
            result_count = len(results)

            # Calculate metrics
            metrics = {
                "query": query[:100],  # Truncate for storage
                "timestamp": datetime.utcnow().isoformat(),
                "search_mode": search_mode,
                "result_count": result_count,
                "latency_ms": latency_ms,
            }

            if scores:
                metrics.update(
                    {
                        "avg_score": float(np.mean(scores)),
                        "min_score": float(np.min(scores)),
                        "max_score": float(np.max(scores)),
                        "score_variance": float(np.var(scores)),
                        "score_std": float(np.std(scores)),
                    }
                )

                # Quality indicators
                metrics["is_low_quality"] = (
                    result_count < self.min_results_threshold
                    or metrics["avg_score"] < self.low_quality_threshold
                )
            else:
                metrics.update(
                    {
                        "avg_score": 0.0,
                        "min_score": 0.0,
                        "max_score": 0.0,
                        "score_variance": 0.0,
                        "score_std": 0.0,
                        "is_low_quality": True,
                    }
                )

            # Log quality issues
            if metrics["is_low_quality"]:
                logger.warning(
                    f"Low quality search detected: query='{query[:50]}...', "
                    f"results={result_count}, avg_score={metrics['avg_score']:.3f}"
                )

            # Store in Redis if available
            if self.redis_client:
                await self._store_metrics(metrics)

            # Store in memory
            self.metrics[search_mode].append(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to track search metrics: {e}")
            return {}

    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in Redis"""
        try:
            key = f"search_quality:{metrics['timestamp'][:10]}"  # Daily key
            await self.redis_client.lpush(key, str(metrics))
            await self.redis_client.expire(key, 86400 * 7)  # Keep for 7 days
        except Exception as e:
            logger.debug(f"Failed to store metrics in Redis: {e}")

    async def get_quality_report(
        self, search_mode: Optional[str] = None, time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get quality report for recent searches.

        Args:
            search_mode: Filter by search mode (None for all)
            time_window_minutes: Time window to analyze

        Returns:
            Quality report with statistics
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            # Filter metrics
            all_metrics = []
            for mode, metrics_list in self.metrics.items():
                if search_mode and mode != search_mode:
                    continue

                for m in metrics_list:
                    try:
                        timestamp = datetime.fromisoformat(m["timestamp"])
                        if timestamp >= cutoff_time:
                            all_metrics.append(m)
                    except:
                        continue

            if not all_metrics:
                return {"total_searches": 0, "time_window_minutes": time_window_minutes}

            # Calculate aggregate statistics
            result_counts = [m["result_count"] for m in all_metrics]
            avg_scores = [m["avg_score"] for m in all_metrics if m["avg_score"] > 0]
            latencies = [m["latency_ms"] for m in all_metrics if m.get("latency_ms")]
            low_quality_count = sum(1 for m in all_metrics if m.get("is_low_quality"))

            report = {
                "total_searches": len(all_metrics),
                "time_window_minutes": time_window_minutes,
                "low_quality_rate": (
                    low_quality_count / len(all_metrics) if all_metrics else 0
                ),
                "avg_result_count": (
                    float(np.mean(result_counts)) if result_counts else 0
                ),
                "result_count_std": (
                    float(np.std(result_counts)) if result_counts else 0
                ),
            }

            if avg_scores:
                report.update(
                    {
                        "avg_score": float(np.mean(avg_scores)),
                        "score_std": float(np.std(avg_scores)),
                        "min_score": float(np.min(avg_scores)),
                        "max_score": float(np.max(avg_scores)),
                    }
                )

            if latencies:
                report.update(
                    {
                        "avg_latency_ms": float(np.mean(latencies)),
                        "p50_latency_ms": float(np.percentile(latencies, 50)),
                        "p95_latency_ms": float(np.percentile(latencies, 95)),
                        "p99_latency_ms": float(np.percentile(latencies, 99)),
                    }
                )

            # Mode breakdown
            mode_breakdown = defaultdict(int)
            for m in all_metrics:
                mode_breakdown[m["search_mode"]] += 1
            report["mode_breakdown"] = dict(mode_breakdown)

            return report

        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            return {"error": str(e)}

    def get_low_quality_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent low-quality queries for analysis"""
        low_quality = []

        for metrics_list in self.metrics.values():
            for m in metrics_list:
                if m.get("is_low_quality"):
                    low_quality.append(m)

        # Sort by timestamp (most recent first)
        low_quality.sort(key=lambda x: x["timestamp"], reverse=True)

        return low_quality[:limit]


# Global monitor instance
_quality_monitor: Optional[SearchQualityMonitor] = None


def get_quality_monitor(
    redis_client: Optional[redis.Redis] = None,
) -> SearchQualityMonitor:
    """Get global quality monitor instance"""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = SearchQualityMonitor(redis_client)
    return _quality_monitor
