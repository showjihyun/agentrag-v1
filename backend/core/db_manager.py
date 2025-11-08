"""
Database Manager with Read/Write Splitting

Provides read replica support and connection pooling optimization.
"""

import logging
import random
from typing import List, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database Manager with Read/Write splitting.
    
    Supports:
    - Write operations to master database
    - Read operations to replica databases (round-robin)
    - Connection pooling
    - Health checks
    """
    
    def __init__(
        self,
        write_url: str,
        read_urls: Optional[List[str]] = None,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False
    ):
        """
        Initialize Database Manager.
        
        Args:
            write_url: Master database URL
            read_urls: List of replica database URLs
            pool_size: Base connection pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Connection timeout in seconds
            pool_recycle: Recycle connections after seconds
            pool_pre_ping: Enable connection health check
            echo: Enable SQL echo (debugging)
        """
        self.write_url = write_url
        self.read_urls = read_urls or []
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.echo = echo
        
        # Create engines
        self.write_engine = self._create_engine(
            write_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            label="write"
        )
        
        self.read_engines = [
            self._create_engine(
                url,
                pool_size=pool_size // 2,  # Smaller pool for replicas
                max_overflow=max_overflow // 2,
                label=f"read_{i}"
            )
            for i, url in enumerate(self.read_urls)
        ]
        
        # If no read replicas, use write engine for reads
        if not self.read_engines:
            self.read_engines = [self.write_engine]
            logger.warning("No read replicas configured, using write engine for reads")
        
        # Round-robin index for read replicas
        self.current_read_index = 0
        
        # Session factories
        self.WriteSession = sessionmaker(bind=self.write_engine)
        self.ReadSession = sessionmaker(bind=self.read_engines[0])
        
        logger.info(
            f"Database manager initialized: "
            f"1 write engine, {len(self.read_engines)} read engines"
        )
    
    def _create_engine(
        self,
        url: str,
        pool_size: int,
        max_overflow: int,
        label: str
    ):
        """
        Create SQLAlchemy engine with connection pooling.
        
        Args:
            url: Database URL
            pool_size: Pool size
            max_overflow: Max overflow
            label: Engine label for logging
            
        Returns:
            SQLAlchemy engine
        """
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo
        )
        
        # Add event listeners for monitoring
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug(f"[{label}] New database connection established")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug(f"[{label}] Connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            logger.debug(f"[{label}] Connection returned to pool")
        
        logger.info(
            f"[{label}] Engine created: pool_size={pool_size}, "
            f"max_overflow={max_overflow}"
        )
        
        return engine
    
    @contextmanager
    def get_write_session(self) -> Session:
        """
        Get a write session (master database).
        
        Yields:
            SQLAlchemy session for write operations
        """
        session = self.WriteSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Write session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_read_session(self, strategy: str = "round_robin") -> Session:
        """
        Get a read session (replica database).
        
        Args:
            strategy: Load balancing strategy (round_robin, random, least_connections)
            
        Yields:
            SQLAlchemy session for read operations
        """
        engine = self._select_read_engine(strategy)
        SessionClass = sessionmaker(bind=engine)
        session = SessionClass()
        
        try:
            yield session
        except Exception as e:
            logger.error(f"Read session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def _select_read_engine(self, strategy: str = "round_robin"):
        """
        Select a read engine based on strategy.
        
        Args:
            strategy: Load balancing strategy
            
        Returns:
            Selected engine
        """
        if strategy == "round_robin":
            # Round-robin selection
            engine = self.read_engines[self.current_read_index]
            self.current_read_index = (
                (self.current_read_index + 1) % len(self.read_engines)
            )
            return engine
        
        elif strategy == "random":
            # Random selection
            return random.choice(self.read_engines)
        
        elif strategy == "least_connections":
            # Select engine with least connections (simplified)
            # In production, track actual connection counts
            return min(
                self.read_engines,
                key=lambda e: e.pool.size() - e.pool.checkedin()
            )
        
        else:
            # Default to round-robin
            return self._select_read_engine("round_robin")
    
    def get_pool_status(self) -> dict:
        """
        Get connection pool status.
        
        Returns:
            Pool status dictionary
        """
        def get_engine_status(engine, label):
            pool = engine.pool
            return {
                "label": label,
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.size() - pool.checkedin(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow()
            }
        
        status = {
            "write": get_engine_status(self.write_engine, "write"),
            "read": [
                get_engine_status(engine, f"read_{i}")
                for i, engine in enumerate(self.read_engines)
            ]
        }
        
        return status
    
    def health_check(self) -> dict:
        """
        Perform health check on all databases.
        
        Returns:
            Health check results
        """
        results = {
            "write": self._check_engine_health(self.write_engine, "write"),
            "read": [
                self._check_engine_health(engine, f"read_{i}")
                for i, engine in enumerate(self.read_engines)
            ]
        }
        
        return results
    
    def _check_engine_health(self, engine, label: str) -> dict:
        """
        Check health of a single engine.
        
        Args:
            engine: SQLAlchemy engine
            label: Engine label
            
        Returns:
            Health check result
        """
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            
            return {
                "label": label,
                "status": "healthy",
                "error": None
            }
        except Exception as e:
            logger.error(f"[{label}] Health check failed: {e}")
            return {
                "label": label,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def dispose(self):
        """Dispose all engines and close connections."""
        self.write_engine.dispose()
        for engine in self.read_engines:
            if engine != self.write_engine:
                engine.dispose()
        
        logger.info("All database engines disposed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager


def initialize_db_manager(
    write_url: str,
    read_urls: Optional[List[str]] = None,
    **kwargs
) -> DatabaseManager:
    """
    Initialize global database manager.
    
    Args:
        write_url: Master database URL
        read_urls: List of replica database URLs
        **kwargs: Additional arguments for DatabaseManager
        
    Returns:
        Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(
            write_url=write_url,
            read_urls=read_urls,
            **kwargs
        )
    return _db_manager


def cleanup_db_manager():
    """Cleanup global database manager."""
    global _db_manager
    if _db_manager is not None:
        _db_manager.dispose()
        _db_manager = None
