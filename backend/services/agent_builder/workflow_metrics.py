"""
Workflow Metrics Collector

Prometheus-compatible metrics for workflow monitoring.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Single metric value with labels."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_prometheus(self) -> str:
        """Convert to Prometheus format."""
        if self.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
            return f'{self.name}{{{label_str}}} {self.value}'
        return f'{self.name} {self.value}'


class Counter:
    """Prometheus-style counter metric."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
    
    def inc(self, amount: float = 1, **labels):
        """Increment counter."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        self._values[key] += amount
    
    def get(self, **labels) -> float:
        """Get counter value."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        return self._values.get(key, 0)
    
    def collect(self) -> List[MetricValue]:
        """Collect all values."""
        result = []
        for key, value in self._values.items():
            labels = dict(zip(self.label_names, key))
            result.append(MetricValue(self.name, value, labels))
        return result


class Gauge:
    """Prometheus-style gauge metric."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
    
    def set(self, value: float, **labels):
        """Set gauge value."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        self._values[key] = value
    
    def inc(self, amount: float = 1, **labels):
        """Increment gauge."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        self._values[key] = self._values.get(key, 0) + amount
    
    def dec(self, amount: float = 1, **labels):
        """Decrement gauge."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        self._values[key] = self._values.get(key, 0) - amount
    
    def get(self, **labels) -> float:
        """Get gauge value."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        return self._values.get(key, 0)
    
    def collect(self) -> List[MetricValue]:
        """Collect all values."""
        result = []
        for key, value in self._values.items():
            labels = dict(zip(self.label_names, key))
            result.append(MetricValue(self.name, value, labels))
        return result


class Histogram:
    """Prometheus-style histogram metric."""
    
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        buckets: List[float] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        
        self._counts: Dict[tuple, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._totals: Dict[tuple, int] = defaultdict(int)
    
    def observe(self, value: float, **labels):
        """Observe a value."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        
        self._sums[key] += value
        self._totals[key] += 1
        
        for bucket in self.buckets:
            if value <= bucket:
                self._counts[key][bucket] += 1
    
    @contextmanager
    def time(self, **labels):
        """Context manager for timing."""
        start = time.time()
        try:
            yield
        finally:
            self.observe(time.time() - start, **labels)
    
    def collect(self) -> List[MetricValue]:
        """Collect all values."""
        result = []
        
        for key in self._totals.keys():
            labels = dict(zip(self.label_names, key))
            
            # Bucket values
            cumulative = 0
            for bucket in self.buckets:
                cumulative += self._counts[key].get(bucket, 0)
                bucket_labels = {**labels, "le": str(bucket)}
                result.append(MetricValue(f"{self.name}_bucket", cumulative, bucket_labels))
            
            # +Inf bucket
            inf_labels = {**labels, "le": "+Inf"}
            result.append(MetricValue(f"{self.name}_bucket", self._totals[key], inf_labels))
            
            # Sum and count
            result.append(MetricValue(f"{self.name}_sum", self._sums[key], labels))
            result.append(MetricValue(f"{self.name}_count", self._totals[key], labels))
        
        return result


