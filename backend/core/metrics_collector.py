"""
Metrics Collector - Phase 2.3 Optimization

Comprehensive metrics collection for observability:
- Prometheus metrics
- Query performance tracking
- Agent performance tracking
- LLM usage and cost tracking
- Cache performance tracking

Key features:
- Real-time metrics
- Histogram for latency percentiles
- Counter for totals
- Gauge for current values
"""

import time
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        CollectorRegistry,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Only log prometheus warning in debug mode or if explicitly requested
    import os
    if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("SHOW_PROMETHEUS_WARNING", "false").lower() == "true":
        logging.warning("prometheus_client not installed - metrics disabled")

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Comprehensive metrics collector.

    Metrics categories:
    - Query metrics (latency, volume, success rate)
    - Agent metrics (calls, latency per agent)
    - LLM metrics (calls, tokens, cost)
    - Cache metrics (hits, misses, hit rate)
    - System metrics (memory, CPU)

    Integration:
    - Prometheus for metrics storage
    - Grafana for visualization
    - Alerts for anomalies
    """

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        """
        Initialize metrics collector.

        Args:
            registry: Prometheus registry (optional)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "Metrics collection disabled - prometheus_client not available"
            )
            self.enabled = False
            return

        self.enabled = True
        self.registry = registry or CollectorRegistry()

        # Initialize metrics
        self._init_query_metrics()
        self._init_agent_metrics()
        self._init_llm_metrics()
        self._init_cache_metrics()
        self._init_system_metrics()
        self._init_adaptive_routing_metrics()

        logger.info("MetricsCollector initialized with Prometheus")

    def _init_query_metrics(self):
        """Initialize query metrics."""
        if not self.enabled:
            return

        # Query counters
        self.query_total = Counter(
            "rag_queries_total",
            "Total number of queries",
            ["mode", "complexity", "status"],
            registry=self.registry,
        )

        self.query_success = Counter(
            "rag_query_success_total",
            "Successful queries",
            ["mode", "complexity"],
            registry=self.registry,
        )

        self.query_errors = Counter(
            "rag_query_errors_total",
            "Failed queries",
            ["mode", "error_type"],
            registry=self.registry,
        )

        # Query latency histogram
        self.query_latency = Histogram(
            "rag_query_latency_seconds",
            "Query latency in seconds",
            ["mode", "complexity"],
            buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
            registry=self.registry,
        )

        # Current queries gauge
        self.queries_in_progress = Gauge(
            "rag_queries_in_progress",
            "Number of queries currently being processed",
            ["mode"],
            registry=self.registry,
        )

    def _init_agent_metrics(self):
        """Initialize agent metrics."""
        if not self.enabled:
            return

        # Agent call counters
        self.agent_calls = Counter(
            "rag_agent_calls_total",
            "Total agent calls",
            ["agent_type", "status"],
            registry=self.registry,
        )

        # Agent latency
        self.agent_latency = Histogram(
            "rag_agent_latency_seconds",
            "Agent execution latency",
            ["agent_type"],
            buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry,
        )

        # Agent iterations
        self.agent_iterations = Histogram(
            "rag_agent_iterations",
            "Number of ReAct iterations",
            buckets=[1, 2, 3, 5, 7, 10, 15],
            registry=self.registry,
        )

    def _init_llm_metrics(self):
        """Initialize LLM metrics."""
        if not self.enabled:
            return

        # LLM call counters
        self.llm_calls = Counter(
            "rag_llm_calls_total",
            "Total LLM API calls",
            ["provider", "model", "status"],
            registry=self.registry,
        )

        # Token usage
        self.llm_tokens = Counter(
            "rag_llm_tokens_total",
            "Total tokens used",
            ["provider", "model", "type"],  # type: prompt, completion
            registry=self.registry,
        )

        # LLM cost
        self.llm_cost = Counter(
            "rag_llm_cost_dollars",
            "Total LLM cost in dollars",
            ["provider", "model"],
            registry=self.registry,
        )

        # LLM latency
        self.llm_latency = Histogram(
            "rag_llm_latency_seconds",
            "LLM API call latency",
            ["provider", "model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry,
        )

    def _init_cache_metrics(self):
        """Initialize cache metrics."""
        if not self.enabled:
            return

        # Cache hits/misses
        self.cache_hits = Counter(
            "rag_cache_hits_total", "Cache hits", ["cache_type"], registry=self.registry
        )

        self.cache_misses = Counter(
            "rag_cache_misses_total",
            "Cache misses",
            ["cache_type"],
            registry=self.registry,
        )

        # Cache size
        self.cache_size = Gauge(
            "rag_cache_size_bytes",
            "Cache size in bytes",
            ["cache_type"],
            registry=self.registry,
        )

    def _init_system_metrics(self):
        """Initialize system metrics."""
        if not self.enabled:
            return

        # System info
        self.system_info = Info(
            "rag_system", "System information", registry=self.registry
        )

    def _init_adaptive_routing_metrics(self):
        """Initialize adaptive routing metrics."""
        if not self.enabled:
            return

        # Mode distribution
        self.adaptive_mode_distribution = Counter(
            "rag_adaptive_mode_total",
            "Query count by mode",
            ["mode"],
            registry=self.registry,
        )

        # Complexity distribution
        self.adaptive_complexity_distribution = Counter(
            "rag_adaptive_complexity_total",
            "Query count by complexity",
            ["complexity"],
            registry=self.registry,
        )

        # Routing confidence
        self.adaptive_routing_confidence = Histogram(
            "rag_adaptive_routing_confidence",
            "Routing decision confidence",
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
            registry=self.registry,
        )

        # Routing time
        self.adaptive_routing_time = Histogram(
            "rag_adaptive_routing_time_seconds",
            "Time spent on routing decision",
            buckets=[0.001, 0.005, 0.01, 0.02, 0.05, 0.1],
            registry=self.registry,
        )

        # Escalations
        self.adaptive_escalations = Counter(
            "rag_adaptive_escalations_total",
            "Mode escalations",
            ["from_mode", "to_mode"],
            registry=self.registry,
        )

        # Cache hit rate by mode
        self.adaptive_cache_hits_by_mode = Counter(
            "rag_adaptive_cache_hits_by_mode_total",
            "Cache hits by mode",
            ["mode"],
            registry=self.registry,
        )

        self.adaptive_cache_misses_by_mode = Counter(
            "rag_adaptive_cache_misses_by_mode_total",
            "Cache misses by mode",
            ["mode"],
            registry=self.registry,
        )

        # User satisfaction by mode
        self.adaptive_user_satisfaction = Histogram(
            "rag_adaptive_user_satisfaction",
            "User satisfaction rating by mode",
            ["mode"],
            buckets=[1.0, 2.0, 3.0, 4.0, 5.0],
            registry=self.registry,
        )

        # Threshold values
        self.adaptive_threshold_simple = Gauge(
            "rag_adaptive_threshold_simple",
            "Current simple/medium complexity threshold",
            registry=self.registry,
        )

        self.adaptive_threshold_complex = Gauge(
            "rag_adaptive_threshold_complex",
            "Current medium/complex complexity threshold",
            registry=self.registry,
        )

    # Query metrics methods

    @contextmanager
    def track_query(self, mode: str = "auto", complexity: str = "medium"):
        """
        Context manager to track query execution.

        Usage:
            with metrics.track_query(mode="fast", complexity="simple"):
                # Execute query
                pass

        Args:
            mode: Query mode (fast, deep, auto)
            complexity: Query complexity (simple, medium, complex)
        """
        if not self.enabled:
            yield
            return

        # Increment in-progress
        self.queries_in_progress.labels(mode=mode).inc()

        # Track latency
        start_time = time.time()
        success = False
        error_type = None

        try:
            yield
            success = True
        except Exception as e:
            error_type = type(e).__name__
            raise
        finally:
            # Record latency
            latency = time.time() - start_time
            self.query_latency.labels(mode=mode, complexity=complexity).observe(latency)

            # Record total
            status = "success" if success else "error"
            self.query_total.labels(
                mode=mode, complexity=complexity, status=status
            ).inc()

            # Record success/error
            if success:
                self.query_success.labels(mode=mode, complexity=complexity).inc()
            else:
                self.query_errors.labels(
                    mode=mode, error_type=error_type or "unknown"
                ).inc()

            # Decrement in-progress
            self.queries_in_progress.labels(mode=mode).dec()

    # Agent metrics methods

    @contextmanager
    def track_agent(self, agent_type: str):
        """
        Context manager to track agent execution.

        Args:
            agent_type: Agent type (vector, local, web, aggregator)
        """
        if not self.enabled:
            yield
            return

        start_time = time.time()
        success = False

        try:
            yield
            success = True
        except Exception:
            raise
        finally:
            # Record latency
            latency = time.time() - start_time
            self.agent_latency.labels(agent_type=agent_type).observe(latency)

            # Record call
            status = "success" if success else "error"
            self.agent_calls.labels(agent_type=agent_type, status=status).inc()

    def record_agent_iterations(self, iterations: int):
        """Record number of ReAct iterations."""
        if self.enabled:
            self.agent_iterations.observe(iterations)

    # LLM metrics methods

    @contextmanager
    def track_llm_call(self, provider: str, model: str):
        """
        Context manager to track LLM API call.

        Args:
            provider: LLM provider (openai, claude, ollama)
            model: Model name
        """
        if not self.enabled:
            yield {}
            return

        start_time = time.time()
        success = False
        result = {}

        try:
            yield result
            success = True
        except Exception:
            raise
        finally:
            # Record latency
            latency = time.time() - start_time
            self.llm_latency.labels(provider=provider, model=model).observe(latency)

            # Record call
            status = "success" if success else "error"
            self.llm_calls.labels(provider=provider, model=model, status=status).inc()

            # Record tokens if available
            if success and result:
                prompt_tokens = result.get("prompt_tokens", 0)
                completion_tokens = result.get("completion_tokens", 0)

                if prompt_tokens:
                    self.llm_tokens.labels(
                        provider=provider, model=model, type="prompt"
                    ).inc(prompt_tokens)

                if completion_tokens:
                    self.llm_tokens.labels(
                        provider=provider, model=model, type="completion"
                    ).inc(completion_tokens)

                # Record cost if available
                cost = result.get("cost", 0)
                if cost:
                    self.llm_cost.labels(provider=provider, model=model).inc(cost)

    # Cache metrics methods

    def record_cache_hit(self, cache_type: str = "default"):
        """Record cache hit."""
        if self.enabled:
            self.cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str = "default"):
        """Record cache miss."""
        if self.enabled:
            self.cache_misses.labels(cache_type=cache_type).inc()

    def update_cache_size(self, size_bytes: int, cache_type: str = "default"):
        """Update cache size."""
        if self.enabled:
            self.cache_size.labels(cache_type=cache_type).set(size_bytes)

    # Adaptive routing metrics methods

    def record_adaptive_routing(
        self,
        mode: str,
        complexity: str,
        routing_confidence: float,
        routing_time: float,
        cache_hit: bool,
        escalated: bool = False,
        escalated_from: Optional[str] = None,
    ):
        """
        Record adaptive routing metrics.

        Args:
            mode: Selected mode (fast, balanced, deep)
            complexity: Query complexity (simple, medium, complex)
            routing_confidence: Confidence in routing decision (0-1)
            routing_time: Time spent on routing (seconds)
            cache_hit: Whether result was cached
            escalated: Whether mode was escalated
            escalated_from: Original mode if escalated
        """
        if not self.enabled:
            return

        # Record mode distribution
        self.adaptive_mode_distribution.labels(mode=mode).inc()

        # Record complexity distribution
        self.adaptive_complexity_distribution.labels(complexity=complexity).inc()

        # Record routing confidence
        self.adaptive_routing_confidence.observe(routing_confidence)

        # Record routing time
        self.adaptive_routing_time.observe(routing_time)

        # Record cache performance by mode
        if cache_hit:
            self.adaptive_cache_hits_by_mode.labels(mode=mode).inc()
        else:
            self.adaptive_cache_misses_by_mode.labels(mode=mode).inc()

        # Record escalation
        if escalated and escalated_from:
            self.adaptive_escalations.labels(
                from_mode=escalated_from, to_mode=mode
            ).inc()

    def record_user_satisfaction(self, mode: str, rating: float):
        """
        Record user satisfaction rating.

        Args:
            mode: Mode used (fast, balanced, deep)
            rating: User rating (1-5)
        """
        if self.enabled:
            self.adaptive_user_satisfaction.labels(mode=mode).observe(rating)

    def update_adaptive_thresholds(
        self, simple_threshold: float, complex_threshold: float
    ):
        """
        Update adaptive routing thresholds.

        Args:
            simple_threshold: Simple/medium threshold
            complex_threshold: Medium/complex threshold
        """
        if self.enabled:
            self.adaptive_threshold_simple.set(simple_threshold)
            self.adaptive_threshold_complex.set(complex_threshold)

    # Export methods

    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        if not self.enabled:
            return b""

        return generate_latest(self.registry)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.

        Returns:
            Dictionary of current stats
        """
        if not self.enabled:
            return {"enabled": False}

        # This is a simplified version
        # In production, you'd query Prometheus for actual values
        return {
            "enabled": True,
            "message": "Use /metrics endpoint for Prometheus format",
        }


# Global metrics instance
_metrics_instance: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_instance

    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()

    return _metrics_instance


# Decorator for automatic tracking
def track_performance(metric_type: str = "query", **labels):
    """
    Decorator to automatically track function performance.

    Usage:
        @track_performance(metric_type="agent", agent_type="vector")
        async def search_vectors(query):
            ...

    Args:
        metric_type: Type of metric (query, agent, llm)
        **labels: Additional labels
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()

            if metric_type == "query":
                with metrics.track_query(**labels):
                    return await func(*args, **kwargs)

            elif metric_type == "agent":
                agent_type = labels.get("agent_type", "unknown")
                with metrics.track_agent(agent_type):
                    return await func(*args, **kwargs)

            elif metric_type == "llm":
                provider = labels.get("provider", "unknown")
                model = labels.get("model", "unknown")
                with metrics.track_llm_call(provider, model):
                    return await func(*args, **kwargs)

            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
