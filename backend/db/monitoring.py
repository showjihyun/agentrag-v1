"""Database query performance monitoring."""

import time
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Slow query threshold in seconds
SLOW_QUERY_THRESHOLD = 1.0


def setup_query_monitoring(
    engine: Engine, slow_query_threshold: float = SLOW_QUERY_THRESHOLD
):
    """
    Setup query performance monitoring on the given engine.

    Args:
        engine: SQLAlchemy engine to monitor
        slow_query_threshold: Threshold in seconds for slow query warnings
    """

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Record query start time."""
        conn.info.setdefault("query_start_time", []).append(time.time())

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Executing query: {statement[:200]}...")
            if parameters:
                logger.debug(f"Parameters: {parameters}")

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Measure query execution time and log slow queries."""
        total_time = time.time() - conn.info["query_start_time"].pop()

        if total_time > slow_query_threshold:
            logger.warning(
                f"Slow query detected ({total_time:.2f}s):\n"
                f"Statement: {statement}\n"
                f"Parameters: {parameters}"
            )
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Query executed in {total_time:.4f}s")

    logger.info(
        f"Query monitoring enabled (slow query threshold: {slow_query_threshold}s)"
    )


def get_pool_status(engine: Engine) -> dict:
    """
    Get connection pool status.

    Args:
        engine: SQLAlchemy engine

    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
        "max_connections": pool.size() + pool._max_overflow,
    }


class QueryPerformanceTracker:
    """Track query performance metrics."""

    def __init__(self):
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
        self.queries_by_type = {}

    def record_query(self, statement: str, duration: float, is_slow: bool = False):
        """Record a query execution."""
        self.query_count += 1
        self.total_time += duration

        # Extract query type (SELECT, INSERT, UPDATE, DELETE)
        query_type = statement.strip().split()[0].upper()
        if query_type not in self.queries_by_type:
            self.queries_by_type[query_type] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
            }

        self.queries_by_type[query_type]["count"] += 1
        self.queries_by_type[query_type]["total_time"] += duration
        self.queries_by_type[query_type]["avg_time"] = (
            self.queries_by_type[query_type]["total_time"]
            / self.queries_by_type[query_type]["count"]
        )

        if is_slow:
            self.slow_queries.append(
                {
                    "statement": statement[:200],
                    "duration": duration,
                    "timestamp": time.time(),
                }
            )

    def get_stats(self) -> dict:
        """Get performance statistics."""
        return {
            "total_queries": self.query_count,
            "total_time": self.total_time,
            "avg_time": (
                self.total_time / self.query_count if self.query_count > 0 else 0
            ),
            "queries_by_type": self.queries_by_type,
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
        }

    def reset(self):
        """Reset all statistics."""
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
        self.queries_by_type = {}


# Global performance tracker
performance_tracker = QueryPerformanceTracker()
