"""Bookmark service for managing user bookmarks."""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.db.models.bookmark import Bookmark
from backend.models.enums import BookmarkType
from backend.core.enhanced_error_handler import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class BookmarkService:
    """Service for managing bookmarks."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_bookmark(
        self,
        user_id: UUID,
        type: BookmarkType,
        item_id: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Bookmark:
        """
        Create a new bookmark.
        
        Args:
            user_id: User ID
            type: Bookmark type enum
            item_id: ID of the bookmarked item
            title: Bookmark title
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            Created bookmark
        """
        try:
            
            # Check if bookmark already exists
            existing = self.db.query(Bookmark).filter(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.type == type.value,
                    Bookmark.item_id == item_id
                )
            ).first()
            
            if existing:
                logger.info(
                    "Bookmark already exists",
                    extra={
                        "user_id": str(user_id),
                        "item_id": item_id,
                        "type": type.value
                    }
                )
                return existing
            
            # Create bookmark
            bookmark = Bookmark(
                user_id=user_id,
                type=type.value,
                item_id=item_id,
                title=title,
                description=description,
                tags=tags or []
            )
            
            self.db.add(bookmark)
            self.db.commit()
            self.db.refresh(bookmark)
            
            logger.info(
                "Created bookmark",
                extra={
                    "bookmark_id": str(bookmark.id),
                    "user_id": str(user_id),
                    "type": type.value
                }
            )
            return bookmark
            
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(
                "Duplicate bookmark",
                extra={"user_id": str(user_id), "item_id": item_id}
            )
            raise ValidationError(
                message="Bookmark already exists",
                field="item_id",
                details={"user_id": str(user_id), "item_id": item_id}
            )
        except OperationalError as e:
            self.db.rollback()
            logger.error(
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
            self.db.rollback()
            logger.error(
                "Failed to create bookmark",
                extra={
                    "user_id": str(user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to create bookmark",
                details={"user_id": str(user_id), "type": type.value, "item_id": item_id},
                original_error=e
            )
    
    async def get_bookmarks(
        self,
        user_id: UUID,
        type: Optional[BookmarkType] = None,
        is_favorite: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Bookmark]:
        """
        Get user's bookmarks with optional filters (optimized with joinedload).
        
        Args:
            user_id: User ID
            type: Optional type filter
            is_favorite: Optional favorite filter
            tags: Optional tags filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of bookmarks
        """
        try:
            # Use joinedload to prevent N+1 queries
            query = (
                self.db.query(Bookmark)
                .options(joinedload(Bookmark.user))
                .filter(Bookmark.user_id == user_id)
            )
            
            # Apply filters
            if type:
                query = query.filter(Bookmark.type == type.value)
            
            if is_favorite is not None:
                query = query.filter(Bookmark.is_favorite == is_favorite)
            
            if tags:
                # Filter by tags (any match)
                query = query.filter(Bookmark.tags.overlap(tags))
            
            # Order by created_at descending
            query = query.order_by(Bookmark.created_at.desc())
            
            # Apply pagination
            bookmarks = query.limit(limit).offset(offset).all()
            
            logger.debug(f"Retrieved {len(bookmarks)} bookmarks for user {user_id}")
            return bookmarks
            
        except Exception as e:
            logger.error(f"Failed to get bookmarks: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to retrieve bookmarks",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def get_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID
    ) -> Optional[Bookmark]:
        """
        Get a specific bookmark.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            
        Returns:
            Bookmark or None
        """
        try:
            bookmark = self.db.query(Bookmark).filter(
                and_(
                    Bookmark.id == bookmark_id,
                    Bookmark.user_id == user_id
                )
            ).first()
            
            return bookmark
            
        except Exception as e:
            logger.error(f"Failed to get bookmark: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to retrieve bookmark",
                details={"bookmark_id": str(bookmark_id)},
                original_error=e
            )
    
    async def update_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Bookmark]:
        """
        Update a bookmark.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            title: Optional new title
            description: Optional new description
            tags: Optional new tags
            
        Returns:
            Updated bookmark or None
        """
        try:
            bookmark = await self.get_bookmark(bookmark_id, user_id)
            
            if not bookmark:
                return None
            
            # Update fields
            if title is not None:
                bookmark.title = title
            if description is not None:
                bookmark.description = description
            if tags is not None:
                bookmark.tags = tags
            
            bookmark.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bookmark)
            
            logger.info(f"Updated bookmark {bookmark_id}")
            return bookmark
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update bookmark: {e}", exc_info=True)
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
        Delete a bookmark.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        try:
            bookmark = await self.get_bookmark(bookmark_id, user_id)
            
            if not bookmark:
                return False
            
            self.db.delete(bookmark)
            self.db.commit()
            
            logger.info(f"Deleted bookmark {bookmark_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete bookmark: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to delete bookmark",
                details={"bookmark_id": str(bookmark_id)},
                original_error=e
            )
    
    async def toggle_favorite(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        is_favorite: bool
    ) -> Optional[Bookmark]:
        """
        Toggle favorite status of a bookmark.
        
        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            is_favorite: New favorite status
            
        Returns:
            Updated bookmark or None
        """
        try:
            bookmark = await self.get_bookmark(bookmark_id, user_id)
            
            if not bookmark:
                return None
            
            bookmark.is_favorite = is_favorite
            bookmark.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bookmark)
            
            logger.info(f"Toggled favorite for bookmark {bookmark_id}: {is_favorite}")
            return bookmark
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to toggle favorite: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to toggle favorite",
                details={"bookmark_id": str(bookmark_id)},
                original_error=e
            )
    
    async def get_all_tags(
        self,
        user_id: UUID
    ) -> List[str]:
        """
        Get all unique tags used by user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of unique tags
        """
        try:
            bookmarks = self.db.query(Bookmark).filter(
                Bookmark.user_id == user_id
            ).all()
            
            # Collect all tags
            all_tags = set()
            for bookmark in bookmarks:
                if bookmark.tags:
                    all_tags.update(bookmark.tags)
            
            return sorted(list(all_tags))
            
        except Exception as e:
            logger.error(f"Failed to get tags: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to retrieve tags",
                details={"user_id": str(user_id)},
                original_error=e
            )


def get_bookmark_service(db: Session) -> BookmarkService:
    """Get bookmark service instance."""
    return BookmarkService(db)
