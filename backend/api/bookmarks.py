"""
Bookmarks API

Provides endpoints for managing bookmarks and favorites.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from backend.db.database import get_db
from sqlalchemy.orm import Session
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.bookmark_service import get_bookmark_service
from backend.models.enums import BookmarkType
from backend.core.enhanced_error_handler import handle_error, ValidationError, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bookmarks", tags=["Bookmarks"])


class BookmarkCreate(BaseModel):
    type: BookmarkType = Field(..., description="Bookmark type: conversation or document")
    itemId: str = Field(..., description="ID of the bookmarked item")
    title: str = Field(..., min_length=1, max_length=500, description="Bookmark title")
    description: Optional[str] = Field(None, max_length=2000, description="Optional description")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    
    class Config:
        use_enum_values = True


class BookmarkUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None


class FavoriteUpdate(BaseModel):
    isFavorite: bool = Field(..., description="Favorite status")


class BookmarkResponse(BaseModel):
    id: str
    type: str
    itemId: str
    title: str
    description: Optional[str]
    tags: List[str]
    isFavorite: bool
    createdAt: str
    updatedAt: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=dict)
async def get_bookmarks(
    type: Optional[BookmarkType] = Query(None, description="Filter by type: conversation or document"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all bookmarks for current user with optional filters."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        # Parse tags
        tag_list = tags.split(",") if tags else None
        
        # Get bookmarks
        bookmarks = await bookmark_service.get_bookmarks(
            user_id=current_user.id,
            type=type,
            is_favorite=is_favorite,
            tags=tag_list,
            limit=limit,
            offset=offset
        )
        
        # Format response
        bookmark_list = [
            {
                "id": str(b.id),
                "type": b.type,
                "itemId": b.item_id,
                "title": b.title,
                "description": b.description,
                "tags": b.tags,
                "isFavorite": b.is_favorite,
                "createdAt": b.created_at.isoformat(),
                "updatedAt": b.updated_at.isoformat(),
            }
            for b in bookmarks
        ]
        
        return {
            "bookmarks": bookmark_list,
            "total": len(bookmark_list),
            "limit": limit,
            "offset": offset
        }

    except DatabaseError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=app_error.message
        )
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get bookmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bookmarks"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bookmark."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        new_bookmark = await bookmark_service.create_bookmark(
            user_id=current_user.id,
            type=bookmark.type,
            item_id=bookmark.itemId,
            title=bookmark.title,
            description=bookmark.description,
            tags=bookmark.tags
        )
        
        return {
            "success": True,
            "bookmark": {
                "id": str(new_bookmark.id),
                "type": new_bookmark.type,
                "itemId": new_bookmark.item_id,
                "title": new_bookmark.title,
                "description": new_bookmark.description,
                "tags": new_bookmark.tags,
                "isFavorite": new_bookmark.is_favorite,
                "createdAt": new_bookmark.created_at.isoformat(),
                "updatedAt": new_bookmark.updated_at.isoformat(),
            }
        }

    except ValidationError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=app_error.message
        )
    except DatabaseError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=app_error.message
        )
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to create bookmark: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bookmark"
        )


@router.get("/{bookmark_id}")
async def get_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bookmark."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        bookmark = await bookmark_service.get_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.id
        )
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        return {
            "id": str(bookmark.id),
            "type": bookmark.type,
            "itemId": bookmark.item_id,
            "title": bookmark.title,
            "description": bookmark.description,
            "tags": bookmark.tags,
            "isFavorite": bookmark.is_favorite,
            "createdAt": bookmark.created_at.isoformat(),
            "updatedAt": bookmark.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get bookmark: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bookmark"
        )


@router.patch("/{bookmark_id}")
async def update_bookmark(
    bookmark_id: UUID,
    update: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a bookmark."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        updated_bookmark = await bookmark_service.update_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.id,
            title=update.title,
            description=update.description,
            tags=update.tags
        )
        
        if not updated_bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        return {
            "success": True,
            "bookmark": {
                "id": str(updated_bookmark.id),
                "type": updated_bookmark.type,
                "itemId": updated_bookmark.item_id,
                "title": updated_bookmark.title,
                "description": updated_bookmark.description,
                "tags": updated_bookmark.tags,
                "isFavorite": updated_bookmark.is_favorite,
                "createdAt": updated_bookmark.created_at.isoformat(),
                "updatedAt": updated_bookmark.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to update bookmark: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bookmark"
        )


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bookmark."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        deleted = await bookmark_service.delete_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        return None

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to delete bookmark: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bookmark"
        )


@router.patch("/{bookmark_id}/favorite")
async def toggle_favorite(
    bookmark_id: UUID,
    update: FavoriteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a bookmark."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        updated_bookmark = await bookmark_service.toggle_favorite(
            bookmark_id=bookmark_id,
            user_id=current_user.id,
            is_favorite=update.isFavorite
        )
        
        if not updated_bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        return {
            "success": True,
            "isFavorite": updated_bookmark.is_favorite
        }

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to toggle favorite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle favorite"
        )


@router.get("/tags/all")
async def get_all_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique tags used in bookmarks."""
    try:
        bookmark_service = get_bookmark_service(db)
        
        tags = await bookmark_service.get_all_tags(user_id=current_user.id)
        
        return {"tags": tags}

    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tags"
        )
