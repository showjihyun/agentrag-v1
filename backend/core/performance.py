"""Performance optimization utilities."""

import time
import functools
import logging
from typing import Callable, Any, Optional
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time-to-live for cache entries (None = no expiration)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            self.misses += 1
            return None

        # Check TTL
        if self.ttl_seconds:
            timestamp = self.timestamps.get(key)
            if timestamp and datetime.utcnow() - timestamp > timedelta(
                seconds=self.ttl_seconds
            ):
                self.cache.pop(key)
                self.timestamps.pop(key)
                self.misses += 1
                return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def set(self, key: str, value: Any):
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key, None)

        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow()

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


def timed_operation(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Usage:
        @timed_operation
        def my_function():
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(f"{func.__name__} completed in {elapsed:.2f}ms")
        return result

    return wrapper


def async_timed_operation(func: Callable) -> Callable:
    """
    Decorator to measure async function execution time.

    Usage:
        @async_timed_operation
        async def my_async_function():
            pass
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(f"{func.__name__} completed in {elapsed:.2f}ms")
        return result

    return wrapper


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}

    def record_metric(self, name: str, value: float, unit: str = "ms"):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = {
                "count": 0,
                "total": 0,
                "min": float("inf"),
                "max": 0,
                "unit": unit,
            }

        metric = self.metrics[name]
        metric["count"] += 1
        metric["total"] += value
        metric["min"] = min(metric["min"], value)
        metric["max"] = max(metric["max"], value)

    def get_stats(self, name: str) -> Optional[dict]:
        """Get statistics for a metric."""
        if name not in self.metrics:
            return None

        metric = self.metrics[name]
        avg = metric["total"] / metric["count"] if metric["count"] > 0 else 0

        return {
            "count": metric["count"],
            "average": f"{avg:.2f}{metric['unit']}",
            "min": f"{metric['min']:.2f}{metric['unit']}",
            "max": f"{metric['max']:.2f}{metric['unit']}",
            "total": f"{metric['total']:.2f}{metric['unit']}",
        }

    def get_all_stats(self) -> dict:
        """Get all performance statistics."""
        return {name: self.get_stats(name) for name in self.metrics.keys()}

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()


# Global performance monitor
performance_monitor = PerformanceMonitor()


class BatchProcessor:
    """Utility for batch processing operations."""

    @staticmethod
    def process_in_batches(
        items: list, batch_size: int, process_func: Callable, show_progress: bool = True
    ) -> list:
        """
        Process items in batches.

        Args:
            items: List of items to process
            batch_size: Number of items per batch
            process_func: Function to process each batch
            show_progress: Whether to log progress

        Returns:
            List of results from all batches
        """
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_num = i // batch_size + 1

            if show_progress:
                logger.info(f"Processing batch {batch_num}/{total_batches}")

            batch_results = process_func(batch)
            results.extend(batch_results)

        return results


class ConnectionPool:
    """Simple connection pool implementation."""

    def __init__(self, create_connection: Callable, max_size: int = 10):
        """
        Initialize connection pool.

        Args:
            create_connection: Function to create new connections
            max_size: Maximum pool size
        """
        self.create_connection = create_connection
        self.max_size = max_size
        self.pool = []
        self.in_use = set()

    def acquire(self):
        """Acquire connection from pool."""
        if self.pool:
            conn = self.pool.pop()
        elif len(self.in_use) < self.max_size:
            conn = self.create_connection()
        else:
            raise Exception("Connection pool exhausted")

        self.in_use.add(id(conn))
        return conn

    def release(self, conn):
        """Release connection back to pool."""
        conn_id = id(conn)
        if conn_id in self.in_use:
            self.in_use.remove(conn_id)
            self.pool.append(conn)

    def close_all(self):
        """Close all connections in pool."""
        for conn in self.pool:
            if hasattr(conn, "close"):
                conn.close()
        self.pool.clear()
        self.in_use.clear()
