"""
Milvus Connection Pool Manager

Provides efficient connection pooling for Milvus vector database operations.
"""

import logging
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager
from pymilvus import connections, Collection, MilvusException
import time

logger = logging.getLogger(__name__)


class MilvusConnectionPool:
    """
    Connection pool manager for Milvus.

    Features:
    - Connection pooling with configurable size
    - Automatic connection health checks
    - Connection reuse and lifecycle management
    - Thread-safe operations
    """

    def __init__(
        self,
        host: str,
        port: int,
        pool_size: int = 10,  # Increased for 5-100 concurrent users
        max_idle_time: int = 300,
        health_check_interval: int = 60,
    ):
        """
        Initialize Milvus connection pool.

        Args:
            host: Milvus server host
            port: Milvus server port
            pool_size: Maximum number of connections in pool
            max_idle_time: Maximum idle time before connection refresh (seconds)
            health_check_interval: Interval for health checks (seconds)
        """
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval

        self._connections: List[dict] = []
        self._lock = asyncio.Lock()
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info(
            f"MilvusConnectionPool initialized: {host}:{port} "
            f"(pool_size={pool_size})"
        )

    async def initialize(self) -> None:
        """Initialize connection pool."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info(f"Creating {self.pool_size} Milvus connections...")

            for i in range(self.pool_size):
                try:
                    alias = f"milvus_pool_{i}"
                    connections.connect(alias=alias, host=self.host, port=self.port)

                    self._connections.append(
                        {
                            "alias": alias,
                            "in_use": False,
                            "last_used": time.time(),
                            "created_at": time.time(),
                        }
                    )

                    logger.debug(f"Created connection: {alias}")

                except MilvusException as e:
                    logger.error(f"Failed to create connection {i}: {e}")
                    raise

            self._initialized = True
            logger.info(
                f"Connection pool initialized with {len(self._connections)} connections"
            )

            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.

        Usage:
            async with pool.acquire() as alias:
                # Use connection with alias
                collection = Collection("my_collection", using=alias)
        """
        if not self._initialized:
            await self.initialize()

        connection = await self._get_connection()

        try:
            yield connection["alias"]
        finally:
            await self._release_connection(connection)

    async def _get_connection(self) -> dict:
        """Get an available connection from the pool."""
        max_wait = 30  # Maximum wait time in seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            async with self._lock:
                # Find available connection
                for conn in self._connections:
                    if not conn["in_use"]:
                        conn["in_use"] = True
                        conn["last_used"] = time.time()
                        logger.debug(f"Acquired connection: {conn['alias']}")
                        return conn

            # No connection available, wait a bit
            await asyncio.sleep(0.1)

        raise TimeoutError("Failed to acquire Milvus connection within timeout")

    async def _release_connection(self, connection: dict) -> None:
        """Release a connection back to the pool."""
        async with self._lock:
            connection["in_use"] = False
            connection["last_used"] = time.time()
            logger.debug(f"Released connection: {connection['alias']}")

    async def _health_check_loop(self) -> None:
        """Periodic health check for connections."""
        while self._initialized:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self) -> None:
        """Perform health check on all connections."""
        async with self._lock:
            current_time = time.time()

            for conn in self._connections:
                if conn["in_use"]:
                    continue

                # Check if connection is idle for too long
                idle_time = current_time - conn["last_used"]
                if idle_time > self.max_idle_time:
                    logger.info(
                        f"Refreshing idle connection: {conn['alias']} "
                        f"(idle for {idle_time:.0f}s)"
                    )

                    try:
                        # Disconnect and reconnect
                        connections.disconnect(alias=conn["alias"])
                        connections.connect(
                            alias=conn["alias"], host=self.host, port=self.port
                        )
                        conn["last_used"] = current_time
                        logger.debug(f"Connection refreshed: {conn['alias']}")
                    except Exception as e:
                        logger.error(
                            f"Failed to refresh connection {conn['alias']}: {e}"
                        )

    async def get_stats(self) -> dict:
        """Get connection pool statistics."""
        async with self._lock:
            in_use = sum(1 for conn in self._connections if conn["in_use"])
            available = len(self._connections) - in_use

            return {
                "total_connections": len(self._connections),
                "in_use": in_use,
                "available": available,
                "pool_size": self.pool_size,
                "host": self.host,
                "port": self.port,
            }

    async def close(self) -> None:
        """Close all connections in the pool."""
        if not self._initialized:
            return

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            logger.info("Closing Milvus connection pool...")

            for conn in self._connections:
                try:
                    connections.disconnect(alias=conn["alias"])
                    logger.debug(f"Closed connection: {conn['alias']}")
                except Exception as e:
                    logger.error(f"Error closing connection {conn['alias']}: {e}")

            self._connections.clear()
            self._initialized = False

            logger.info("Milvus connection pool closed")

    def __repr__(self) -> str:
        return (
            f"MilvusConnectionPool(host={self.host}, port={self.port}, "
            f"pool_size={self.pool_size}, initialized={self._initialized})"
        )


# Global pool instance
_milvus_pool: Optional[MilvusConnectionPool] = None


def get_milvus_pool(host: str, port: int, pool_size: int = 10) -> MilvusConnectionPool:  # Increased for 5-100 concurrent users
    """
    Get or create global Milvus connection pool.

    Args:
        host: Milvus server host
        port: Milvus server port
        pool_size: Maximum number of connections

    Returns:
        MilvusConnectionPool: Connection pool instance
    """
    global _milvus_pool

    if _milvus_pool is None:
        _milvus_pool = MilvusConnectionPool(host=host, port=port, pool_size=pool_size)

    return _milvus_pool


async def cleanup_milvus_pool() -> None:
    """Cleanup global Milvus connection pool."""
    global _milvus_pool

    if _milvus_pool:
        await _milvus_pool.close()
        _milvus_pool = None
        logger.info("Global Milvus connection pool cleaned up")
