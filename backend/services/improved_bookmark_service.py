"""Improved Bookmark Service with Python Best Practices.

This is an example of applying Python best practices to the bookmark service.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Protocol
from uuid import UUID
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.db.models.bookmark import Bookmark
from backend.core.enhanced_error_handler import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class BookmarkType(str, Enum):
    """Bookmark types with explicit enum."""
    CONVERSATION = "conversation"
    DOCUMENT = "document"


@dataclass
class BookmarkData:
    """Bookmark data transfer object."""
    user_id: UUID
    type: BookmarkType
    item_id: str
    title: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.title or len(self.title) > 500:
            raise ValueError("Title must be between 1 and 500 characters")
        if self.description and len(self.description) > 2000:
            raise ValueError("Description must be less than 2000 characters")
        if len(self.tags) > 10:
            raise ValueError("Maximum 10 tags allowed")


@dataclass
class BookmarkFilter:
    """Bookmark filter criteria."""
    user_id: UUID
    type: Optional[BookmarkType] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
    
    def __post_init__(self):
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


@dataclass
class BookmarkUpdate:
    """Bookmark update data."""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None


# ============================================================================
# Repository Interface (Dependency Inversion)
# ============================================================================

class IBookmarkRepository(Protocol):
    """Bookmark repository interface for dependency injection."""
    
    async def create(self, bookmark: Bookmark) -> Bookmark:
        """Create a new bookmark."""
        ...
    
    async def find_by_id(self, bookmark_id: UUID, user_id: UUID) -> Optional[Bookmark]:
        """Find bookmark by ID."""
        ...
    
    async def find_all(self, filter: BookmarkFilter) -> List[Bookmark]:
        """Find all bookmarks matching filter."""
        ...
    
    async def update(self, bookmark: Bookmark) -> Bookmark:
        """Update bookmark."""
        ...
    
    async def delete(self, bookmark: Bookmark) -> None:
        """Delete bookmark."""
        ...
    
    async def exists(self, user_id: UUID, type: BookmarkType, item_id: str) -> bool:
        """Check if bookmark exists."""
        ...


# ============================================================================
# Context Managers
# ============================================================================

@asynccontextmanager
async def db_transaction(db: Session):
    """Database transaction context manager with automatic commit/rollback."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# Improved Service
# ============================================================================

