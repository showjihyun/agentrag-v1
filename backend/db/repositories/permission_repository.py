"""Permission repository for document ACL operations."""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.permission import DocumentPermission

logger = logging.getLogger(__name__)


class PermissionRepository:
    """Database operations for document permissions."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def grant_permission(
        self, document_id: UUID, user_id: UUID, permission_type: str, granted_by: UUID
    ) -> DocumentPermission:
        """Grant permission to a user for a document."""
        try:
            # Check if permission already exists
            existing = (
                self.db.query(DocumentPermission)
                .filter(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                    DocumentPermission.permission_type == permission_type,
                )
                .first()
            )

            if existing:
                logger.info(f"Permission already exists: {existing.id}")
                return existing

            permission = DocumentPermission(
                document_id=document_id,
                user_id=user_id,
                permission_type=permission_type,
                granted_by=granted_by,
            )

            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)

            logger.info(
                f"Granted {permission_type} permission on document {document_id} "
                f"to user {user_id}"
            )
            return permission

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to grant permission: {e}")
            raise

    def revoke_permission(
        self, document_id: UUID, user_id: UUID, permission_type: Optional[str] = None
    ) -> int:
        """Revoke permission(s) from a user for a document."""
        try:
            query = self.db.query(DocumentPermission).filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.user_id == user_id,
            )

            if permission_type:
                query = query.filter(
                    DocumentPermission.permission_type == permission_type
                )

            count = query.delete()
            self.db.commit()

            logger.info(
                f"Revoked {count} permission(s) on document {document_id} "
                f"from user {user_id}"
            )
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke permission: {e}")
            raise

    def get_document_permissions(self, document_id: UUID) -> List[DocumentPermission]:
        """Get all permissions for a document."""
        return (
            self.db.query(DocumentPermission)
            .filter(DocumentPermission.document_id == document_id)
            .all()
        )

    def get_user_permissions(
        self, user_id: UUID, document_id: UUID
    ) -> List[DocumentPermission]:
        """Get user's permissions for a specific document."""
        return (
            self.db.query(DocumentPermission)
            .filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.user_id == user_id,
            )
            .all()
        )

    def has_permission(
        self, user_id: UUID, document_id: UUID, permission_type: str
    ) -> bool:
        """Check if user has specific permission for a document."""
        permission = (
            self.db.query(DocumentPermission)
            .filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.user_id == user_id,
                DocumentPermission.permission_type == permission_type,
            )
            .first()
        )

        return permission is not None

    def get_accessible_documents(
        self, user_id: UUID, permission_type: str = "read"
    ) -> List[UUID]:
        """Get list of document IDs accessible to user."""
        permissions = (
            self.db.query(DocumentPermission.document_id)
            .filter(
                DocumentPermission.user_id == user_id,
                DocumentPermission.permission_type == permission_type,
            )
            .all()
        )

        return [p.document_id for p in permissions]
