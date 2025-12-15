"""
API Key Management Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.core.security.api_key_manager import get_api_key_manager
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/security/api-keys", tags=["security-api-keys"])


# Request/Response Models
class CreateAPIKeyRequest(BaseModel):
    """Request to create new API key"""
    name: str = Field(..., min_length=3, max_length=255, description="Key name/description")
    expires_in_days: int = Field(90, ge=1, le=365, description="Days until expiration")
    scopes: Optional[List[str]] = Field(default=None, description="List of allowed scopes")


class APIKeyResponse(BaseModel):
    """API key response (without raw key)"""
    id: str
    name: str
    prefix: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    usage_count: int
    is_active: bool
    scopes: List[str]
    created_at: str


class CreateAPIKeyResponse(BaseModel):
    """Response when creating new API key (includes raw key once!)"""
    id: str
    key: str  # ⚠️ Only shown once!
    name: str
    prefix: str
    expires_at: Optional[str]
    scopes: List[str]
    created_at: str
    warning: str = "⚠️ Save this key now! It won't be shown again."


class RotateAPIKeyResponse(BaseModel):
    """Response when rotating API key"""
    old_key_id: str
    new_key: CreateAPIKeyResponse


# Endpoints
@router.post("/", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new API key for current user
    
    **⚠️ Important**: The raw API key is only shown once! Save it securely.
    """
    try:
        manager = get_api_key_manager()
        
        key_info = await manager.create_key(
            db=db,
            user_id=current_user.id,
            name=request.name,
            expires_in_days=request.expires_in_days,
            scopes=request.scopes
        )
        
        logger.info(
            "api_key_created",
            user_id=str(current_user.id),
            key_id=key_info["id"],
            name=request.name
        )
        
        return CreateAPIKeyResponse(**key_info)
        
    except Exception as e:
        logger.error(
            "api_key_creation_failed",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for current user
    
    Args:
        include_inactive: Include revoked/expired keys
    """
    try:
        manager = get_api_key_manager()
        
        keys = await manager.list_keys(
            db=db,
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        return [APIKeyResponse(**key) for key in keys]
        
    except Exception as e:
        logger.error(
            "api_key_list_failed",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.post("/{key_id}/rotate", response_model=CreateAPIKeyResponse)
async def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rotate API key (create new, mark old as rotated)
    
    **⚠️ Important**: The new API key is only shown once! Save it securely.
    """
    try:
        manager = get_api_key_manager()
        
        new_key_info = await manager.rotate_key(
            db=db,
            key_id=key_id,
            user_id=current_user.id
        )
        
        logger.info(
            "api_key_rotated",
            user_id=str(current_user.id),
            old_key_id=key_id,
            new_key_id=new_key_info["id"]
        )
        
        return CreateAPIKeyResponse(**new_key_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "api_key_rotation_failed",
            user_id=str(current_user.id),
            key_id=key_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate API key: {str(e)}"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke API key (mark as inactive)
    """
    try:
        manager = get_api_key_manager()
        
        success = await manager.revoke_key(
            db=db,
            key_id=key_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        logger.info(
            "api_key_revoked",
            user_id=str(current_user.id),
            key_id=key_id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "api_key_revocation_failed",
            user_id=str(current_user.id),
            key_id=key_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get("/expiring", response_model=List[dict])
async def get_expiring_keys(
    days_threshold: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get API keys expiring soon
    
    Args:
        days_threshold: Days before expiration to alert (default: 7)
    """
    try:
        manager = get_api_key_manager()
        
        expiring_keys = await manager.check_expiring_keys(
            db=db,
            days_threshold=days_threshold
        )
        
        # Filter to current user's keys only
        user_keys = [
            key for key in expiring_keys
            if key["user_id"] == current_user.id
        ]
        
        return user_keys
        
    except Exception as e:
        logger.error(
            "expiring_keys_check_failed",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check expiring keys: {str(e)}"
        )