class ImprovedBookmarkService:
    """
    Improved bookmark service with Python best practices.
    
    Features:
    - Type safety with Enums and DataClasses
    - Dependency injection with Protocol
    - Context managers for resource management
    - Structured logging
    - Specific exception handling
    - Performance optimization
    """
    
    def __init__(
        self,
        db: Session,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize service.
        
        Args:
            db: Database session
            logger: Optional logger instance
        """
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
    
    async def create_bookmark(self, data: BookmarkData) -> Bookmark:
        """
        Create a new bookmark with improved error handling.
        
        Args:
            data: Bookmark data
            
        Returns:
            Created bookmark
            
        Raises:
            ValidationError: If bookmark already exists or data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Check if bookmark already exists
            existing = await self._check_existing(
                data.user_id,
                data.type,
                data.item_id
            )
            
            if existing:
                self.logger.info(
                    "Bookmark already exists",
                    extra={
                        "user_id": str(data.user_id),
                        "item_id": data.item_id,
                        "action": "create_bookmark"
                    }
                )
                return existing
            
            # Create bookmark
            async with db_transaction(self.db):
                bookmark = Bookmark(
                    user_id=data.user_id,
                    type=data.type.value,
                    item_id=data.item_id,
                    title=data.title,
                    description=data.description,
                    tags=data.tags
                )
                
                self.db.add(bookmark)
                self.db.flush()  # Get ID before commit
                self.db.refresh(bookmark)
                
                self.logger.info(
                    "Bookmark created successfully",
                    extra={
                        "bookmark_id": str(bookmark.id),
                        "user_id": str(data.user_id),
                        "type": data.type.value,
                        "action": "create_bookmark"
                    }
                )
                
                return bookmark
        
        except IntegrityError as e:
            self.logger.warning(
                "Duplicate bookmark detected",
                extra={
                    "user_id": str(data.user_id),
                    "item_id": data.item_id,
                    "error": str(e)
                }
            )
            raise ValidationError(
                message="Bookmark already exists",
                field="item_id",
                details={"user_id": str(data.user_id), "item_id": data.item_id}
            )
        
        except OperationalError as e:
            self.logger.error(
                "Database connection error",
                extra={
                    "error": str(e),
                    "action": "create_bookmark"
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "create_bookmark"},
                original_error=e
            )
        
        except Exception as e:
            self.logger.error(
                "Unexpected error creating bookmark",
                extra={
                    "user_id": str(data.user_id),
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to create bookmark",
                details={"user_id": str(data.user_id)},
                original_error=e
            )
    
    async def get_bookmarks(self, filter: BookmarkFilter) -> List[Bookmark]:
        """
        Get bookmarks with optimized query (no N+1 problem).
        
        Args:
            filter: Filter criteria
            
        Returns:
            List of bookmarks
        """
        try:
            # Build query with eager loading
            query = (
                self.db.query(Bookmark)
                .options(joinedload(Bookmark.user))  # Prevent N+1
                .filter(Bookmark.user_id == filter.user_id)
            )
            
            # Apply filters
            if filter.type:
                query = query.filter(Bookmark.type == filter.type.value)
            
            if filter.is_favorite is not None:
                query = query.filter(Bookmark.is_favorite == filter.is_favorite)
            
            if filter.tags:
                query = query.filter(Bookmark.tags.overlap(filter.tags))
            
            # Order and paginate
            bookmarks = (
                query
                .order_by(Bookmark.created_at.desc())
                .limit(filter.limit)
                .offset(filter.offset)
                .all()
            )
            
            self.logger.debug(
                "Retrieved bookmarks",
                extra={
                    "user_id": str(filter.user_id),
                    "count": len(bookmarks),
                    "filter_type": filter.type.value if filter.type else None
                }
            )
            
            return bookmarks
        
        except Exception as e:
            self.logger.error(
                "Failed to retrieve bookmarks",
                extra={
                    "user_id": str(filter.user_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to retrieve bookmarks",
                details={"user_id": str(filter.user_id)},
                original_error=e
            )
    
    async def update_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        update: BookmarkUpdate
    ) -> Optional[Bookmark]:
        """
        Update bookmark with validation.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            update: Update data
            
        Returns:
            Updated bookmark or None if not found
        """
        try:
            bookmark = await self._get_bookmark(bookmark_id, user_id)
            
            if not bookmark:
                return None
            
            async with db_transaction(self.db):
                # Update fields
                if update.title is not None:
                    bookmark.title = update.title
                if update.description is not None:
                    bookmark.description = update.description
                if update.tags is not None:
                    bookmark.tags = update.tags
                if update.is_favorite is not None:
                    bookmark.is_favorite = update.is_favorite
                
                bookmark.updated_at = datetime.utcnow()
                
                self.db.flush()
                self.db.refresh(bookmark)
                
                self.logger.info(
                    "Bookmark updated",
                    extra={
                        "bookmark_id": str(bookmark_id),
                        "user_id": str(user_id)
                    }
                )
                
                return bookmark
        
        except Exception as e:
            self.logger.error(
                "Failed to update bookmark",
                extra={
                    "bookmark_id": str(bookmark_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to update bookmark",
                details={"bookmark_id": str(bookmark_id)},
                original_error=e
            )
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    async def _check_existing(
        self,
        user_id: UUID,
        type: BookmarkType,
        item_id: str
    ) -> Optional[Bookmark]:
        """Check if bookmark already exists."""
        return (
            self.db.query(Bookmark)
            .filter(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.type == type.value,
                    Bookmark.item_id == item_id
                )
            )
            .first()
        )
    
    async def _get_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID
    ) -> Optional[Bookmark]:
        """Get bookmark by ID with authorization check."""
        return (
            self.db.query(Bookmark)
            .filter(
                and_(
                    Bookmark.id == bookmark_id,
                    Bookmark.user_id == user_id
                )
            )
            .first()
        )


# ============================================================================
# Factory Function
# ============================================================================

def get_improved_bookmark_service(
    db: Session,
    logger: Optional[logging.Logger] = None
) -> ImprovedBookmarkService:
    """
    Factory function for creating bookmark service.
    
    Args:
        db: Database session
        logger: Optional logger
        
    Returns:
        Bookmark service instance
    """
    return ImprovedBookmarkService(db, logger)
