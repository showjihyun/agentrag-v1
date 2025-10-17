"""
Share API

Provides endpoints for sharing conversations with other users.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import secrets

from backend.db.database import get_db
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


class SharedUser(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar: Optional[str] = None


@router.post("/{conversation_id}/share")
async def share_conversation(
    conversation_id: str, request: ShareRequest, db: Session = Depends(get_db)
):
    """
    Share conversation with another user.

    Roles:
    - viewer: Can view conversation and messages
    - editor: Can view and add messages
    - admin: Can manage sharing and permissions
    """
    try:
        # TODO: Implement actual database operations
        # For now, return mock data

        # Verify conversation ownership or admin rights
        # conversation = db.query(Conversation).filter(
        #     Conversation.id == conversation_id,
        #     Conversation.user_id == current_user.id
        # ).first()

        # if not conversation:
        #     raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if user exists
        # target_user = db.query(User).filter(User.email == request.email).first()
        # if not target_user:
        #     raise HTTPException(status_code=404, detail="User not found")

        # Create share record
        # share = ConversationShare(
        #     conversation_id=conversation_id,
        #     user_id=target_user.id,
        #     role=request.role,
        #     shared_by=current_user.id
        # )
        # db.add(share)
        # db.commit()

        return {
            "success": True,
            "user": {
                "id": "user_123",
                "email": request.email,
                "name": request.email.split("@")[0],
                "role": request.role,
                "avatar": None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to share conversation: {str(e)}"
        )


@router.delete("/{conversation_id}/share/{user_id}")
async def remove_share(
    conversation_id: str, user_id: str, db: Session = Depends(get_db)
):
    """Remove user's access to conversation."""
    try:
        # TODO: Implement actual database operations
        # Verify ownership or admin rights
        # Delete share record

        return {"success": True, "message": "User access removed"}

    except Exception as e:
        logger.error(f"Failed to remove share: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove share: {str(e)}")


@router.patch("/{conversation_id}/share/{user_id}")
async def update_share_role(
    conversation_id: str,
    user_id: str,
    request: ShareUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update user's role for conversation."""
    try:
        # TODO: Implement actual database operations
        # Verify ownership or admin rights
        # Update share record

        return {"success": True, "role": request.role}

    except Exception as e:
        logger.error(f"Failed to update share role: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update share role: {str(e)}"
        )


@router.post("/{conversation_id}/public")
async def toggle_public_link(
    conversation_id: str, request: PublicLinkRequest, db: Session = Depends(get_db)
):
    """Toggle public link for conversation."""
    try:
        # TODO: Implement actual database operations

        if request.isPublic:
            # Generate unique public link
            public_token = secrets.token_urlsafe(32)
            public_link = f"https://your-domain.com/shared/{public_token}"

            # Save to database
            # conversation.public_token = public_token
            # conversation.is_public = True
            # db.commit()

            return {"success": True, "isPublic": True, "publicLink": public_link}
        else:
            # Disable public link
            # conversation.public_token = None
            # conversation.is_public = False
            # db.commit()

            return {"success": True, "isPublic": False}

    except Exception as e:
        logger.error(f"Failed to toggle public link: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle public link: {str(e)}"
        )


@router.get("/{conversation_id}/shares")
async def get_conversation_shares(conversation_id: str, db: Session = Depends(get_db)):
    """Get list of users with access to conversation."""
    try:
        # TODO: Implement actual database operations

        return {
            "shares": [
                {
                    "id": "user_123",
                    "email": "user@example.com",
                    "name": "User Name",
                    "role": "viewer",
                    "avatar": None,
                    "sharedAt": datetime.utcnow().isoformat(),
                }
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get shares: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get shares: {str(e)}")