class WorkflowMetricsCollector:
    """
    Metrics collector for workflow system.
    
    Provides Prometheus-compatible metrics for:
    - Execution counts and durations
    - Node execution metrics
    - Error rates
    - Cache hit rates
    - Queue depths
    """
    
    def __init__(self):
        # Execution metrics
        self.executions_total = Counter(
            "workflow_executions_total",
            "Total workflow executions",
            ["workflow_id", "status"],
        )
        
        self.execution_duration = Histogram(
            "workflow_execution_duration_seconds",
            "Workflow execution duration",
            ["workflow_id"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300],
        )
        
        # Node metrics
        self.node_executions_total = Counter(
            "workflow_node_executions_total",
            "Total node executions",
            ["workflow_id", "node_type", "status"],
        )
        
        self.node_duration = Histogram(
            "workflow_node_duration_seconds",
            "Node execution duration",
            ["node_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
        )
        
        # Active executions
        self.active_executions = Gauge(
            "workflow_active_executions",
            "Currently active executions",
            ["workflow_id"],
        )
        
        # Error metrics
        self.errors_total = Counter(
            "workflow_errors_total",
            "Total errors",
            ["workflow_id", "error_type"],
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            "workflow_cache_hits_total",
            "Cache hits",
            ["cache_type"],
        )
        
        self.cache_misses = Counter(
            "workflow_cache_misses_total",
            "Cache misses",
            ["cache_type"],
        )
        
        # Queue metrics
        self.dlq_size = Gauge(
            "workflow_dlq_size",
            "Dead letter queue size",
            ["status"],
        )
        
        # Rate limit metrics
        self.rate_limit_hits = Counter(
            "workflow_rate_limit_hits_total",
            "Rate limit hits",
            ["user_tier"],
        )
    
    def record_execution_start(self, workflow_id: str):
        """Record execution start."""
        self.active_executions.inc(workflow_id=workflow_id)
    
    def record_execution_end(
        self,
        workflow_id: str,
        status: str,
        duration_seconds: float,
    ):
        """Record execution end."""
        self.executions_total.inc(workflow_id=workflow_id, status=status)
        self.execution_duration.observe(duration_seconds, workflow_id=workflow_id)
        self.active_executions.dec(workflow_id=workflow_id)
    
    def record_node_execution(
        self,
        workflow_id: str,
        node_type: str,
        status: str,
        duration_seconds: float,
    ):
        """Record node execution."""
        self.node_executions_total.inc(
            workflow_id=workflow_id,
            node_type=node_type,
            status=status,
        )
        self.node_duration.observe(duration_seconds, node_type=node_type)
    
    def record_error(self, workflow_id: str, error_type: str):
        """Record error."""
        self.errors_total.inc(workflow_id=workflow_id, error_type=error_type)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        self.cache_hits.inc(cache_type=cache_type)
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        self.cache_misses.inc(cache_type=cache_type)
    
    def update_dlq_size(self, pending: int, retrying: int):
        """Update DLQ size."""
        self.dlq_size.set(pending, status="pending")
        self.dlq_size.set(retrying, status="retrying")
    
    def record_rate_limit(self, user_tier: str):
        """Record rate limit hit."""
        self.rate_limit_hits.inc(user_tier=user_tier)
    
    def collect_all(self) -> List[MetricValue]:
        """Collect all metrics."""
        metrics = []
        
        metrics.extend(self.executions_total.collect())
        metrics.extend(self.execution_duration.collect())
        metrics.extend(self.node_executions_total.collect())
        metrics.extend(self.node_duration.collect())
        metrics.extend(self.active_executions.collect())
        metrics.extend(self.errors_total.collect())
        metrics.extend(self.cache_hits.collect())
        metrics.extend(self.cache_misses.collect())
        metrics.extend(self.dlq_size.collect())
        metrics.extend(self.rate_limit_hits.collect())
        
        return metrics
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for metric in self.collect_all():
            lines.append(metric.to_prometheus())
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_executions": sum(
                m.value for m in self.executions_total.collect()
            ),
            "active_executions": sum(
                m.value for m in self.active_executions.collect()
            ),
            "total_errors": sum(
                m.value for m in self.errors_total.collect()
            ),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        hits = sum(m.value for m in self.cache_hits.collect())
        misses = sum(m.value for m in self.cache_misses.collect())
        total = hits + misses
        return round(hits / total * 100, 2) if total > 0 else 0


# Global metrics collector
_metrics: Optional[WorkflowMetricsCollector] = None


def get_metrics_collector() -> WorkflowMetricsCollector:
    """Get or create global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = WorkflowMetricsCollector()
    return _metrics
