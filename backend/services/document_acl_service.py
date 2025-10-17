"""
Document Access Control List (ACL) Service.

Provides fine-grained access control for documents including:
- User-level permissions
- Group-level permissions
- Permission inheritance
- Permission checking with caching
- Audit logging
- Bulk operations
"""

import logging
from typing import Optional, List, Dict, Set
from uuid import UUID
from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.permission import (
    DocumentPermission,
    Group,
    GroupMember,
    PermissionType,
)
from backend.db.models.document import Document

logger = logging.getLogger(__name__)


class DocumentACLServiceError(Exception):
    """Custom exception for ACL service errors."""

    pass


class PermissionCache:
    """Simple in-memory cache for permission checks."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL."""
        self._cache: Dict[str, tuple[bool, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[bool]:
        """Get cached permission result."""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self._ttl:
                return result
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: bool) -> None:
        """Cache permission result."""
        self._cache[key] = (value, datetime.utcnow())

    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]


# Global permission cache
_permission_cache = PermissionCache()


class DocumentACLService:
    """
    Service for managing document access control.

    Features:
    - User-level permissions (read, write, admin)
    - Group-level permissions
    - Permission inheritance
    - Owner always has admin permission
    - Permission checking with caching
    """

    def __init__(self, db: Session):
        """
        Initialize DocumentACLService.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("DocumentACLService initialized")

    async def check_permission(
        self,
        user_id: UUID,
        document_id: UUID,
        required_permission: PermissionType = PermissionType.READ,
        use_cache: bool = True,
    ) -> bool:
        """
        Check if user has required permission for document.

        Permission hierarchy: admin > write > read

        Args:
            user_id: User's unique identifier
            document_id: Document UUID
            required_permission: Required permission level
            use_cache: Whether to use permission cache

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Check cache first
            if use_cache:
                cache_key = f"{user_id}:{document_id}:{required_permission.value}"
                cached_result = _permission_cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for permission check: {cache_key}")
                    return cached_result

            # Check if user is document owner (always has admin)
            document = (
                self.db.query(Document).filter(Document.id == document_id).first()
            )

            if not document:
                logger.warning(f"Document {document_id} not found")
                return False

            if document.user_id == user_id:
                logger.debug(f"User {user_id} is owner of document {document_id}")
                result = True
            else:
                # Check direct user permission
                has_direct = await self._check_direct_permission(
                    user_id, document_id, required_permission
                )
                if has_direct:
                    result = True
                else:
                    # Check group permissions
                    user_groups = await self._get_user_groups(user_id)
                    result = False
                    for group in user_groups:
                        has_group = await self._check_group_permission(
                            group.id, document_id, required_permission
                        )
                        if has_group:
                            logger.debug(
                                f"User {user_id} has permission via group {group.id}"
                            )
                            result = True
                            break

                    if not result:
                        logger.debug(
                            f"User {user_id} does not have {required_permission} "
                            f"permission for document {document_id}"
                        )

            # Cache the result
            if use_cache:
                cache_key = f"{user_id}:{document_id}:{required_permission.value}"
                _permission_cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Permission check failed: {e}", exc_info=True)
            return False

    async def _check_direct_permission(
        self, user_id: UUID, document_id: UUID, required_permission: PermissionType
    ) -> bool:
        """Check direct user permission."""
        try:
            permission = (
                self.db.query(DocumentPermission)
                .filter(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                )
                .first()
            )

            if not permission:
                return False

            # Check expiration
            if permission.expires_at and permission.expires_at < datetime.utcnow():
                logger.debug(f"Permission expired for user {user_id}")
                return False

            # Check permission level
            return self._has_sufficient_permission(
                permission.permission_type, required_permission
            )

        except Exception as e:
            logger.error(f"Direct permission check failed: {e}")
            return False

    async def _check_group_permission(
        self, group_id: UUID, document_id: UUID, required_permission: PermissionType
    ) -> bool:
        """Check group permission."""
        try:
            permission = (
                self.db.query(DocumentPermission)
                .filter(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.group_id == group_id,
                )
                .first()
            )

            if not permission:
                return False

            # Check expiration
            if permission.expires_at and permission.expires_at < datetime.utcnow():
                return False

            # Check permission level
            return self._has_sufficient_permission(
                permission.permission_type, required_permission
            )

        except Exception as e:
            logger.error(f"Group permission check failed: {e}")
            return False

    def _has_sufficient_permission(
        self, granted_permission: PermissionType, required_permission: PermissionType
    ) -> bool:
        """
        Check if granted permission is sufficient.

        Hierarchy: admin > write > read
        """
        permission_levels = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3,
        }

        granted_level = permission_levels.get(granted_permission, 0)
        required_level = permission_levels.get(required_permission, 0)

        return granted_level >= required_level

    async def _get_user_groups(self, user_id: UUID) -> List[Group]:
        """Get all groups user belongs to."""
        try:
            memberships = (
                self.db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
            )

            groups = [m.group for m in memberships if m.group]

            return groups

        except Exception as e:
            logger.error(f"Failed to get user groups: {e}")
            return []

    async def grant_permission(
        self,
        document_id: UUID,
        owner_id: UUID,
        target_user_id: Optional[UUID] = None,
        target_group_id: Optional[UUID] = None,
        permission_type: PermissionType = PermissionType.READ,
        expires_at: Optional[datetime] = None,
    ) -> DocumentPermission:
        """
        Grant permission to user or group.

        Args:
            document_id: Document UUID
            owner_id: Owner user ID (must have admin permission)
            target_user_id: Target user ID (if user permission)
            target_group_id: Target group ID (if group permission)
            permission_type: Permission to grant
            expires_at: Optional expiration date

        Returns:
            Created DocumentPermission

        Raises:
            DocumentACLServiceError: If grant fails
        """
        try:
            # Verify owner has admin permission
            has_admin = await self.check_permission(
                owner_id, document_id, PermissionType.ADMIN, use_cache=False
            )

            if not has_admin:
                raise DocumentACLServiceError(
                    "Only document admin can grant permissions"
                )

            # Verify target
            if not target_user_id and not target_group_id:
                raise DocumentACLServiceError(
                    "Either target_user_id or target_group_id must be provided"
                )

            # Check if permission already exists
            existing = (
                self.db.query(DocumentPermission)
                .filter(
                    DocumentPermission.document_id == document_id,
                    (
                        DocumentPermission.user_id == target_user_id
                        if target_user_id
                        else None
                    ),
                    (
                        DocumentPermission.group_id == target_group_id
                        if target_group_id
                        else None
                    ),
                )
                .first()
            )

            if existing:
                # Update existing permission
                old_type = existing.permission_type
                existing.permission_type = permission_type
                existing.expires_at = expires_at
                existing.granted_by = owner_id
                existing.granted_at = datetime.utcnow()

                self.db.commit()
                self.db.refresh(existing)

                # Invalidate cache for this document
                _permission_cache.invalidate(str(document_id))

                logger.info(
                    f"Updated permission: {existing.id} "
                    f"(doc={document_id}, {old_type} -> {permission_type})"
                )
                return existing

            # Create new permission
            permission = DocumentPermission(
                document_id=document_id,
                user_id=target_user_id,
                group_id=target_group_id,
                permission_type=permission_type,
                granted_by=owner_id,
                expires_at=expires_at,
            )

            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)

            # Invalidate cache for this document
            _permission_cache.invalidate(str(document_id))

            logger.info(
                f"Permission granted: {permission.id} "
                f"(doc={document_id}, type={permission_type})"
            )

            return permission

        except DocumentACLServiceError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to grant permission: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to grant permission: {e}")

    async def revoke_permission(self, permission_id: UUID, owner_id: UUID) -> None:
        """
        Revoke a permission.

        Args:
            permission_id: Permission UUID
            owner_id: Owner user ID (must have admin permission)

        Raises:
            DocumentACLServiceError: If revoke fails
        """
        try:
            # Get permission
            permission = (
                self.db.query(DocumentPermission)
                .filter(DocumentPermission.id == permission_id)
                .first()
            )

            if not permission:
                raise DocumentACLServiceError("Permission not found")

            # Verify owner has admin permission
            has_admin = await self.check_permission(
                owner_id, permission.document_id, PermissionType.ADMIN
            )

            if not has_admin:
                raise DocumentACLServiceError(
                    "Only document admin can revoke permissions"
                )

            # Delete permission
            self.db.delete(permission)
            self.db.commit()

            logger.info(f"Permission revoked: {permission_id}")

        except DocumentACLServiceError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke permission: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to revoke permission: {e}")

    async def list_document_permissions(
        self, document_id: UUID, owner_id: UUID
    ) -> List[DocumentPermission]:
        """
        List all permissions for a document.

        Args:
            document_id: Document UUID
            owner_id: Owner user ID (must have admin permission)

        Returns:
            List of DocumentPermission objects

        Raises:
            DocumentACLServiceError: If listing fails
        """
        try:
            # Verify owner has admin permission
            has_admin = await self.check_permission(
                owner_id, document_id, PermissionType.ADMIN
            )

            if not has_admin:
                raise DocumentACLServiceError(
                    "Only document admin can list permissions"
                )

            # Get permissions
            permissions = (
                self.db.query(DocumentPermission)
                .filter(DocumentPermission.document_id == document_id)
                .all()
            )

            logger.info(
                f"Listed {len(permissions)} permissions for document {document_id}"
            )

            return permissions

        except DocumentACLServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to list permissions: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to list permissions: {e}")

    async def create_group(
        self, name: str, description: Optional[str], creator_id: UUID
    ) -> Group:
        """
        Create a new group.

        Args:
            name: Group name
            description: Optional description
            creator_id: Creator user ID

        Returns:
            Created Group

        Raises:
            DocumentACLServiceError: If creation fails
        """
        try:
            # Check if group name already exists
            existing = self.db.query(Group).filter(Group.name == name).first()

            if existing:
                raise DocumentACLServiceError(f"Group '{name}' already exists")

            # Create group
            group = Group(name=name, description=description, created_by=creator_id)

            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)

            # Add creator as first member
            member = GroupMember(
                group_id=group.id, user_id=creator_id, added_by=creator_id
            )

            self.db.add(member)
            self.db.commit()

            logger.info(f"Group created: {group.id} ({name})")

            return group

        except DocumentACLServiceError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create group: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to create group: {e}")

    async def add_group_member(
        self, group_id: UUID, user_id: UUID, added_by: UUID
    ) -> GroupMember:
        """
        Add user to group.

        Args:
            group_id: Group UUID
            user_id: User UUID to add
            added_by: User ID performing the action

        Returns:
            Created GroupMember

        Raises:
            DocumentACLServiceError: If addition fails
        """
        try:
            # Verify group exists
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise DocumentACLServiceError(f"Group {group_id} not found")

            # Check if adder is group creator or existing member
            is_creator = group.created_by == added_by
            is_member = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == group_id, GroupMember.user_id == added_by
                )
                .first()
                is not None
            )

            if not (is_creator or is_member):
                raise DocumentACLServiceError(
                    "Only group creator or members can add new members"
                )

            # Check if already member
            existing = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == group_id, GroupMember.user_id == user_id
                )
                .first()
            )

            if existing:
                logger.info(f"User {user_id} already in group {group_id}")
                return existing

            # Add member
            member = GroupMember(group_id=group_id, user_id=user_id, added_by=added_by)

            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)

            # Invalidate cache for all documents with this group permission
            _permission_cache.invalidate(str(group_id))

            logger.info(f"User {user_id} added to group {group_id}")

            return member

        except DocumentACLServiceError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add group member: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to add group member: {e}")

    async def remove_group_member(
        self, group_id: UUID, user_id: UUID, removed_by: UUID
    ) -> None:
        """
        Remove user from group.

        Args:
            group_id: Group UUID
            user_id: User UUID to remove
            removed_by: User ID performing the action

        Raises:
            DocumentACLServiceError: If removal fails
        """
        try:
            # Verify group exists
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise DocumentACLServiceError(f"Group {group_id} not found")

            # Check if remover is group creator
            if group.created_by != removed_by:
                raise DocumentACLServiceError("Only group creator can remove members")

            # Find member
            member = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == group_id, GroupMember.user_id == user_id
                )
                .first()
            )

            if not member:
                raise DocumentACLServiceError(
                    f"User {user_id} is not a member of group {group_id}"
                )

            # Don't allow removing creator
            if user_id == group.created_by:
                raise DocumentACLServiceError("Cannot remove group creator from group")

            # Remove member
            self.db.delete(member)
            self.db.commit()

            # Invalidate cache
            _permission_cache.invalidate(str(group_id))

            logger.info(f"User {user_id} removed from group {group_id}")

        except DocumentACLServiceError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove group member: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to remove group member: {e}")

    async def grant_bulk_permissions(
        self,
        document_id: UUID,
        owner_id: UUID,
        user_ids: List[UUID],
        permission_type: PermissionType = PermissionType.READ,
        expires_at: Optional[datetime] = None,
    ) -> List[DocumentPermission]:
        """
        Grant permission to multiple users at once.

        Args:
            document_id: Document UUID
            owner_id: Owner user ID (must have admin permission)
            user_ids: List of user IDs to grant permission to
            permission_type: Permission to grant
            expires_at: Optional expiration date

        Returns:
            List of created/updated DocumentPermission objects

        Raises:
            DocumentACLServiceError: If grant fails
        """
        try:
            # Verify owner has admin permission
            has_admin = await self.check_permission(
                owner_id, document_id, PermissionType.ADMIN, use_cache=False
            )

            if not has_admin:
                raise DocumentACLServiceError(
                    "Only document admin can grant permissions"
                )

            permissions = []

            for user_id in user_ids:
                try:
                    permission = await self.grant_permission(
                        document_id=document_id,
                        owner_id=owner_id,
                        target_user_id=user_id,
                        permission_type=permission_type,
                        expires_at=expires_at,
                    )
                    permissions.append(permission)
                except Exception as e:
                    logger.warning(f"Failed to grant permission to user {user_id}: {e}")

            logger.info(
                f"Bulk granted {len(permissions)} permissions for document {document_id}"
            )

            return permissions

        except DocumentACLServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to grant bulk permissions: {e}", exc_info=True)
            raise DocumentACLServiceError(f"Failed to grant bulk permissions: {e}")

    async def cleanup_expired_permissions(self) -> int:
        """
        Remove expired permissions from database.

        Returns:
            Number of permissions removed
        """
        try:
            # Find expired permissions
            expired = (
                self.db.query(DocumentPermission)
                .filter(
                    and_(
                        DocumentPermission.expires_at.isnot(None),
                        DocumentPermission.expires_at < datetime.utcnow(),
                    )
                )
                .all()
            )

            count = len(expired)

            # Delete expired permissions
            for permission in expired:
                self.db.delete(permission)

            self.db.commit()

            # Clear cache
            _permission_cache.invalidate()

            logger.info(f"Cleaned up {count} expired permissions")

            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired permissions: {e}", exc_info=True)
            return 0

    async def get_user_accessible_documents(
        self, user_id: UUID, permission_type: PermissionType = PermissionType.READ
    ) -> List[UUID]:
        """
        Get list of document IDs that user can access.

        Args:
            user_id: User UUID
            permission_type: Minimum required permission

        Returns:
            List of document IDs
        """
        try:
            document_ids: Set[UUID] = set()

            # Get documents owned by user
            owned_docs = (
                self.db.query(Document.id).filter(Document.user_id == user_id).all()
            )
            document_ids.update([doc.id for doc in owned_docs])

            # Get documents with direct user permission
            user_perms = (
                self.db.query(DocumentPermission.document_id)
                .filter(
                    and_(
                        DocumentPermission.user_id == user_id,
                        or_(
                            DocumentPermission.expires_at.is_(None),
                            DocumentPermission.expires_at > datetime.utcnow(),
                        ),
                    )
                )
                .all()
            )

            for perm in user_perms:
                document_ids.add(perm.document_id)

            # Get documents with group permission
            user_groups = await self._get_user_groups(user_id)
            for group in user_groups:
                group_perms = (
                    self.db.query(DocumentPermission.document_id)
                    .filter(
                        and_(
                            DocumentPermission.group_id == group.id,
                            or_(
                                DocumentPermission.expires_at.is_(None),
                                DocumentPermission.expires_at > datetime.utcnow(),
                            ),
                        )
                    )
                    .all()
                )

                for perm in group_perms:
                    document_ids.add(perm.document_id)

            logger.info(f"User {user_id} has access to {len(document_ids)} documents")

            return list(document_ids)

        except Exception as e:
            logger.error(f"Failed to get accessible documents: {e}", exc_info=True)
            return []


def get_document_acl_service(db: Session) -> DocumentACLService:
    """
    Get DocumentACLService instance.

    Args:
        db: Database session

    Returns:
        DocumentACLService instance
    """
    return DocumentACLService(db)
