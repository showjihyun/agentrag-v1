"""Database connection and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

# Create engine with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo_pool=settings.DB_ECHO_POOL,
    echo=settings.DEBUG,
    connect_args={"options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT}"},
)

# Setup pool monitoring (Phase 1)
try:
    from backend.db.pool_monitor import setup_pool_monitoring

    pool_monitor = setup_pool_monitoring(
        engine=engine, 
        long_connection_threshold=10.0,  # Increased for document processing
        leak_detection_threshold=60.0    # Increased for long-running operations
    )
    logger.info("✅ Pool monitoring enabled")
except Exception as e:
    logger.warning(f"Pool monitoring setup failed: {e}")

# Connection Pool Event Listeners (for monitoring)
if settings.DEBUG:

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log when a new connection is established."""
        logger.debug("Database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log when a connection is checked out from pool."""
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log when a connection is returned to pool."""
        logger.debug("Connection returned to pool")


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Get database session for dependency injection.

    TRANSACTION BOUNDARY RULES:
    ===========================

    1. **Dependency Role**: This function ONLY manages session lifecycle (create/close)
       - Creates session at request start
       - Closes session at request end
       - Does NOT commit or rollback

    2. **Repository Role**: Repositories handle their own transactions
       - Each repository method should commit on success
       - Each repository method should rollback on error
       - Use try/except blocks in repository methods

    3. **Service Layer Role**: For complex multi-repository transactions
       - Service layer can manage transaction across multiple repositories
       - Pass db session to multiple repository calls
       - Commit once at service layer after all operations succeed

    EXAMPLES:
    =========

    Simple Repository Pattern:
    ```python
    class UserRepository:
        def create_user(self, user_data):
            try:
                user = User(**user_data)
                self.db.add(user)
                self.db.commit()  # Repository commits
                return user
            except Exception as e:
                self.db.rollback()  # Repository rolls back
                raise
    ```

    Complex Service Pattern:
    ```python
    class UserService:
        def create_user_with_profile(self, user_data, profile_data):
            try:
                # Multiple repository calls in one transaction
                user = user_repo.create_user_no_commit(user_data)
                profile = profile_repo.create_profile_no_commit(user.id, profile_data)

                self.db.commit()  # Service commits once
                return user, profile
            except Exception as e:
                self.db.rollback()  # Service rolls back
                raise
    ```

    Usage in FastAPI:
    ```python
    from fastapi import Depends
    from backend.db.database import get_db

    @app.post("/users")
    def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
        repo = UserRepository(db)
        return repo.create_user(user_data)  # Repo handles commit
    ```

    IMPORTANT:
    ==========
    - Never commit/rollback in this dependency function
    - Always commit/rollback in Repository or Service layer
    - Session is always closed in finally block (automatic cleanup)
    - This prevents double commit/rollback issues
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Always close the session (but never commit/rollback here)
        db.close()


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)


def get_pool_status():
    """
    Get current connection pool status.

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
    }
