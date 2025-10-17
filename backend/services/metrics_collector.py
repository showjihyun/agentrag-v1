# Performance Metrics Collection Service
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricStats:
    """Statistical summary of metrics"""

    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class MetricsCollector:
    """
    Collects and aggregates performance metrics for the RAG system.

    Tracks:
    - Query response times
    - Vector search accuracy
    - Cache hit rates
    - Agent performance
    - LLM token usage
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._lock = asyncio.Lock()

    async def record_query_latency(
        self,
        latency_ms: float,
        mode: str,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record query latency metric"""
        metric_labels = {"mode": mode, "success": str(success), **(labels or {})}

        await self._record_metric("query_latency_ms", latency_ms, metric_labels)

    async def record_vector_search(
        self,
        latency_ms: float,
        num_results: int,
        top_k: int,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record vector search metrics"""
        metric_labels = {
            "num_results": str(num_results),
            "top_k": str(top_k),
            **(labels or {}),
        }

        await self._record_metric("vector_search_latency_ms", latency_ms, metric_labels)

        # Record retrieval rate
        retrieval_rate = num_results / top_k if top_k > 0 else 0
        await self._record_metric(
            "vector_search_retrieval_rate", retrieval_rate, metric_labels
        )

    async def record_cache_hit(
        self, hit: bool, cache_type: str, labels: Optional[Dict[str, str]] = None
    ):
        """Record cache hit/miss"""
        metric_labels = {"cache_type": cache_type, "hit": str(hit), **(labels or {})}

        await self._record_metric("cache_access", 1.0 if hit else 0.0, metric_labels)

    async def record_agent_execution(
        self,
        agent_name: str,
        latency_ms: float,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record agent execution metrics"""
        metric_labels = {"agent": agent_name, "success": str(success), **(labels or {})}

        await self._record_metric("agent_latency_ms", latency_ms, metric_labels)

    async def record_llm_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record LLM usage metrics"""
        metric_labels = {"provider": provider, "model": model, **(labels or {})}

        await self._record_metric(
            "llm_prompt_tokens", float(prompt_tokens), metric_labels
        )

        await self._record_metric(
            "llm_completion_tokens", float(completion_tokens), metric_labels
        )

        await self._record_metric("llm_latency_ms", latency_ms, metric_labels)

    async def _record_metric(
        self, metric_name: str, value: float, labels: Dict[str, str]
    ):
        """Internal method to record a metric"""
        async with self._lock:
            point = MetricPoint(timestamp=datetime.utcnow(), value=value, labels=labels)
            self.metrics[metric_name].append(point)

    async def get_stats(
        self,
        metric_name: str,
        time_window_minutes: int = 60,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[MetricStats]:
        """Get statistical summary for a metric"""
        async with self._lock:
            if metric_name not in self.metrics:
                return None

            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            # Filter by time and labels
            values = []
            for point in self.metrics[metric_name]:
                if point.timestamp < cutoff_time:
                    continue

                if labels:
                    if not all(point.labels.get(k) == v for k, v in labels.items()):
                        continue

                values.append(point.value)

            if not values:
                return None

            values.sort()
            count = len(values)

            return MetricStats(
                count=count,
                sum=sum(values),
                min=min(values),
                max=max(values),
                avg=sum(values) / count,
                p50=values[int(count * 0.5)],
                p95=values[int(count * 0.95)],
                p99=values[int(count * 0.99)],
            )

    async def get_cache_hit_rate(
        self, cache_type: str, time_window_minutes: int = 60
    ) -> float:
        """Calculate cache hit rate"""
        async with self._lock:
            if "cache_access" not in self.metrics:
                return 0.0

            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            hits = 0
            total = 0

            for point in self.metrics["cache_access"]:
                if point.timestamp < cutoff_time:
                    continue

                if point.labels.get("cache_type") != cache_type:
                    continue

                total += 1
                if point.value > 0:
                    hits += 1

            return hits / total if total > 0 else 0.0

    async def get_agent_success_rate(
        self, agent_name: str, time_window_minutes: int = 60
    ) -> float:
        """Calculate agent success rate"""
        async with self._lock:
            if "agent_latency_ms" not in self.metrics:
                return 0.0

            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            successes = 0
            total = 0

            for point in self.metrics["agent_latency_ms"]:
                if point.timestamp < cutoff_time:
                    continue

                if point.labels.get("agent") != agent_name:
                    continue

                total += 1
                if point.labels.get("success") == "True":
                    successes += 1

            return successes / total if total > 0 else 0.0

    async def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

            for metric_name in self.metrics:
                # Remove old points
                while (
                    self.metrics[metric_name]
                    and self.metrics[metric_name][0].timestamp < cutoff_time
                ):
                    self.metrics[metric_name].popleft()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
