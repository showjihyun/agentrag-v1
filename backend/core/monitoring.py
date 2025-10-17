"""Advanced monitoring and observability utilities."""

import time
import psutil
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int


@dataclass
class RequestMetrics:
    """Request performance metrics."""

    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    error: Optional[str] = None


class MetricsCollector:
    """Collect and aggregate system and application metrics."""

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self.system_metrics: deque = deque(maxlen=max_history)
        self.request_metrics: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = {}
        self.endpoint_stats: Dict[str, Dict] = {}

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            active_connections=len(psutil.net_connections()),
        )

        self.system_metrics.append(metrics)
        return metrics

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Record request metrics."""
        metrics = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            error=error,
        )

        self.request_metrics.append(metrics)

        # Update endpoint statistics
        key = f"{method}:{endpoint}"
        if key not in self.endpoint_stats:
            self.endpoint_stats[key] = {
                "count": 0,
                "total_duration": 0,
                "errors": 0,
                "min_duration": float("inf"),
                "max_duration": 0,
            }

        stats = self.endpoint_stats[key]
        stats["count"] += 1
        stats["total_duration"] += duration_ms
        stats["min_duration"] = min(stats["min_duration"], duration_ms)
        stats["max_duration"] = max(stats["max_duration"], duration_ms)

        if status_code >= 400:
            stats["errors"] += 1

            # Track error types
            error_key = f"{status_code}:{endpoint}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def get_system_health(self) -> Dict:
        """Get current system health status."""
        if not self.system_metrics:
            self.collect_system_metrics()

        latest = self.system_metrics[-1]

        # Determine health status
        health_status = "healthy"
        issues = []

        if latest.cpu_percent > 80:
            health_status = "warning"
            issues.append(f"High CPU usage: {latest.cpu_percent:.1f}%")

        if latest.memory_percent > 85:
            health_status = "warning"
            issues.append(f"High memory usage: {latest.memory_percent:.1f}%")

        if latest.disk_usage_percent > 90:
            health_status = "critical"
            issues.append(f"Critical disk usage: {latest.disk_usage_percent:.1f}%")

        return {
            "status": health_status,
            "timestamp": latest.timestamp.isoformat(),
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "disk_usage_percent": latest.disk_usage_percent,
            "issues": issues,
        }

    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict:
        """Get endpoint performance statistics."""
        if endpoint:
            stats = self.endpoint_stats.get(endpoint, {})
            if not stats:
                return {}

            avg_duration = (
                stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
            )
            error_rate = (
                (stats["errors"] / stats["count"] * 100) if stats["count"] > 0 else 0
            )

            return {
                "endpoint": endpoint,
                "total_requests": stats["count"],
                "average_duration_ms": round(avg_duration, 2),
                "min_duration_ms": round(stats["min_duration"], 2),
                "max_duration_ms": round(stats["max_duration"], 2),
                "error_count": stats["errors"],
                "error_rate_percent": round(error_rate, 2),
            }

        # Return all endpoint stats
        return {
            endpoint: self.get_endpoint_stats(endpoint)
            for endpoint in self.endpoint_stats.keys()
        }

    def get_error_summary(self, limit: int = 10) -> List[Dict]:
        """Get most common errors."""
        sorted_errors = sorted(
            self.error_counts.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        return [{"error": error, "count": count} for error, count in sorted_errors]

    def get_recent_requests(
        self, limit: int = 100, status_code: Optional[int] = None
    ) -> List[Dict]:
        """Get recent request metrics."""
        requests = list(self.request_metrics)

        if status_code:
            requests = [r for r in requests if r.status_code == status_code]

        requests = requests[-limit:]

        return [asdict(r) for r in requests]

    def get_performance_trends(self, minutes: int = 60) -> Dict:
        """Get performance trends over time."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        recent_requests = [r for r in self.request_metrics if r.timestamp >= cutoff]

        if not recent_requests:
            return {
                "period_minutes": minutes,
                "total_requests": 0,
                "average_duration_ms": 0,
                "error_rate_percent": 0,
            }

        total_requests = len(recent_requests)
        total_duration = sum(r.duration_ms for r in recent_requests)
        error_count = sum(1 for r in recent_requests if r.status_code >= 400)

        return {
            "period_minutes": minutes,
            "total_requests": total_requests,
            "average_duration_ms": round(total_duration / total_requests, 2),
            "error_count": error_count,
            "error_rate_percent": round(error_count / total_requests * 100, 2),
            "requests_per_minute": round(total_requests / minutes, 2),
        }

    def reset_metrics(self):
        """Reset all collected metrics."""
        self.system_metrics.clear()
        self.request_metrics.clear()
        self.error_counts.clear()
        self.endpoint_stats.clear()
        logger.info("Metrics collector reset")


class HealthChecker:
    """Health check utilities for system components."""

    @staticmethod
    def check_database(db_session) -> Dict:
        """Check database connectivity and health."""
        try:
            start = time.time()
            db_session.execute("SELECT 1")
            latency_ms = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": "Database connection OK",
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed",
            }

    @staticmethod
    def check_redis(redis_client) -> Dict:
        """Check Redis connectivity and health."""
        try:
            start = time.time()
            redis_client.ping()
            latency_ms = (time.time() - start) * 1000

            info = redis_client.info()

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0),
                "message": "Redis connection OK",
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed",
            }

    @staticmethod
    def check_milvus(milvus_client) -> Dict:
        """Check Milvus connectivity and health."""
        try:
            start = time.time()
            # Attempt to list collections
            collections = milvus_client.list_collections()
            latency_ms = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "collections_count": len(collections),
                "message": "Milvus connection OK",
            }
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Milvus connection failed",
            }


# Global metrics collector instance
metrics_collector = MetricsCollector()
