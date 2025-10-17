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


class RedisConnectionPool:
    """
    Redis connection pool manager.

    Features:
    - Connection pooling
    - Health checks
    - Automatic reconnection
    - Statistics tracking
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
        Get connection pool statistics.

        Returns:
            dict: Pool statistics
        """
        try:
            client = self.get_client()
            info = await client.info("stats")

            return {
                "max_connections": self.max_connections,
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return {}

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
