"""
Share API

Provides endpoints for sharing conversations with other users.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.conversation_share import ShareRole
from backend.db.repositories.user_repository import UserRepository
from backend.core.auth_dependencies import get_current_user
from backend.services.share_service import get_share_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["Share"])


class ShareRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"  # viewer, editor, admin


class ShareUpdateRequest(BaseModel):
    role: str


class PublicLinkRequest(BaseModel):
    isPublic: bool


class SharedUserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar: Optional[str] = None
    sharedAt: Optional[str] = None


@router.post("/{conversation_id}/share")
async def share_conversation(
    conversation_id: str,
    request: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share conversation with another user.

    Roles:
    - viewer: Can view conversation and messages
    - editor: Can view and add messages
    - admin: Can manage sharing and permissions
    """
    try:
        # Find target user by email
        user_repo = UserRepository(db)
        target_user = user_repo.get_user_by_email(request.email)
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Cannot share with yourself
        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot share with yourself")
        
        # Map role string to enum
        role_map = {
            "viewer": ShareRole.VIEWER,
            "editor": ShareRole.EDITOR,
            "admin": ShareRole.ADMIN,
        }
        role = role_map.get(request.role.lower(), ShareRole.VIEWER)
        
        # Share conversation
        share_service = get_share_service(db)
        share = await share_service.share_conversation(
            conversation_id=UUID(conversation_id),
            owner_id=current_user.id,
            target_user_id=target_user.id,
            role=role
        )
        
        logger.info(f"User {current_user.email} shared conversation {conversation_id} with {request.email}")

        return {
            "success": True,
            "user": {
                "id": str(target_user.id),
                "email": target_user.email,
                "name": target_user.username or target_user.email.split("@")[0],
                "role": request.role,
                "avatar": None,
                "sharedAt": share.created_at.isoformat() if share.created_at else datetime.utcnow().isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to share conversation: {str(e)}"
        )


@router.delete("/{conversation_id}/share/{user_id}")
async def remove_share(
    conversation_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove user's access to conversation."""
    try:
        share_service = get_share_service(db)
        success = await share_service.unshare_conversation(
            conversation_id=UUID(conversation_id),
            owner_id=current_user.id,
            target_user_id=UUID(user_id)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Share not found")
        
        logger.info(f"User {current_user.email} removed share for user {user_id} from conversation {conversation_id}")

        return {"success": True, "message": "User access removed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove share: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove share: {str(e)}")


@router.patch("/{conversation_id}/share/{user_id}")
async def update_share_role(
    conversation_id: str,
    user_id: str,
    request: ShareUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's role for conversation."""
    try:
        # Map role string to enum
        role_map = {
            "viewer": ShareRole.VIEWER,
            "editor": ShareRole.EDITOR,
            "admin": ShareRole.ADMIN,
        }
        role = role_map.get(request.role.lower())
        
        if not role:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        share_service = get_share_service(db)
        share = await share_service.update_share_role(
            conversation_id=UUID(conversation_id),
            owner_id=current_user.id,
            target_user_id=UUID(user_id),
            role=role
        )
        
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        
        logger.info(f"User {current_user.email} updated share role for user {user_id} to {request.role}")

        return {"success": True, "role": request.role}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update share role: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to update share role: {str(e)}"
        )


@router.post("/{conversation_id}/public")
async def toggle_public_link(
    conversation_id: str,
    request: PublicLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle public link for conversation."""
    try:
        share_service = get_share_service(db)
        result = await share_service.toggle_public_link(
            conversation_id=UUID(conversation_id),
            owner_id=current_user.id,
            is_public=request.isPublic
        )
        
        logger.info(f"User {current_user.email} toggled public link for conversation {conversation_id}: {request.isPublic}")

        return {
            "success": True,
            "isPublic": result["isPublic"],
            "publicLink": result.get("publicUrl"),
        }

    except Exception as e:
        logger.error(f"Failed to toggle public link: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle public link: {str(e)}"
        )


@router.get("/{conversation_id}/shares")
async def get_conversation_shares(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users with access to conversation."""
    try:
        share_service = get_share_service(db)
        shares = await share_service.get_shared_users(
            conversation_id=UUID(conversation_id),
            owner_id=current_user.id
        )
        
        # Get user details for each share
        user_repo = UserRepository(db)
        share_list = []
        
        for share in shares:
            user = user_repo.get_user_by_id(share.user_id)
            if user:
                share_list.append({
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.username or user.email.split("@")[0],
                    "role": share.role.value if hasattr(share.role, 'value') else share.role,
                    "avatar": None,
                    "sharedAt": share.created_at.isoformat() if share.created_at else None,
                })

        return {"shares": share_list}

    except Exception as e:
        logger.error(f"Failed to get shares: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get shares: {str(e)}")
