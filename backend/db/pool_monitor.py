"""
PostgreSQL Connection Pool Monitor

Provides detailed monitoring and alerting for connection pool health.
"""

import logging
import time
from typing import Dict, Any, List
from sqlalchemy.engine import Engine
from sqlalchemy import event
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class PoolMonitor:
    """
    Monitor PostgreSQL connection pool health and performance.

    Features:
    - Connection checkout/checkin tracking
    - Long-lived connection detection
    - Pool utilization metrics
    - Connection leak detection
    - Historical statistics
    """

    def __init__(
        self,
        engine: Engine,
        long_connection_threshold: float = 5.0,
        leak_detection_threshold: float = 30.0,
        history_size: int = 1000,
    ):
        """
        Initialize pool monitor.

        Args:
            engine: SQLAlchemy engine to monitor
            long_connection_threshold: Warn if connection held > this many seconds
            leak_detection_threshold: Alert if connection held > this many seconds
            history_size: Number of historical events to keep
        """
        self.engine = engine
        self.long_connection_threshold = long_connection_threshold
        self.leak_detection_threshold = leak_detection_threshold

        # Tracking
        self.checkout_times: Dict[int, float] = {}
        self.connection_durations: deque = deque(maxlen=history_size)
        self.long_connections: List[Dict[str, Any]] = []
        self.potential_leaks: List[Dict[str, Any]] = []

        # Statistics
        self.total_checkouts = 0
        self.total_checkins = 0
        self.total_connects = 0
        self.total_disconnects = 0

        logger.info(
            f"PoolMonitor initialized: "
            f"long_threshold={long_connection_threshold}s, "
            f"leak_threshold={leak_detection_threshold}s"
        )

    def setup_monitoring(self) -> None:
        """Setup connection pool event listeners."""

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkout from pool."""
            conn_id = id(dbapi_conn)
            self.checkout_times[conn_id] = time.time()
            self.total_checkouts += 1

            pool = self.engine.pool
            logger.debug(
                f"Pool checkout: "
                f"size={pool.size()}, "
                f"checked_out={pool.checkedout()}, "
                f"overflow={pool.overflow()}, "
                f"total_checkouts={self.total_checkouts}"
            )

            # Check for pool exhaustion
            utilization = self._calculate_utilization()
            if utilization > 90:
                logger.warning(
                    f"High pool utilization: {utilization:.1f}% "
                    f"({pool.checkedout()}/{pool.size() + pool._max_overflow})"
                )

        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkin to pool."""
            conn_id = id(dbapi_conn)

            if conn_id in self.checkout_times:
                checkout_time = self.checkout_times[conn_id]
                duration = time.time() - checkout_time

                # Record duration
                self.connection_durations.append(duration)
                self.total_checkins += 1

                # Check for long-lived connections
                if duration > self.long_connection_threshold:
                    warning_data = {
                        "duration": duration,
                        "timestamp": datetime.utcnow(),
                        "threshold": self.long_connection_threshold,
                    }
                    self.long_connections.append(warning_data)

                    logger.warning(
                        f"Long-lived connection detected: {duration:.2f}s "
                        f"(threshold: {self.long_connection_threshold}s)"
                    )

                # Check for potential leaks
                if duration > self.leak_detection_threshold:
                    leak_data = {
                        "duration": duration,
                        "timestamp": datetime.utcnow(),
                        "threshold": self.leak_detection_threshold,
                    }
                    self.potential_leaks.append(leak_data)

                    logger.error(
                        f"POTENTIAL CONNECTION LEAK: {duration:.2f}s "
                        f"(threshold: {self.leak_detection_threshold}s)"
                    )

                del self.checkout_times[conn_id]

            logger.debug(f"Pool checkin: total_checkins={self.total_checkins}")

        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Track new connection creation."""
            self.total_connects += 1
            logger.info(
                f"New database connection created "
                f"(total_connects={self.total_connects})"
            )

        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Track connection closure."""
            self.total_disconnects += 1
            logger.info(
                f"Database connection closed "
                f"(total_disconnects={self.total_disconnects})"
            )

        logger.info("Pool monitoring events registered")

    def _calculate_utilization(self) -> float:
        """Calculate current pool utilization percentage."""
        pool = self.engine.pool
        max_connections = pool.size() + pool._max_overflow
        if max_connections == 0:
            return 0.0
        return (pool.checkedout() / max_connections) * 100

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive pool statistics.

        Returns:
            Dictionary with detailed pool metrics
        """
        pool = self.engine.pool

        # Calculate statistics
        avg_duration = (
            sum(self.connection_durations) / len(self.connection_durations)
            if self.connection_durations
            else 0
        )

        max_duration = (
            max(self.connection_durations) if self.connection_durations else 0
        )
        min_duration = (
            min(self.connection_durations) if self.connection_durations else 0
        )

        # Current active connections
        active_connections = len(self.checkout_times)

        # Check for stuck connections
        current_time = time.time()
        stuck_connections = [
            {"duration": current_time - checkout_time, "conn_id": conn_id}
            for conn_id, checkout_time in self.checkout_times.items()
            if current_time - checkout_time > self.leak_detection_threshold
        ]

        return {
            # Pool configuration
            "pool_size": pool.size(),
            "max_overflow": pool._max_overflow,
            "max_connections": pool.size() + pool._max_overflow,
            # Current state
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "utilization_percent": self._calculate_utilization(),
            # Lifetime statistics
            "total_checkouts": self.total_checkouts,
            "total_checkins": self.total_checkins,
            "total_connects": self.total_connects,
            "total_disconnects": self.total_disconnects,
            # Connection duration statistics
            "avg_connection_duration_ms": avg_duration * 1000,
            "max_connection_duration_ms": max_duration * 1000,
            "min_connection_duration_ms": min_duration * 1000,
            "connection_samples": len(self.connection_durations),
            # Active connections
            "active_connections": active_connections,
            "active_connection_ids": list(self.checkout_times.keys()),
            # Warnings and alerts
            "long_connections_count": len(self.long_connections),
            "potential_leaks_count": len(self.potential_leaks),
            "stuck_connections": stuck_connections,
            # Health status
            "health_status": self._get_health_status(),
        }

    def _get_health_status(self) -> str:
        """
        Determine overall pool health status.

        Returns:
            Health status: "healthy", "warning", or "critical"
        """
        utilization = self._calculate_utilization()
        stuck_count = sum(
            1
            for checkout_time in self.checkout_times.values()
            if time.time() - checkout_time > self.leak_detection_threshold
        )

        if stuck_count > 0:
            return "critical"
        elif utilization > 90:
            return "critical"
        elif utilization > 75 or len(self.long_connections) > 10:
            return "warning"
        else:
            return "healthy"

    def get_recent_long_connections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent long-lived connections.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of long connection records
        """
        return self.long_connections[-limit:]

    def get_potential_leaks(self) -> List[Dict[str, Any]]:
        """
        Get all potential connection leaks.

        Returns:
            List of potential leak records
        """
        return self.potential_leaks

    def reset_statistics(self) -> None:
        """Reset all statistics (useful for testing)."""
        self.checkout_times.clear()
        self.connection_durations.clear()
        self.long_connections.clear()
        self.potential_leaks.clear()

        self.total_checkouts = 0
        self.total_checkins = 0
        self.total_connects = 0
        self.total_disconnects = 0

        logger.info("Pool monitor statistics reset")

    def __repr__(self) -> str:
        return (
            f"PoolMonitor("
            f"checkouts={self.total_checkouts}, "
            f"checkins={self.total_checkins}, "
            f"health={self._get_health_status()})"
        )


# Global monitor instance
_pool_monitor: PoolMonitor = None


def setup_pool_monitoring(
    engine: Engine,
    long_connection_threshold: float = 5.0,
    leak_detection_threshold: float = 30.0,
) -> PoolMonitor:
    """
    Setup global pool monitoring.

    Args:
        engine: SQLAlchemy engine to monitor
        long_connection_threshold: Warn if connection held > this many seconds
        leak_detection_threshold: Alert if connection held > this many seconds

    Returns:
        PoolMonitor instance
    """
    global _pool_monitor

    if _pool_monitor is None:
        _pool_monitor = PoolMonitor(
            engine=engine,
            long_connection_threshold=long_connection_threshold,
            leak_detection_threshold=leak_detection_threshold,
        )
        _pool_monitor.setup_monitoring()
        logger.info("Global pool monitoring enabled")

    return _pool_monitor


def get_pool_monitor() -> PoolMonitor:
    """
    Get global pool monitor instance.

    Returns:
        PoolMonitor instance

    Raises:
        RuntimeError: If monitoring not setup
    """
    if _pool_monitor is None:
        raise RuntimeError(
            "Pool monitoring not setup. Call setup_pool_monitoring() first."
        )
    return _pool_monitor
