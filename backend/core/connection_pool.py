"""
Connection pooling for Redis and other resources.

Provides efficient connection management with pooling,
health checks, and automatic reconnection.
"""

import logging
from typing import Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class ConnectionPoolMetrics:
    """Track connection pool metrics for monitoring."""
    
    def __init__(self):
        self.total_checkouts = 0
        self.total_checkins = 0
        self.total_timeouts = 0
        self.total_errors = 0
        self.checkout_times = []  # Last 100 checkout times
        self.max_checkout_time = 0.0
        self.avg_checkout_time = 0.0
        
    def record_checkout(self, duration_ms: float):
        """Record a connection checkout."""
        self.total_checkouts += 1
        self.checkout_times.append(duration_ms)
        
        # Keep only last 100 measurements
        if len(self.checkout_times) > 100:
            self.checkout_times.pop(0)
        
        # Update statistics
        self.max_checkout_time = max(self.max_checkout_time, duration_ms)
        if self.checkout_times:
            self.avg_checkout_time = sum(self.checkout_times) / len(self.checkout_times)
    
    def record_checkin(self):
        """Record a connection checkin."""
        self.total_checkins += 1
    
    def record_timeout(self):
        """Record a connection timeout."""
        self.total_timeouts += 1
    
    def record_error(self):
        """Record a connection error."""
        self.total_errors += 1
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            "total_checkouts": self.total_checkouts,
            "total_checkins": self.total_checkins,
            "total_timeouts": self.total_timeouts,
            "total_errors": self.total_errors,
            "active_connections": self.total_checkouts - self.total_checkins,
            "max_checkout_time_ms": self.max_checkout_time,
            "avg_checkout_time_ms": self.avg_checkout_time,
            "recent_checkout_times": self.checkout_times[-10:] if self.checkout_times else [],
        }


class RedisConnectionPool:
    """
    Redis connection pool manager with enhanced monitoring.

    Features:
    - Connection pooling
    - Health checks
    - Automatic reconnection
    - Statistics tracking
    - Performance metrics
    - Alerting thresholds
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 150,  # Increased for 5-100 concurrent users
        decode_responses: bool = True,
        socket_keepalive: bool = True,
        socket_keepalive_options: Optional[dict] = None,
        health_check_interval: int = 30,
    ):
        """
        Initialize Redis connection pool.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional password
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode responses
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self.health_check_interval = health_check_interval

        # Socket keepalive options for long-lived connections
        if socket_keepalive_options is None:
            socket_keepalive_options = {
                1: 1,  # TCP_KEEPIDLE
                2: 1,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            }

        # Create connection pool with optimized settings
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options=socket_keepalive_options,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=health_check_interval,
        )

        self._client: Optional[redis.Redis] = None
        self.metrics = ConnectionPoolMetrics()

        logger.info(
            f"RedisConnectionPool initialized: {host}:{port} "
            f"(max_connections={max_connections}, keepalive={socket_keepalive})"
        )

    def get_client(self) -> redis.Redis:
        """
        Get Redis client from pool.

        Returns:
            redis.Redis: Redis client instance
        """
        if self._client is None:
            self._client = redis.Redis(connection_pool=self.pool)

        return self._client

    async def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            bool: True if healthy
        """
        try:
            client = self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def get_pool_stats(self) -> dict:
        """
        Get comprehensive connection pool statistics.

        Returns:
            dict: Pool statistics including Redis info and custom metrics
        """
        try:
            import time
            start_time = time.time()
            
            client = self.get_client()
            info = await client.info("stats")
            
            # Record checkout time
            checkout_time_ms = (time.time() - start_time) * 1000
            self.metrics.record_checkout(checkout_time_ms)
            
            # Get pool info
            pool_info = {
                "connection_kwargs": {
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                },
                "max_connections": self.max_connections,
                "connection_class": str(self.pool.connection_class),
            }

            # Combine Redis stats with custom metrics
            stats = {
                "pool_config": pool_info,
                "redis_stats": {
                    "total_connections_received": info.get("total_connections_received", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                },
                "custom_metrics": self.metrics.get_metrics(),
                "health": {
                    "is_healthy": True,
                    "last_check": time.time(),
                },
            }
            
            # Check for potential issues
            warnings = []
            active_conns = self.metrics.get_metrics()["active_connections"]
            
            if active_conns > self.max_connections * 0.8:
                warnings.append(f"High connection usage: {active_conns}/{self.max_connections}")
            
            if self.metrics.avg_checkout_time > 100:  # 100ms threshold
                warnings.append(f"Slow checkout time: {self.metrics.avg_checkout_time:.2f}ms")
            
            if self.metrics.total_timeouts > 0:
                warnings.append(f"Connection timeouts detected: {self.metrics.total_timeouts}")
            
            if warnings:
                stats["warnings"] = warnings
                logger.warning(f"Redis pool warnings: {warnings}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}", exc_info=True)
            self.metrics.record_error()
            return {
                "error": str(e),
                "custom_metrics": self.metrics.get_metrics(),
            }

    async def close(self) -> None:
        """Close connection pool."""
        try:
            if self._client:
                await self._client.close()

            await self.pool.disconnect()

            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")

    def __repr__(self) -> str:
        return (
            f"RedisConnectionPool(host={self.host}, port={self.port}, "
            f"max_connections={self.max_connections})"
        )


# Global connection pool instance
_redis_pool: Optional[RedisConnectionPool] = None


def get_redis_pool(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    max_connections: int = 150,  # Increased for 5-100 concurrent users
) -> RedisConnectionPool:
    """
    Get or create global Redis connection pool.

    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Optional password
        max_connections: Maximum connections

    Returns:
        RedisConnectionPool: Connection pool instance
    """
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = RedisConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
        )

    return _redis_pool


async def cleanup_redis_pool() -> None:
    """Cleanup global Redis connection pool."""
    global _redis_pool

    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
