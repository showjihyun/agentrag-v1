"""Enhanced Bookmark Service with DTOs and Context Managers."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.db.models.bookmark import Bookmark
from backend.models.enums import BookmarkType
from backend.models.dto import (
    BookmarkCreateDTO,
    BookmarkFilterDTO,
    BookmarkUpdateDTO
)
from backend.core.context_managers import db_transaction, timer
from backend.core.enhanced_error_handler import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class EnhancedBookmarkService:
    """
    Enhanced bookmark service with DTOs and context managers.
    
    Features:
    - Type-safe DTOs
    - Automatic transaction management
    - Performance timing
    - Structured logging
    """
    
    def __init__(self, db: Session):
        """
        Initialize service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.logger = logger
    
    async def create_bookmark(self, data: BookmarkCreateDTO) -> Bookmark:
        """
        Create a new bookmark with DTO and context manager.
        
        Args:
            data: Bookmark creation data
            
        Returns:
            Created bookmark
            
        Raises:
            ValidationError: If bookmark already exists
            DatabaseError: If database operation fails
        """
        with timer("create_bookmark", self.logger):
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
                            "type": data.type.value
                        }
                    )
                    return existing
                
                # Create bookmark with automatic transaction management
                async with db_transaction(self.db, logger_instance=self.logger):
                    bookmark = Bookmark(
                        user_id=data.user_id,
                        type=data.type.value,
                        item_id=data.item_id,
                        title=data.title,
                        description=data.description,
                        tags=data.tags
                    )
                    
                    self.db.add(bookmark)
                    self.db.flush()
                    self.db.refresh(bookmark)
                    
                    self.logger.info(
                        "Bookmark created",
                        extra={
                            "bookmark_id": str(bookmark.id),
                            "user_id": str(data.user_id),
                            "type": data.type.value
                        }
                    )
                    
                    return bookmark
            
            except IntegrityError as e:
                self.logger.warning(
                    "Duplicate bookmark",
                    extra={"user_id": str(data.user_id), "item_id": data.item_id}
                )
                raise ValidationError(
                    message="Bookmark already exists",
                    field="item_id",
                    details={"user_id": str(data.user_id), "item_id": data.item_id}
                )
            
            except OperationalError as e:
                self.logger.error(
                    "Database connection error",
                    extra={"error": str(e)},
                    exc_info=True
                )
                raise DatabaseError(
                    message="Database unavailable",
                    details={"operation": "create_bookmark"},
                    original_error=e
                )
            
            except Exception as e:
                self.logger.error(
                    "Failed to create bookmark",
                    extra={
                        "user_id": str(data.user_id),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise DatabaseError(
                    message="Failed to create bookmark",
                    details={"user_id": str(data.user_id)},
                    original_error=e
                )
    
    async def get_bookmarks(self, filter: BookmarkFilterDTO) -> List[Bookmark]:
        """
        Get bookmarks with DTO filter and performance timing.
        
        Args:
            filter: Filter criteria
            
        Returns:
            List of bookmarks
        """
        with timer("get_bookmarks", self.logger):
            try:
                # Build query with eager loading (prevent N+1)
                query = (
                    self.db.query(Bookmark)
                    .options(joinedload(Bookmark.user))
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
        update: BookmarkUpdateDTO
    ) -> Optional[Bookmark]:
        """
        Update bookmark with DTO and context manager.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            update: Update data
            
        Returns:
            Updated bookmark or None if not found
        """
        with timer("update_bookmark", self.logger):
            try:
                bookmark = await self._get_bookmark(bookmark_id, user_id)
                
                if not bookmark:
                    return None
                
                async with db_transaction(self.db, logger_instance=self.logger):
                    # Update fields
                    if update.title is not None:
                        bookmark.title = update.title
                    if update.description is not None:
                        bookmark.description = update.description
                    if update.tags is not None:
                        bookmark.tags = update.tags
                    if update.is_favorite is not None:
                        bookmark.is_favorite = update.is_favorite
                    
                    from datetime import datetime
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
    
    async def delete_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete bookmark with context manager.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        with timer("delete_bookmark", self.logger):
            try:
                bookmark = await self._get_bookmark(bookmark_id, user_id)
                
                if not bookmark:
                    return False
                
                async with db_transaction(self.db, logger_instance=self.logger):
                    self.db.delete(bookmark)
                    
                    self.logger.info(
                        "Bookmark deleted",
                        extra={
                            "bookmark_id": str(bookmark_id),
                            "user_id": str(user_id)
                        }
                    )
                    
                    return True
            
            except Exception as e:
                self.logger.error(
                    "Failed to delete bookmark",
                    extra={
                        "bookmark_id": str(bookmark_id),
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise DatabaseError(
                    message="Failed to delete bookmark",
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


def get_enhanced_bookmark_service(db: Session) -> EnhancedBookmarkService:
    """Factory function for creating enhanced bookmark service."""
    return EnhancedBookmarkService(db)
