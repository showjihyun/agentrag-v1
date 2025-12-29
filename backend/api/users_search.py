"""User search API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


# ============================================================================
# Response Models
# ============================================================================

class UserSearchResult(BaseModel):
    """User search result model."""
    id: str
    name: str
    email: str
    avatar: str = None


class UserSearchResponse(BaseModel):
    """User search response model."""
    users: List[UserSearchResult]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/search",
    response_model=UserSearchResponse,
    summary="Search users",
    description="Search for users by name or email for sharing and collaboration features.",
)
async def search_users(
    q: str = Query(..., min_length=2, description="Search query (name or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search for users by name or email.
    
    **Query Parameters:**
    - q: Search query (minimum 2 characters)
    - limit: Maximum number of results (default: 10, max: 50)
    
    **Returns:**
    - List of matching users
    
    **Errors:**
    - 400: Invalid search query
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Searching users with query: {q}")
        
        # Mock search results - this would be implemented with proper database search
        mock_users = [
            {
                "id": "user-1",
                "name": "김철수",
                "email": "kim.chulsoo@example.com",
                "avatar": None
            },
            {
                "id": "user-2", 
                "name": "이영희",
                "email": "lee.younghee@example.com",
                "avatar": None
            },
            {
                "id": "user-3",
                "name": "박민수",
                "email": "park.minsu@example.com", 
                "avatar": None
            }
        ]
        
        # Filter based on search query
        query_lower = q.lower()
        filtered_users = [
            user for user in mock_users
            if query_lower in user["name"].lower() or query_lower in user["email"].lower()
        ]
        
        # Limit results
        limited_users = filtered_users[:limit]
        
        return UserSearchResponse(users=limited_users)
        
    except Exception as e:
        logger.error(f"Failed to search users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )