"""Database base class for all models.

This module provides a centralized Base class for SQLAlchemy models.
All models should import Base from this module for consistency.
"""

from backend.db.database import Base

__all__ = ["Base"]
