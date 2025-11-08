"""Transaction management utilities."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Callable, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@contextmanager
def transaction(db: Session, auto_commit: bool = True) -> Generator[Session, None, None]:
    """
    Context manager for database transactions.
    
    Automatically commits on success and rolls back on error.
    
    Args:
        db: Database session
        auto_commit: Whether to auto-commit on success (default: True)
        
    Yields:
        Database session
        
    Example:
        ```python
        with transaction(db) as session:
            agent = Agent(...)
            session.add(agent)
            # Automatically commits here
        ```
    """
    try:
        yield db
        if auto_commit:
            db.commit()
            logger.debug("Transaction committed successfully")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Transaction rolled back due to SQLAlchemy error: {e}", exc_info=True)
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back due to error: {e}", exc_info=True)
        raise


@contextmanager
def nested_transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for nested transactions (savepoints).
    
    Useful for operations that need to be rolled back independently
    without affecting the outer transaction.
    
    Args:
        db: Database session
        
    Yields:
        Database session
        
    Example:
        ```python
        with transaction(db):
            # Outer transaction
            agent = Agent(...)
            db.add(agent)
            
            try:
                with nested_transaction(db):
                    # Inner transaction (savepoint)
                    risky_operation()
            except Exception:
                # Inner transaction rolled back, outer continues
                pass
            
            # Outer transaction commits
        ```
    """
    savepoint = db.begin_nested()
    try:
        yield db
        savepoint.commit()
        logger.debug("Nested transaction committed successfully")
    except SQLAlchemyError as e:
        savepoint.rollback()
        logger.error(f"Nested transaction rolled back due to SQLAlchemy error: {e}", exc_info=True)
        raise
    except Exception as e:
        savepoint.rollback()
        logger.error(f"Nested transaction rolled back due to error: {e}", exc_info=True)
        raise


def transactional(auto_commit: bool = True):
    """
    Decorator for transactional methods.
    
    Wraps a method with transaction management. The first argument
    must be a database session.
    
    Args:
        auto_commit: Whether to auto-commit on success (default: True)
        
    Returns:
        Decorated function
        
    Example:
        ```python
        class AgentService:
            @transactional()
            def create_agent(self, db: Session, data: AgentCreate) -> Agent:
                agent = Agent(...)
                db.add(agent)
                return agent  # Automatically commits
        ```
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # Find db session in arguments
            db = None
            
            # Check first positional argument (after self)
            if len(args) > 1 and isinstance(args[1], Session):
                db = args[1]
            # Check keyword arguments
            elif 'db' in kwargs and isinstance(kwargs['db'], Session):
                db = kwargs['db']
            
            if db is None:
                raise ValueError(
                    f"@transactional decorator requires a 'db' Session argument "
                    f"in function {func.__name__}"
                )
            
            try:
                result = func(*args, **kwargs)
                if auto_commit:
                    db.commit()
                    logger.debug(f"Transaction committed for {func.__name__}")
                return result
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    f"Transaction rolled back in {func.__name__} due to SQLAlchemy error: {e}",
                    exc_info=True
                )
                raise
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Transaction rolled back in {func.__name__} due to error: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class TransactionManager:
    """
    Transaction manager for complex multi-step operations.
    
    Provides explicit control over transaction boundaries and
    supports rollback handlers for cleanup operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize Transaction Manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self._rollback_handlers = []
        self._committed = False
    
    def add_rollback_handler(self, handler: Callable[[], None]) -> None:
        """
        Add a rollback handler to be called if transaction fails.
        
        Useful for cleaning up external resources (files, cache, etc.)
        when database transaction is rolled back.
        
        Args:
            handler: Callable to execute on rollback
            
        Example:
            ```python
            tm = TransactionManager(db)
            
            # Upload file
            file_path = upload_file(data)
            tm.add_rollback_handler(lambda: delete_file(file_path))
            
            # Create database record
            agent = Agent(...)
            db.add(agent)
            
            # If commit fails, file will be deleted automatically
            tm.commit()
            ```
        """
        self._rollback_handlers.append(handler)
    
    def commit(self) -> None:
        """
        Commit the transaction.
        
        Raises:
            SQLAlchemyError: If commit fails
        """
        try:
            self.db.commit()
            self._committed = True
            logger.debug("Transaction committed successfully")
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Transaction commit failed: {e}", exc_info=True)
            raise
        except Exception as e:
            self.rollback()
            logger.error(f"Transaction commit failed: {e}", exc_info=True)
            raise
    
    def rollback(self) -> None:
        """
        Rollback the transaction and execute rollback handlers.
        """
        if not self._committed:
            self.db.rollback()
            logger.debug("Transaction rolled back")
            
            # Execute rollback handlers
            for handler in self._rollback_handlers:
                try:
                    handler()
                    logger.debug(f"Executed rollback handler: {handler.__name__}")
                except Exception as e:
                    logger.error(
                        f"Rollback handler failed: {handler.__name__}: {e}",
                        exc_info=True
                    )
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback()
        elif not self._committed:
            # No exception but not committed, commit now
            try:
                self.commit()
            except Exception:
                # Commit failed, exception will propagate
                pass
        
        # Don't suppress exceptions
        return False


def retry_on_deadlock(max_retries: int = 3, backoff_factor: float = 0.5):
    """
    Decorator to retry database operations on deadlock.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor (seconds)
        
    Returns:
        Decorated function
        
    Example:
        ```python
        @retry_on_deadlock(max_retries=3)
        def update_agent(db: Session, agent_id: str, data: dict):
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            agent.name = data['name']
            db.commit()
        ```
    """
    import time
    from sqlalchemy.exc import OperationalError
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    # Check if it's a deadlock error
                    if "deadlock" in str(e).lower():
                        last_exception = e
                        if attempt < max_retries - 1:
                            sleep_time = backoff_factor * (2 ** attempt)
                            logger.warning(
                                f"Deadlock detected in {func.__name__}, "
                                f"retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(sleep_time)
                            continue
                    raise
            
            # All retries exhausted
            logger.error(f"All {max_retries} retries exhausted for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator
