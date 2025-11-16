"""
Read replica support for database load balancing.

This module provides utilities for routing read queries to read replicas
and write queries to the primary database.
"""

from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
import logging
import random

from backend.config import settings

logger = logging.getLogger(__name__)


class DatabaseRouter:
    """Database router for read/write splitting"""
    
    def __init__(
        self,
        primary_url: str,
        replica_urls: Optional[list[str]] = None,
        pool_size: int = 20,
        max_overflow: int = 30
    ):
        """
        Initialize database router with primary and replica connections.
        
        Args:
            primary_url: Primary database URL (for writes)
            replica_urls: List of read replica URLs (for reads)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        self.primary_url = primary_url
        self.replica_urls = replica_urls or []
        
        # Create primary engine
        self.primary_engine = create_engine(
            primary_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo_pool=False,
        )
        
        # Create replica engines
        self.replica_engines = []
        for replica_url in self.replica_urls:
            engine = create_engine(
                replica_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo_pool=False,
            )
            self.replica_engines.append(engine)
        
        # Create session factories
        self.PrimarySession = sessionmaker(
            bind=self.primary_engine,
            autocommit=False,
            autoflush=False
        )
        
        self.ReplicaSessions = [
            sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False
            )
            for engine in self.replica_engines
        ]
        
        logger.info(
            f"Database router initialized: "
            f"1 primary, {len(self.replica_engines)} replicas"
        )
    
    def get_primary_session(self) -> Session:
        """Get a session connected to the primary database (for writes)"""
        return self.PrimarySession()
    
    def get_replica_session(self) -> Session:
        """
        Get a session connected to a read replica (for reads).
        Falls back to primary if no replicas available.
        """
        if not self.ReplicaSessions:
            logger.debug("No replicas available, using primary")
            return self.PrimarySession()
        
        # Random load balancing across replicas
        session_factory = random.choice(self.ReplicaSessions)
        return session_factory()
    
    @contextmanager
    def primary_session(self) -> Generator[Session, None, None]:
        """Context manager for primary database session"""
        session = self.get_primary_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def replica_session(self) -> Generator[Session, None, None]:
        """Context manager for read replica session"""
        session = self.get_replica_session()
        try:
            yield session
        finally:
            session.close()
    
    def close_all(self):
        """Close all database connections"""
        self.primary_engine.dispose()
        for engine in self.replica_engines:
            engine.dispose()
        logger.info("All database connections closed")


# Global router instance
_router: Optional[DatabaseRouter] = None


def init_database_router(
    primary_url: Optional[str] = None,
    replica_urls: Optional[list[str]] = None
):
    """
    Initialize the global database router.
    
    Args:
        primary_url: Primary database URL (defaults to settings.DATABASE_URL)
        replica_urls: List of replica URLs (defaults to settings.READ_REPLICA_URLS)
    """
    global _router
    
    if _router is not None:
        logger.warning("Database router already initialized")
        return _router
    
    primary_url = primary_url or settings.DATABASE_URL
    replica_urls = replica_urls or getattr(settings, 'READ_REPLICA_URLS', [])
    
    _router = DatabaseRouter(
        primary_url=primary_url,
        replica_urls=replica_urls
    )
    
    return _router


def get_router() -> DatabaseRouter:
    """Get the global database router instance"""
    global _router
    
    if _router is None:
        raise RuntimeError(
            "Database router not initialized. "
            "Call init_database_router() first."
        )
    
    return _router


# Convenience functions

def get_write_db() -> Session:
    """Get a database session for write operations"""
    return get_router().get_primary_session()


def get_read_db() -> Session:
    """Get a database session for read operations"""
    return get_router().get_replica_session()


@contextmanager
def write_session() -> Generator[Session, None, None]:
    """Context manager for write operations"""
    with get_router().primary_session() as session:
        yield session


@contextmanager
def read_session() -> Generator[Session, None, None]:
    """Context manager for read operations"""
    with get_router().replica_session() as session:
        yield session


# FastAPI dependency functions

def get_write_db_dependency():
    """FastAPI dependency for write database session"""
    db = get_write_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_read_db_dependency():
    """FastAPI dependency for read database session"""
    db = get_read_db()
    try:
        yield db
    finally:
        db.close()


# Session routing decorator

def use_replica(func):
    """
    Decorator to force a function to use read replica.
    
    Usage:
        @use_replica
        def get_user(db: Session, user_id: str):
            return db.query(User).filter(User.id == user_id).first()
    """
    def wrapper(*args, **kwargs):
        # Check if 'db' is in kwargs
        if 'db' in kwargs:
            # Replace with replica session
            original_db = kwargs['db']
            kwargs['db'] = get_read_db()
            try:
                return func(*args, **kwargs)
            finally:
                kwargs['db'].close()
                kwargs['db'] = original_db
        else:
            return func(*args, **kwargs)
    
    return wrapper


# Health check functions

def check_primary_health() -> bool:
    """Check if primary database is healthy"""
    try:
        with write_session() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Primary database health check failed: {e}")
        return False


def check_replica_health() -> dict:
    """Check health of all read replicas"""
    router = get_router()
    results = {}
    
    for i, session_factory in enumerate(router.ReplicaSessions):
        try:
            session = session_factory()
            session.execute("SELECT 1")
            session.close()
            results[f"replica_{i}"] = "healthy"
        except Exception as e:
            logger.error(f"Replica {i} health check failed: {e}")
            results[f"replica_{i}"] = "unhealthy"
    
    return results


# Example usage

def example_read_query():
    """Example: Read from replica"""
    with read_session() as db:
        from backend.db.models.user import User
        users = db.query(User).limit(10).all()
        return users


def example_write_query():
    """Example: Write to primary"""
    with write_session() as db:
        from backend.db.models.user import User
        user = User(username="test", email="test@example.com")
        db.add(user)
        # Automatically committed by context manager


def example_fastapi_endpoint():
    """Example: FastAPI endpoint with read replica"""
    from fastapi import Depends
    
    # Read endpoint - use replica
    # @router.get("/users")
    # async def list_users(db: Session = Depends(get_read_db_dependency)):
    #     return db.query(User).all()
    
    # Write endpoint - use primary
    # @router.post("/users")
    # async def create_user(
    #     user_data: UserCreate,
    #     db: Session = Depends(get_write_db_dependency)
    # ):
    #     user = User(**user_data.dict())
    #     db.add(user)
    #     return user
    
    pass


# Configuration example for settings.py

"""
# Add to backend/config.py:

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Read replica URLs (comma-separated)
    READ_REPLICA_URLS: Optional[str] = None
    
    @property
    def read_replica_urls_list(self) -> list[str]:
        if not self.READ_REPLICA_URLS:
            return []
        return [url.strip() for url in self.READ_REPLICA_URLS.split(',')]

# Usage in main.py:

from backend.db.read_replica import init_database_router

@app.on_event("startup")
async def startup_event():
    # Initialize database router
    init_database_router(
        primary_url=settings.DATABASE_URL,
        replica_urls=settings.read_replica_urls_list
    )
"""
