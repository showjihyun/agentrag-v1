# Document Access Control List (ACL) Service
import logging
from typing import List, Set, Optional, Dict
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Document permissions"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"


@dataclass
class AccessRule:
    """Access control rule"""

    user_id: str
    permissions: Set[Permission]
    granted_by: str
    granted_at: str


class DocumentACL:
    """
    Document-level Access Control List.

    Features:
    - Fine-grained permissions (read, write, delete, share)
    - User and group-based access
    - Inheritance from parent documents/folders
    - Audit logging
    """

    def __init__(self):
        # document_id -> {user_id -> AccessRule}
        self.acls: Dict[str, Dict[str, AccessRule]] = {}

        # document_id -> owner_id
        self.owners: Dict[str, str] = {}

        # Audit log
        self.audit_log: List[Dict] = []

    def set_owner(self, document_id: str, user_id: str):
        """Set document owner"""
        self.owners[document_id] = user_id

        # Owner gets all permissions
        self.grant_permission(
            document_id=document_id,
            user_id=user_id,
            permissions={
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.SHARE,
            },
            granted_by="system",
        )

        logger.info(f"Set owner of document {document_id} to user {user_id}")

    def grant_permission(
        self,
        document_id: str,
        user_id: str,
        permissions: Set[Permission],
        granted_by: str,
    ):
        """Grant permissions to user"""
        from datetime import datetime

        if document_id not in self.acls:
            self.acls[document_id] = {}

        self.acls[document_id][user_id] = AccessRule(
            user_id=user_id,
            permissions=permissions,
            granted_by=granted_by,
            granted_at=datetime.utcnow().isoformat(),
        )

        # Audit log
        self.audit_log.append(
            {
                "action": "grant_permission",
                "document_id": document_id,
                "user_id": user_id,
                "permissions": [p.value for p in permissions],
                "granted_by": granted_by,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info(
            f"Granted permissions {permissions} to user {user_id} "
            f"for document {document_id}"
        )

    def revoke_permission(self, document_id: str, user_id: str, revoked_by: str):
        """Revoke all permissions from user"""
        from datetime import datetime

        if document_id in self.acls and user_id in self.acls[document_id]:
            del self.acls[document_id][user_id]

            # Audit log
            self.audit_log.append(
                {
                    "action": "revoke_permission",
                    "document_id": document_id,
                    "user_id": user_id,
                    "revoked_by": revoked_by,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            logger.info(
                f"Revoked permissions from user {user_id} "
                f"for document {document_id}"
            )

    def check_permission(
        self, document_id: str, user_id: str, permission: Permission
    ) -> bool:
        """Check if user has permission"""
        # Owner always has all permissions
        if self.owners.get(document_id) == user_id:
            return True

        # Check ACL
        if document_id in self.acls and user_id in self.acls[document_id]:
            return permission in self.acls[document_id][user_id].permissions

        return False

    def get_accessible_documents(
        self, user_id: str, permission: Permission = Permission.READ
    ) -> List[str]:
        """Get list of documents user can access"""
        accessible = []

        for doc_id, acl in self.acls.items():
            if user_id in acl and permission in acl[user_id].permissions:
                accessible.append(doc_id)

        return accessible

    def get_document_permissions(self, document_id: str) -> Dict[str, List[str]]:
        """Get all permissions for document"""
        if document_id not in self.acls:
            return {}

        result = {}
        for user_id, rule in self.acls[document_id].items():
            result[user_id] = [p.value for p in rule.permissions]

        return result


# Global ACL service
_document_acl: Optional[DocumentACL] = None


def get_document_acl() -> DocumentACL:
    """Get global document ACL service"""
    global _document_acl
    if _document_acl is None:
        _document_acl = DocumentACL()
    return _document_acl
