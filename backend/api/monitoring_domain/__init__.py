"""
Monitoring domain API routers

Groups all monitoring and metrics-related endpoints:
- health.py: Health checks
- metrics.py: Application metrics
- monitoring.py: System monitoring
- monitoring_stats.py: Monitoring statistics
- cache_metrics.py: Cache performance metrics
- database_metrics.py: Database metrics
- pool_metrics.py: Connection pool metrics
- circuit_breaker_status.py: Circuit breaker status
- react_stats.py: ReAct agent statistics
"""

# Re-export routers for easy access
# Usage: from backend.api.monitoring import health_router, metrics_router

__all__ = [
    "health",
    "metrics", 
    "monitoring",
    "monitoring_stats",
    "cache_metrics",
    "database_metrics",
    "pool_metrics",
    "circuit_breaker_status",
    "react_stats",
]
