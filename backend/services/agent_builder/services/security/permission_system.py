"""
Permission System for Agent Builder.

Implements Role-Based Access Control (RBAC) for agents and resources.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Types of resources."""
    AGENT = "agent"
    WORKFLOW = "workflow"
    BLOCK = "block"
    KNOWLEDGEBASE = "knowledgebase"
    EXECUTION = "execution"
    VARIABLE = "variable"


class Action(str, Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    SHARE = "share"
    ADMIN = "admin"


class Role(str, Enum):
    """User roles."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"


# Role permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        ResourceType.AGENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE, Action.ADMIN],
        ResourceType.WORKFLOW: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE, Action.ADMIN],
        ResourceType.BLOCK: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE, Action.ADMIN],
        ResourceType.KNOWLEDGEBASE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.SHARE, Action.ADMIN],
        ResourceType.EXECUTION: [Action.READ, Action.DELETE, Action.ADMIN],
        ResourceType.VARIABLE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.ADMIN],
    },
    Role.DEVELOPER: {
        ResourceType.AGENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE],
        ResourceType.WORKFLOW: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE],
        ResourceType.BLOCK: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.SHARE],
        ResourceType.KNOWLEDGEBASE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.SHARE],
        ResourceType.EXECUTION: [Action.READ, Action.DELETE],
        ResourceType.VARIABLE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE],
    },
    Role.VIEWER: {
        ResourceType.AGENT: [Action.READ, Action.EXECUTE],
        ResourceType.WORKFLOW: [Action.READ, Action.EXECUTE],
        ResourceType.BLOCK: [Action.READ],
        ResourceType.KNOWLEDGEBASE: [Action.READ],
        ResourceType.EXECUTION: [Action.READ],
        ResourceType.VARIABLE: [Action.READ],
    },
    Role.GUEST: {
        ResourceType.AGENT: [Action.READ],
        ResourceType.WORKFLOW: [Action.READ],
        ResourceType.BLOCK: [Action.READ],
        ResourceType.KNOWLEDGEBASE: [Action.READ],
        ResourceType.EXECUTION: [],
        ResourceType.VARIABLE: [],
    },
}


class PermissionDenied(Exception):
    """Raised when permission is denied."""
    pass


class AgentPermissionManager:
    """
    Manages permissions for Agent Builder resources.
    
    Features:
    - Role-based access control (RBAC)
    - Resource-level permissions
    - Permission inheritance
    - Audit logging
    """
    
    def __init__(self, db: Session):
        """
        Initialize permission manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.permission_cache: Dict[str, Set[str]] = {}
        
        logger.info("AgentPermissionManager initialized")
    
    def check_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action,
        user_role: Optional[Role] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action to perform
            user_role: Optional user role (fetched if not provided)
            
        Returns:
            True if permission granted
        """
        # Get user role if not provided
        if not user_role:
            user_role = self._get_user_role(user_id)
        
        # Check role-based permissions
        if self._check_role_permission(user_role, resource_type, action):
            # Check resource ownership or sharing
            if self._check_resource_access(user_id, resource_type, resource_id, action):
                return True
        
        return False
    
    def require_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action,
        user_role: Optional[Role] = None
    ):
        """
        Require permission or raise exception.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action to perform
            user_role: Optional user role
            
        Raises:
            PermissionDenied: If permission is denied
        """
        if not self.check_permission(user_id, resource_type, resource_id, action, user_role):
            raise PermissionDenied(
                f"User {user_id} does not have permission to {action.value} {resource_type.value} {resource_id}"
            )
    
    def _check_role_permission(
        self,
        role: Role,
        resource_type: ResourceType,
        action: Action
    ) -> bool:
        """Check if role has permission for action on resource type."""
        role_perms = ROLE_PERMISSIONS.get(role, {})
        resource_perms = role_perms.get(resource_type, [])
        return action in resource_perms
    
    def _check_resource_access(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action
    ) -> bool:
        """Check if user has access to specific resource."""
        # Check ownership
        if self._is_resource_owner(user_id, resource_type, resource_id):
            return True
        
        # Check if resource is public
        if action == Action.READ and self._is_resource_public(resource_type, resource_id):
            return True
        
        # Check explicit permissions
        if self._has_explicit_permission(user_id, resource_type, resource_id, action):
            return True
        
        return False
    
    def _get_user_role(self, user_id: str) -> Role:
        """Get user role from database."""
        # Simplified - in production, fetch from database
        # For now, return DEVELOPER as default
        return Role.DEVELOPER
    
    def _is_resource_owner(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str
    ) -> bool:
        """Check if user owns the resource."""
        try:
            from backend.db.models.agent_builder import Agent, Workflow, Block, Knowledgebase
            
            # Map resource type to model
            model_map = {
                ResourceType.AGENT: Agent,
                ResourceType.WORKFLOW: Workflow,
                ResourceType.BLOCK: Block,
                ResourceType.KNOWLEDGEBASE: Knowledgebase
            }
            
            model = model_map.get(resource_type)
            if not model:
                return False
            
            # Query resource
            resource = self.db.query(model).filter(
                model.id == resource_id
            ).first()
            
            if not resource:
                return False
            
            # Check ownership
            return str(resource.user_id) == str(user_id)
            
        except Exception as e:
            logger.error(f"Failed to check resource ownership: {e}")
            return False
    
    def _is_resource_public(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> bool:
        """Check if resource is public."""
        try:
            from backend.db.models.agent_builder import Agent, Workflow, Block, Knowledgebase
            
            # Map resource type to model
            model_map = {
                ResourceType.AGENT: Agent,
                ResourceType.WORKFLOW: Workflow,
                ResourceType.BLOCK: Block,
                ResourceType.KNOWLEDGEBASE: Knowledgebase
            }
            
            model = model_map.get(resource_type)
            if not model:
                return False
            
            # Query resource
            resource = self.db.query(model).filter(
                model.id == resource_id
            ).first()
            
            if not resource:
                return False
            
            # Check if public
            return getattr(resource, 'is_public', False)
            
        except Exception as e:
            logger.error(f"Failed to check resource public status: {e}")
            return False
    
    def _has_explicit_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action
    ) -> bool:
        """Check if user has explicit permission."""
        try:
            # Check permission cache
            cache_key = f"{user_id}:{resource_type.value}:{resource_id}:{action.value}"
            if cache_key in self.permission_cache:
                return True
            
            # Query database for explicit permissions
            from backend.db.models.agent_builder import Permission
            
            permission = self.db.query(Permission).filter(
                Permission.user_id == user_id,
                Permission.resource_type == resource_type.value,
                Permission.resource_id == resource_id,
                Permission.action == action.value
            ).first()
            
            if permission:
                # Cache the permission
                self.permission_cache[cache_key] = True
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check explicit permission: {e}")
            return False
    
    def grant_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action,
        granted_by: str
    ) -> Dict[str, Any]:
        """
        Grant permission to user.
        
        Args:
            user_id: User ID to grant permission to
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action to grant
            granted_by: User ID granting permission
            
        Returns:
            Permission record
        """
        # Create permission record
        permission = {
            "user_id": user_id,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "action": action.value,
            "granted_by": granted_by,
            "granted_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add to cache
        cache_key = f"{user_id}:{resource_type.value}:{resource_id}:{action.value}"
        if cache_key not in self.permission_cache:
            self.permission_cache[cache_key] = set()
        self.permission_cache[cache_key].add(action.value)
        
        logger.info(f"Granted {action.value} permission on {resource_type.value} {resource_id} to user {user_id}")
        
        return permission
    
    def revoke_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        action: Action
    ) -> bool:
        """
        Revoke permission from user.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action to revoke
            
        Returns:
            True if revoked
        """
        # Remove from cache
        cache_key = f"{user_id}:{resource_type.value}:{resource_id}:{action.value}"
        self.permission_cache.pop(cache_key, None)
        
        logger.info(f"Revoked {action.value} permission on {resource_type.value} {resource_id} from user {user_id}")
        
        return True
    
    def get_user_permissions(
        self,
        user_id: str,
        resource_type: Optional[ResourceType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
            resource_type: Optional filter by resource type
            
        Returns:
            List of permissions
        """
        # Get from cache
        permissions = []
        
        for cache_key in self.permission_cache:
            parts = cache_key.split(":")
            if parts[0] == user_id:
                if not resource_type or parts[1] == resource_type.value:
                    permissions.append({
                        "user_id": parts[0],
                        "resource_type": parts[1],
                        "resource_id": parts[2],
                        "action": parts[3]
                    })
        
        return permissions
    
    def share_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        owner_id: str,
        share_with_user_id: str,
        actions: List[Action]
    ) -> Dict[str, Any]:
        """
        Share resource with another user.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            owner_id: Owner user ID
            share_with_user_id: User ID to share with
            actions: List of actions to grant
            
        Returns:
            Share record
        """
        # Verify owner has permission to share
        self.require_permission(owner_id, resource_type, resource_id, Action.SHARE)
        
        # Grant permissions
        for action in actions:
            self.grant_permission(
                user_id=share_with_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                granted_by=owner_id
            )
        
        share_record = {
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "owner_id": owner_id,
            "shared_with": share_with_user_id,
            "actions": [a.value for a in actions],
            "shared_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Shared {resource_type.value} {resource_id} with user {share_with_user_id}")
        
        return share_record
