"""Share service for managing conversation sharing."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import secrets

from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.db.models.conversation_share import ConversationShare, ShareRole
from backend.models.enums import ShareRole as ShareRoleEnum
from backend.core.context_managers import db_transaction
from backend.core.enhanced_error_handler import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class ShareService:
    """Service for managing conversation sharing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def share_conversation(
        self,
        conversation_id: UUID,
        owner_id: UUID,
        target_user_id: UUID,
        role: ShareRole = ShareRole.VIEWER
    ) -> ConversationShare:
        """
        Share conversation with another user.
        
        Args:
            conversation_id: Conversation ID
            owner_id: Owner user ID
            target_user_id: Target user ID
            role: Share role
            
        Returns:
            Created share
        """
        try:
            # Check if already shared
            existing = self.db.query(ConversationShare).filter(
                and_(
                    ConversationShare.conversation_id == conversation_id,
                    ConversationShare.user_id == target_user_id
                )
            ).first()
            
            if existing:
                # Update role with context manager
                async with db_transaction(self.db):
                    existing.role = role
                    existing.updated_at = datetime.utcnow()
                    self.db.flush()
                    self.db.refresh(existing)
                    
                    logger.info(
                        "Updated share role",
                        extra={
                            "conversation_id": str(conversation_id),
                            "target_user_id": str(target_user_id),
                            "role": role.value
                        }
                    )
                    return existing
            
            # Create new share with context manager
            async with db_transaction(self.db):
                share = ConversationShare(
                    conversation_id=conversation_id,
                    user_id=target_user_id,
                    role=role,
                    shared_by=owner_id
                )
                
                self.db.add(share)
                self.db.flush()
                self.db.refresh(share)
                
                logger.info(
                    "Conversation shared",
                    extra={
                        "conversation_id": str(conversation_id),
                        "target_user_id": str(target_user_id),
                        "role": role.value
                    }
                )
                return share
        
        except IntegrityError as e:
            logger.warning(
                "Duplicate share or invalid reference",
                extra={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id)
                }
            )
            raise ValidationError(
                message="Share already exists or invalid user/conversation",
                details={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id)
                }
            )
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "share_conversation"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to share conversation",
                extra={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to share conversation",
                details={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id)
                },
                original_error=e
            )
    
    async def unshare_conversation(
        self,
        conversation_id: UUID,
        owner_id: UUID,
        target_user_id: UUID
    ) -> bool:
        """
        Remove user's access to conversation.
        
        Args:
            conversation_id: Conversation ID
            owner_id: Owner user ID
            target_user_id: Target user ID
            
        Returns:
            True if removed, False if not found
        """
        try:
            share = self.db.query(ConversationShare).filter(
                and_(
                    ConversationShare.conversation_id == conversation_id,
                    ConversationShare.user_id == target_user_id
                )
            ).first()
            
            if not share:
                return False
            
            async with db_transaction(self.db):
                self.db.delete(share)
                
                logger.info(
                    "Conversation unshared",
                    extra={
                        "conversation_id": str(conversation_id),
                        "target_user_id": str(target_user_id)
                    }
                )
                return True
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "unshare_conversation"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to unshare conversation",
                extra={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to unshare conversation",
                details={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id)
                },
                original_error=e
            )
    
    async def update_share_role(
        self,
        conversation_id: UUID,
        owner_id: UUID,
        target_user_id: UUID,
        role: ShareRole
    ) -> Optional[ConversationShare]:
        """
        Update user's role for conversation.
        
        Args:
            conversation_id: Conversation ID
            owner_id: Owner user ID
            target_user_id: Target user ID
            role: New role
            
        Returns:
            Updated share or None
        """
        try:
            share = self.db.query(ConversationShare).filter(
                and_(
                    ConversationShare.conversation_id == conversation_id,
                    ConversationShare.user_id == target_user_id
                )
            ).first()
            
            if not share:
                return None
            
            async with db_transaction(self.db):
                share.role = role
                share.updated_at = datetime.utcnow()
                
                self.db.flush()
                self.db.refresh(share)
                
                logger.info(
                    "Share role updated",
                    extra={
                        "conversation_id": str(conversation_id),
                        "target_user_id": str(target_user_id),
                        "new_role": role.value
                    }
                )
                return share
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "update_share_role"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to update share role",
                extra={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to update share role",
                details={
                    "conversation_id": str(conversation_id),
                    "target_user_id": str(target_user_id)
                },
                original_error=e
            )
    
    async def get_shared_users(
        self,
        conversation_id: UUID,
        owner_id: UUID
    ) -> List[ConversationShare]:
        """
        Get list of users with access to conversation.
        
        Args:
            conversation_id: Conversation ID
            owner_id: Owner user ID
            
        Returns:
            List of shares
        """
        try:
            shares = self.db.query(ConversationShare).filter(
                ConversationShare.conversation_id == conversation_id
            ).all()
            
            return shares
            
        except Exception as e:
            logger.error(f"Failed to get shared users: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to retrieve shared users",
                details={"conversation_id": str(conversation_id)},
                original_error=e
            )
    
    async def toggle_public_link(
        self,
        conversation_id: UUID,
        owner_id: UUID,
        is_public: bool
    ) -> Dict[str, Any]:
        """
        Toggle public link for conversation.
        
        Args:
            conversation_id: Conversation ID
            owner_id: Owner user ID
            is_public: Whether to make public
            
        Returns:
            Public link info
        """
        try:
            # In a real implementation, update conversation table
            # For now, generate a token
            if is_public:
                public_token = secrets.token_urlsafe(32)
                public_url = f"/shared/{public_token}"
            else:
                public_token = None
                public_url = None
            
            logger.info(f"Toggled public link for conversation {conversation_id}: {is_public}")
            
            return {
                "isPublic": is_public,
                "publicUrl": public_url,
                "publicToken": public_token
            }
            
        except Exception as e:
            logger.error(f"Failed to toggle public link: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to toggle public link",
                details={"conversation_id": str(conversation_id)},
                original_error=e
            )


def get_share_service(db: Session) -> ShareService:
    """Get share service instance."""
    return ShareService(db)
