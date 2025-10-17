"""
PostgreSQL Read Replica Manager

Implements read/write splitting for improved performance and scalability.
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import time

from backend.config import settings

logger = logging.getLogger(__name__)


class ReadReplicaManager:
    """
    Manages read/write splitting between primary and replica databases.

    Features:
    - Automatic routing (read → replica, write → primary)
    - Health checking and failover
    - Connection pooling for both databases
    - Replication lag monitoring
    """

    def __init__(
        self,
        primary_url: str,
        replica_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        health_check_interval: int = 30,
    ):
        """
        Initialize Read Replica Manager.

        Args:
            primary_url: Primary database URL
            replica_url: Replica database URL (optional)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            health_check_interval: Health check interval in seconds
        """
        self.primary_url = primary_url
        self.replica_url = replica_url or primary_url  # Fallback to primary
        self.health_check_interval = health_check_interval

        # Create engines
        self.primary_engine = self._create_engine(
            self.primary_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_name="primary",
        )

        if replica_url:
            self.replica_engine = self._create_engine(
                self.replica_url,
                pool_size=pool_size * 2,  # More connections for reads
                max_overflow=max_overflow * 2,
                pool_name="replica",
            )
        else:
            self.replica_engine = self.primary_engine
            logger.warning("No replica URL provided, using primary for reads")

        # Session factories
        self.PrimarySession = sessionmaker(
            autocommit=False, autoflush=False, bind=self.primary_engine
        )

        self.ReplicaSession = sessionmaker(
            autocommit=False, autoflush=False, bind=self.replica_engine
        )

        # Health status
        self._replica_healthy = True
        self._last_health_check = 0

        # Statistics
        self.stats = {"read_queries": 0, "write_queries": 0, "replica_failovers": 0}

        logger.info(
            f"ReadReplicaManager initialized: "
            f"primary={primary_url}, replica={replica_url}"
        )

    def _create_engine(
        self, url: str, pool_size: int, max_overflow: int, pool_name: str
    ):
        """Create SQLAlchemy engine with optimized settings."""
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=1800,  # 30 minutes
            pool_timeout=10,
            echo=settings.DEBUG,
            connect_args={"options": f"-c statement_timeout=30000"},
        )

        # Add event listeners for monitoring
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug(f"New {pool_name} connection established")

        return engine

    def _check_replica_health(self) -> bool:
        """
        Check replica health.

        Returns:
            True if replica is healthy, False otherwise
        """
        current_time = time.time()

        # Skip if checked recently
        if current_time - self._last_health_check < self.health_check_interval:
            return self._replica_healthy

        self._last_health_check = current_time

        try:
            # Simple health check query
            with self.replica_engine.connect() as conn:
                result = conn.execute("SELECT 1").scalar()
                self._replica_healthy = result == 1

            if not self._replica_healthy:
                logger.warning("Replica health check failed")

            return self._replica_healthy

        except Exception as e:
            logger.error(f"Replica health check error: {e}")
            self._replica_healthy = False
            return False

    @contextmanager
    def get_read_session(self) -> Generator[Session, None, None]:
        """
        Get session for read operations.

        Uses replica if healthy, otherwise falls back to primary.

        Yields:
            Database session for read operations
        """
        self.stats["read_queries"] += 1

        # Check replica health
        if self._check_replica_health():
            session = self.ReplicaSession()
            logger.debug("Using replica for read")
        else:
            session = self.PrimarySession()
            self.stats["replica_failovers"] += 1
            logger.warning("Replica unhealthy, using primary for read")

        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def get_write_session(self) -> Generator[Session, None, None]:
        """
        Get session for write operations.

        Always uses primary database.

        Yields:
            Database session for write operations
        """
        self.stats["write_queries"] += 1
        session = self.PrimarySession()
        logger.debug("Using primary for write")

        try:
            yield session
        finally:
            session.close()

    def get_replication_lag(self) -> Optional[dict]:
        """
        Get replication lag information.

        Returns:
            Dictionary with lag information or None if not available
        """
        try:
            with self.primary_engine.connect() as conn:
                result = conn.execute(
                    """
                    SELECT
                        client_addr,
                        state,
                        pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
                        EXTRACT(EPOCH FROM (now() - replay_lag)) AS lag_seconds
                    FROM pg_stat_replication
                    WHERE application_name = 'walreceiver'
                    LIMIT 1
                """
                ).fetchone()

                if result:
                    return {
                        "client_addr": str(result[0]),
                        "state": result[1],
                        "lag_bytes": int(result[2]) if result[2] else 0,
                        "lag_seconds": float(result[3]) if result[3] else 0,
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to get replication lag: {e}")
            return None

    def get_stats(self) -> dict:
        """
        Get read/write statistics.

        Returns:
            Dictionary with statistics
        """
        total_queries = self.stats["read_queries"] + self.stats["write_queries"]
        read_ratio = (
            (self.stats["read_queries"] / total_queries * 100)
            if total_queries > 0
            else 0
        )

        return {
            "read_queries": self.stats["read_queries"],
            "write_queries": self.stats["write_queries"],
            "total_queries": total_queries,
            "read_ratio": round(read_ratio, 2),
            "replica_failovers": self.stats["replica_failovers"],
            "replica_healthy": self._replica_healthy,
        }

    def close(self):
        """Close all connections."""
        self.primary_engine.dispose()
        if self.replica_engine != self.primary_engine:
            self.replica_engine.dispose()
        logger.info("ReadReplicaManager closed")


# Global instance
_replica_manager: Optional[ReadReplicaManager] = None


def initialize_read_replica(
    primary_url: str = None, replica_url: str = None
) -> ReadReplicaManager:
    """
    Initialize global read replica manager.

    Args:
        primary_url: Primary database URL (default: from settings)
        replica_url: Replica database URL (default: from settings)

    Returns:
        ReadReplicaManager instance
    """
    global _replica_manager

    if _replica_manager is None:
        primary_url = primary_url or settings.DATABASE_URL
        replica_url = replica_url or getattr(settings, "DATABASE_REPLICA_URL", None)

        _replica_manager = ReadReplicaManager(
            primary_url=primary_url,
            replica_url=replica_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )

        logger.info("Global read replica manager initialized")

    return _replica_manager


def get_replica_manager() -> ReadReplicaManager:
    """
    Get global read replica manager.

    Returns:
        ReadReplicaManager instance

    Raises:
        RuntimeError: If not initialized
    """
    if _replica_manager is None:
        raise RuntimeError(
            "Read replica manager not initialized. "
            "Call initialize_read_replica() first."
        )
    return _replica_manager


def get_db_read() -> Generator[Session, None, None]:
    """
    Get database session for read operations.

    Usage:
        db = get_db_read()
        documents = db.query(Document).all()

    Yields:
        Database session for read operations
    """
    manager = get_replica_manager()
    with manager.get_read_session() as session:
        yield session


def get_db_write() -> Generator[Session, None, None]:
    """
    Get database session for write operations.

    Usage:
        db = get_db_write()
        db.add(document)
        db.commit()

    Yields:
        Database session for write operations
    """
    manager = get_replica_manager()
    with manager.get_write_session() as session:
        yield session


def cleanup_read_replica():
    """Cleanup global read replica manager."""
    global _replica_manager

    if _replica_manager:
        _replica_manager.close()
        _replica_manager = None
        logger.info("Global read replica manager cleaned up")
