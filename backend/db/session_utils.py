"""
Database Session Utilities

Provides helper functions for proper database session management
to prevent connection leaks.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session

from backend.db.database import get_db


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Ensures proper cleanup of database connections to prevent leaks.
    
    Usage:
        with get_db_session() as db:
            # Use db session
            user = db.query(User).first()
    
    This is equivalent to:
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Use db session
            user = db.query(User).first()
        finally:
            try:
                next(db_gen, None)
            except StopIteration:
                pass
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen, None)  # Trigger finally block in get_db()
        except StopIteration:
            pass


def execute_with_db_session(func, *args, **kwargs):
    """
    Execute a function with a database session.
    
    Args:
        func: Function that takes db as first argument
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments
    
    Returns:
        Result of the function
    
    Usage:
        def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
        
        user = execute_with_db_session(get_user, user_id=123)
    """
    with get_db_session() as db:
        return func(db, *args, **kwargs)
