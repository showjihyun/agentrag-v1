"""
Async Database connection and session management.

Provides async SQLAlchemy support for better performance with FastAPI.
Use this for new async endpoints while maintaining backward compatibility
with sync sessions.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import event, text

from backend.config import settings

logger = logging.getLogger(__name__)


def get_async_database_url() -> str:
    """
    Convert sync database URL to async format.
    
    postgresql://user:pass@host:port/db -> postgresql+asyncpg://user:pass@host:port/db
    """
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# Create async engine with optimized connection pooling
async_engine: AsyncEngine = create_async_engine(
    get_async_database_url(),
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session for dependency injection.
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            db: AsyncSession = Depends(get_async_db)
        ):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    
    TRANSACTION RULES:
    - This function manages session lifecycle only
    - Repository/Service layer handles commit/rollback
    - Session is always closed in finally block
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with async_session_scope() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_async_db():
    """Initialize async database - create all tables."""
    from backend.db.database import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Async database initialized")


async def close_async_db():
    """Close async database connections."""
    await async_engine.dispose()
    logger.info("Async database connections closed")


async def check_async_db_connection() -> bool:
    """
    Check if async database connection is healthy.
    
    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Async database connection check failed: {e}")
        return False


async def get_async_pool_status() -> dict:
    """
    Get current async connection pool status.
    
    Returns:
        Dictionary with pool statistics
    """
    pool = async_engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
        "is_async": True,
    }


# ============================================================================
# Async Repository Base Class
# ============================================================================

from typing import TypeVar, Generic, Type, List, Any, Dict
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

T = TypeVar('T')


class AsyncBaseRepository(Generic[T]):
    """
    Async base repository with common CRUD operations.
    
    Usage:
        class UserRepository(AsyncBaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
            
            async def get_by_email(self, email: str) -> Optional[User]:
                result = await self.session.execute(
                    select(User).where(User.email == email)
                )
                return result.scalar_one_or_none()
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
        self.model_name = model.__name__
    
    async def get_by_id(
        self,
        id: Any,
        load_relations: List[str] = None
    ) -> Optional[T]:
        """
        Get entity by ID with optional eager loading.
        
        Args:
            id: Entity ID
            load_relations: List of relationship names to eager load
        """
        query = select(self.model).where(self.model.id == id)
        
        # Apply eager loading for specified relations
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        load_relations: List[str] = None
    ) -> List[T]:
        """Get all entities with pagination."""
        query = select(self.model).limit(limit).offset(offset)
        
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        """Update entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity: T) -> None:
        """Delete entity."""
        await self.session.delete(entity)
        await self.session.flush()
    
    async def exists(self, id: Any) -> bool:
        """Check if entity exists."""
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar() > 0
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count entities with optional filters."""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()
