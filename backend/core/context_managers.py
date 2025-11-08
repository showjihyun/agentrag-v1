"""Context managers for resource management."""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, AsyncGenerator, Generator
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# ============================================================================
# Database Transaction Context Managers
# ============================================================================

@asynccontextmanager
async def db_transaction(
    db: Session,
    auto_commit: bool = True,
    logger_instance: Optional[logging.Logger] = None
) -> AsyncGenerator[Session, None]:
    """
    Database transaction context manager with automatic commit/rollback.
    
    Args:
        db: Database session
        auto_commit: Whether to auto-commit on success
        logger_instance: Optional logger instance
        
    Yields:
        Database session
        
    Example:
        async with db_transaction(db) as session:
            bookmark = Bookmark(...)
            session.add(bookmark)
            # Auto-commit on success, auto-rollback on error
    """
    log = logger_instance or logger
    start_time = datetime.utcnow()
    
    try:
        log.debug("Starting database transaction")
        yield db
        
        if auto_commit:
            db.commit()
            duration = (datetime.utcnow() - start_time).total_seconds()
            log.debug(f"Transaction committed successfully ({duration:.3f}s)")
    
    except SQLAlchemyError as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.error(
            f"Database error, transaction rolled back ({duration:.3f}s)",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise
    
    except Exception as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.error(
            f"Unexpected error, transaction rolled back ({duration:.3f}s)",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise
    
    finally:
        # Session cleanup is handled by FastAPI dependency
        pass


@contextmanager
def db_transaction_sync(
    db: Session,
    auto_commit: bool = True,
    logger_instance: Optional[logging.Logger] = None
) -> Generator[Session, None, None]:
    """
    Synchronous database transaction context manager.
    
    Args:
        db: Database session
        auto_commit: Whether to auto-commit on success
        logger_instance: Optional logger instance
        
    Yields:
        Database session
    """
    log = logger_instance or logger
    start_time = datetime.utcnow()
    
    try:
        log.debug("Starting database transaction (sync)")
        yield db
        
        if auto_commit:
            db.commit()
            duration = (datetime.utcnow() - start_time).total_seconds()
            log.debug(f"Transaction committed successfully ({duration:.3f}s)")
    
    except SQLAlchemyError as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.error(
            f"Database error, transaction rolled back ({duration:.3f}s)",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise
    
    except Exception as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.error(
            f"Unexpected error, transaction rolled back ({duration:.3f}s)",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise


# ============================================================================
# Timing Context Manager
# ============================================================================

@contextmanager
def timer(
    operation_name: str,
    logger_instance: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG
):
    """
    Context manager for timing operations.
    
    Args:
        operation_name: Name of the operation being timed
        logger_instance: Optional logger instance
        log_level: Log level for timing messages
        
    Example:
        with timer("fetch_bookmarks"):
            bookmarks = await service.get_bookmarks(...)
        # Logs: "fetch_bookmarks completed in 0.123s"
    """
    log = logger_instance or logger
    start_time = datetime.utcnow()
    
    try:
        yield
    finally:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.log(
            log_level,
            f"{operation_name} completed",
            extra={"operation": operation_name, "duration_seconds": duration}
        )


@asynccontextmanager
async def async_timer(
    operation_name: str,
    logger_instance: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG
):
    """
    Async context manager for timing operations.
    
    Args:
        operation_name: Name of the operation being timed
        logger_instance: Optional logger instance
        log_level: Log level for timing messages
    """
    log = logger_instance or logger
    start_time = datetime.utcnow()
    
    try:
        yield
    finally:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.log(
            log_level,
            f"{operation_name} completed",
            extra={"operation": operation_name, "duration_seconds": duration}
        )


# ============================================================================
# Error Suppression Context Manager
# ============================================================================

@contextmanager
def suppress_and_log(
    *exceptions,
    logger_instance: Optional[logging.Logger] = None,
    message: str = "Suppressed exception"
):
    """
    Context manager to suppress specific exceptions and log them.
    
    Args:
        *exceptions: Exception types to suppress
        logger_instance: Optional logger instance
        message: Log message
        
    Example:
        with suppress_and_log(ValueError, KeyError, message="Invalid data"):
            # Code that might raise ValueError or KeyError
            process_data(data)
        # Exceptions are logged but not raised
    """
    log = logger_instance or logger
    
    try:
        yield
    except exceptions as e:
        log.warning(
            message,
            extra={
                "exception_type": type(e).__name__,
                "exception_message": str(e)
            }
        )


# ============================================================================
# Batch Processing Context Manager
# ============================================================================

@asynccontextmanager
async def batch_processor(
    items: list,
    batch_size: int = 100,
    logger_instance: Optional[logging.Logger] = None
):
    """
    Context manager for batch processing with progress logging.
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        logger_instance: Optional logger instance
        
    Yields:
        Tuple of (batch_items, batch_number, total_batches)
        
    Example:
        async with batch_processor(bookmarks, batch_size=50) as processor:
            for batch, batch_num, total in processor:
                await process_batch(batch)
    """
    log = logger_instance or logger
    total_items = len(items)
    total_batches = (total_items + batch_size - 1) // batch_size
    
    log.info(
        f"Starting batch processing",
        extra={
            "total_items": total_items,
            "batch_size": batch_size,
            "total_batches": total_batches
        }
    )
    
    start_time = datetime.utcnow()
    
    try:
        def batch_generator():
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                yield batch, batch_num, total_batches
        
        yield batch_generator()
    
    finally:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log.info(
            f"Batch processing completed",
            extra={
                "total_items": total_items,
                "duration_seconds": duration,
                "items_per_second": total_items / duration if duration > 0 else 0
            }
        )
