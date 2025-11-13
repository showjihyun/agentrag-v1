"""API endpoints for managing user API keys."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.api_key_service import APIKeyService
from backend.models.agent_builder import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyListResponse,
    APIKeyTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/api-keys",
    tags=["agent-builder-api-keys"],
)


@router.post(
    "",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update API key",
    description="Create a new API key or update existing one for a service.",
)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update an API key."""
    try:
        logger.info(f"Creating/updating API key for user {current_user.id}, service {api_key_data.service_name}")
        
        service = APIKeyService(db)
        api_key = service.create_api_key(
            user_id=str(current_user.id),
            api_key_data=api_key_data
        )
        
        return APIKeyResponse(
            id=str(api_key.id),
            service_name=api_key.service_name,
            service_display_name=api_key.service_display_name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count,
        )
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get(
    "",
    response_model=APIKeyListResponse,
    summary="List API keys",
    description="List all API keys for the current user.",
)
async def list_api_keys(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all API keys."""
    try:
        logger.info(f"Listing API keys for user {current_user.id}")
        
        service = APIKeyService(db)
        api_keys = service.list_api_keys(
            user_id=str(current_user.id),
            include_inactive=include_inactive
        )
        
        api_key_responses = [
            APIKeyResponse(
                id=str(key.id),
                service_name=key.service_name,
                service_display_name=key.service_display_name,
                description=key.description,
                is_active=key.is_active,
                created_at=key.created_at,
                updated_at=key.updated_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
            )
            for key in api_keys
        ]
        
        return APIKeyListResponse(
            api_keys=api_key_responses,
            total=len(api_key_responses)
        )
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.get(
    "/{api_key_id}",
    response_model=APIKeyResponse,
    summary="Get API key",
    description="Get a specific API key by ID.",
)
async def get_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get an API key by ID."""
    try:
        service = APIKeyService(db)
        api_key = service.get_api_key(
            user_id=str(current_user.id),
            api_key_id=api_key_id
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {api_key_id} not found"
            )
        
        return APIKeyResponse(
            id=str(api_key.id),
            service_name=api_key.service_name,
            service_display_name=api_key.service_display_name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key"
        )


@router.put(
    "/{api_key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="Update an existing API key.",
)
async def update_api_key(
    api_key_id: str,
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an API key."""
    try:
        service = APIKeyService(db)
        api_key = service.update_api_key(
            user_id=str(current_user.id),
            api_key_id=api_key_id,
            api_key_data=api_key_data
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {api_key_id} not found"
            )
        
        return APIKeyResponse(
            id=str(api_key.id),
            service_name=api_key.service_name,
            service_display_name=api_key.service_display_name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
        )


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
    description="Delete an API key.",
)
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an API key."""
    try:
        service = APIKeyService(db)
        deleted = service.delete_api_key(
            user_id=str(current_user.id),
            api_key_id=api_key_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {api_key_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.post(
    "/test/{service_name}",
    response_model=APIKeyTestResponse,
    summary="Test API key",
    description="Test if an API key is valid and working.",
)
async def test_api_key(
    service_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test an API key."""
    try:
        service = APIKeyService(db)
        result = service.test_api_key(
            user_id=str(current_user.id),
            service_name=service_name
        )
        
        return APIKeyTestResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to test API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test API key"
        )
