"""Agent Builder API endpoints for permission management."""

import logging
import secrets
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.agent_builder import Permission, ResourceShare, Agent, Block, Workflow, Knowledgebase
from backend.models.agent_builder import (
    PermissionCreate,
    PermissionResponse,
    ResourceShareCreate,
    ResourceShareResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder",
    tags=["agent-builder-permissions"],
)


def check_resource_ownership(
    db: Session,
    resource_type: str,
    resource_id: str,
    user_id: str
) -> bool:
    """
    Check if user owns the resource.
    
    Args:
        db: Database session
        resource_type: Type of resource (agent, block, workflow, knowledgebase)
        resource_id: Resource ID
        user_id: User ID
        
    Returns:
        True if user owns the resource, False otherwise
    """
    try:
        from uuid import UUID
        resource_uuid = UUID(resource_id)
        user_uuid = UUID(user_id)
    except ValueError:
        return False
    
    if resource_type == "agent":
        resource = db.query(Agent).filter(
            Agent.id == resource_uuid,
            Agent.user_id == user_uuid,
            Agent.deleted_at.is_(None)
        ).first()
    elif resource_type == "block":
        resource = db.query(Block).filter(
            Block.id == resource_uuid,
            Block.user_id == user_uuid
        ).first()
    elif resource_type == "workflow":
        resource = db.query(Workflow).filter(
            Workflow.id == resource_uuid,
            Workflow.user_id == user_uuid
        ).first()
    elif resource_type == "knowledgebase":
        resource = db.query(Knowledgebase).filter(
            Knowledgebase.id == resource_uuid,
            Knowledgebase.user_id == user_uuid
        ).first()
    else:
        return False
    
    return resource is not None


def check_permission(
    db: Session,
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str
) -> bool:
    """
    Check if user has permission for the action on the resource.
    
    Args:
        db: Database session
        user_id: User ID
        resource_type: Type of resource
        resource_id: Resource ID
        action: Action to check (read, write, execute, delete, share, admin)
        
    Returns:
        True if user has permission, False otherwise
    """
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
        resource_uuid = UUID(resource_id)
    except ValueError:
        return False
    
    # Check if user owns the resource (owners have all permissions)
    if check_resource_ownership(db, resource_type, resource_id, user_id):
        return True
    
    # Check explicit permission
    permission = db.query(Permission).filter(
        Permission.user_id == user_uuid,
        Permission.resource_type == resource_type,
        Permission.resource_id == resource_uuid,
        or_(
            Permission.action == action,
            Permission.action == "admin"  # Admin permission grants all actions
        )
    ).first()
    
    return permission is not None


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant permission",
    description="Grant a user permission to access a resource. Requires ownership or admin permission on the resource.",
)
async def grant_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Grant permission to a user for a resource.
    
    **Requirements:** 9.1, 11.1, 34.1
    
    **Request Body:**
    - user_id: User ID to grant permission to
    - resource_type: Type of resource (agent, block, workflow, knowledgebase)
    - resource_id: Resource ID
    - action: Action to permit (read, write, execute, delete, share, admin)
    
    **Returns:**
    - Permission object with ID and metadata
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 403: Forbidden - user doesn't own the resource
    - 404: Resource not found
    - 409: Permission already exists
    - 500: Internal server error
    """
    try:
        logger.info(
            f"Granting permission for user {current_user.id} on "
            f"{permission_data.resource_type}:{permission_data.resource_id}"
        )
        
        # Check if current user owns the resource or has admin permission
        if not check_resource_ownership(
            db, permission_data.resource_type, permission_data.resource_id, str(current_user.id)
        ) and not check_permission(
            db, str(current_user.id), permission_data.resource_type, 
            permission_data.resource_id, "admin"
        ):
            logger.warning(
                f"User {current_user.id} attempted to grant permission without ownership"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to grant access to this resource"
            )
        
        # Check if permission already exists
        from uuid import UUID
        existing_permission = db.query(Permission).filter(
            Permission.user_id == UUID(permission_data.user_id),
            Permission.resource_type == permission_data.resource_type,
            Permission.resource_id == UUID(permission_data.resource_id),
            Permission.action == permission_data.action
        ).first()
        
        if existing_permission:
            logger.warning("Permission already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission already exists"
            )
        
        # Create permission
        permission = Permission(
            user_id=UUID(permission_data.user_id),
            resource_type=permission_data.resource_type,
            resource_id=UUID(permission_data.resource_id),
            action=permission_data.action,
            granted_by=current_user.id,
            granted_at=datetime.utcnow()
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        logger.info(f"Permission granted successfully: {permission.id}")
        
        return PermissionResponse(
            id=str(permission.id),
            user_id=str(permission.user_id),
            resource_type=permission.resource_type,
            resource_id=str(permission.resource_id),
            action=permission.action,
            granted_at=permission.granted_at,
            granted_by=str(permission.granted_by) if permission.granted_by else None
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid permission data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to grant permission: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant permission"
        )


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke permission",
    description="Revoke a user's permission to access a resource. Requires ownership or admin permission on the resource.",
)
async def revoke_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a permission.
    
    **Requirements:** 9.2, 11.1, 34.1
    
    **Path Parameters:**
    - permission_id: Permission ID to revoke
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden - user doesn't own the resource
    - 404: Permission not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Revoking permission {permission_id} by user {current_user.id}")
        
        # Get permission
        from uuid import UUID
        permission = db.query(Permission).filter(
            Permission.id == UUID(permission_id)
        ).first()
        
        if not permission:
            logger.warning(f"Permission not found: {permission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        # Check if current user owns the resource or has admin permission
        if not check_resource_ownership(
            db, permission.resource_type, str(permission.resource_id), str(current_user.id)
        ) and not check_permission(
            db, str(current_user.id), permission.resource_type, 
            str(permission.resource_id), "admin"
        ):
            logger.warning(
                f"User {current_user.id} attempted to revoke permission without ownership"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to revoke access to this resource"
            )
        
        # Delete permission
        db.delete(permission)
        db.commit()
        
        logger.info(f"Permission revoked successfully: {permission_id}")
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid permission ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission ID"
        )
    except Exception as e:
        logger.error(f"Failed to revoke permission: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke permission"
        )


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    summary="List user permissions",
    description="List all permissions for the current user or for a specific resource.",
)
async def list_permissions(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List permissions.
    
    **Requirements:** 11.1, 34.1
    
    **Query Parameters:**
    - resource_type: Filter by resource type (optional)
    - resource_id: Filter by resource ID (optional)
    
    **Returns:**
    - List of permissions
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Listing permissions for user {current_user.id}")
        
        # Build query
        query = db.query(Permission)
        
        # If resource_id is provided, check if user owns the resource or has admin permission
        if resource_id:
            if not resource_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="resource_type is required when resource_id is provided"
                )
            
            # Check if user owns the resource or has admin permission
            if not check_resource_ownership(
                db, resource_type, resource_id, str(current_user.id)
            ) and not check_permission(
                db, str(current_user.id), resource_type, resource_id, "admin"
            ):
                logger.warning(
                    f"User {current_user.id} attempted to list permissions without ownership"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view permissions for this resource"
                )
            
            from uuid import UUID
            query = query.filter(
                Permission.resource_type == resource_type,
                Permission.resource_id == UUID(resource_id)
            )
        else:
            # List permissions granted to the current user
            query = query.filter(Permission.user_id == current_user.id)
            
            if resource_type:
                query = query.filter(Permission.resource_type == resource_type)
        
        permissions = query.all()
        
        logger.info(f"Found {len(permissions)} permissions")
        
        return [
            PermissionResponse(
                id=str(p.id),
                user_id=str(p.user_id),
                resource_type=p.resource_type,
                resource_id=str(p.resource_id),
                action=p.action,
                granted_at=p.granted_at,
                granted_by=str(p.granted_by) if p.granted_by else None
            )
            for p in permissions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list permissions"
        )


@router.post(
    "/shares",
    response_model=ResourceShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shareable link",
    description="Create a shareable link with token for a resource. Requires ownership or share permission on the resource.",
)
async def create_share(
    share_data: ResourceShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a shareable link for a resource.
    
    **Requirements:** 9.1, 34.3, 34.4
    
    **Request Body:**
    - resource_type: Type of resource (agent, block, workflow, knowledgebase)
    - resource_id: Resource ID
    - permissions: List of allowed actions
    - expires_at: Expiration time (optional)
    
    **Returns:**
    - Resource share object with share token
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 403: Forbidden - user doesn't own the resource
    - 404: Resource not found
    - 500: Internal server error
    """
    try:
        logger.info(
            f"Creating share for user {current_user.id} on "
            f"{share_data.resource_type}:{share_data.resource_id}"
        )
        
        # Check if current user owns the resource or has share permission
        if not check_resource_ownership(
            db, share_data.resource_type, share_data.resource_id, str(current_user.id)
        ) and not check_permission(
            db, str(current_user.id), share_data.resource_type, 
            share_data.resource_id, "share"
        ):
            logger.warning(
                f"User {current_user.id} attempted to create share without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to share this resource"
            )
        
        # Generate unique share token
        share_token = secrets.token_urlsafe(32)
        
        # Create resource share
        from uuid import UUID
        resource_share = ResourceShare(
            resource_type=share_data.resource_type,
            resource_id=UUID(share_data.resource_id),
            share_token=share_token,
            permissions=share_data.permissions,
            expires_at=share_data.expires_at,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(resource_share)
        db.commit()
        db.refresh(resource_share)
        
        logger.info(f"Share created successfully: {resource_share.id}")
        
        return ResourceShareResponse(
            id=str(resource_share.id),
            resource_type=resource_share.resource_type,
            resource_id=str(resource_share.resource_id),
            share_token=resource_share.share_token,
            permissions=resource_share.permissions,
            expires_at=resource_share.expires_at,
            created_by=str(resource_share.created_by),
            created_at=resource_share.created_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid share data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create share: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share"
        )


@router.get(
    "/shares/{token}",
    response_model=dict,
    summary="Access shared resource",
    description="Access a shared resource using a share token. Returns resource details if token is valid and not expired.",
)
async def access_shared_resource(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Access a shared resource using a share token.
    
    **Requirements:** 9.2, 34.4
    
    **Path Parameters:**
    - token: Share token
    
    **Returns:**
    - Resource details and allowed permissions
    
    **Errors:**
    - 404: Share not found or expired
    - 500: Internal server error
    """
    try:
        logger.info(f"Accessing shared resource with token")
        
        # Get resource share
        resource_share = db.query(ResourceShare).filter(
            ResourceShare.share_token == token
        ).first()
        
        if not resource_share:
            logger.warning("Share not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )
        
        # Check if share has expired
        if resource_share.expires_at and resource_share.expires_at < datetime.utcnow():
            logger.warning("Share has expired")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share has expired"
            )
        
        # Get resource details based on type
        resource = None
        if resource_share.resource_type == "agent":
            resource = db.query(Agent).filter(
                Agent.id == resource_share.resource_id,
                Agent.deleted_at.is_(None)
            ).first()
        elif resource_share.resource_type == "block":
            resource = db.query(Block).filter(
                Block.id == resource_share.resource_id
            ).first()
        elif resource_share.resource_type == "workflow":
            resource = db.query(Workflow).filter(
                Workflow.id == resource_share.resource_id
            ).first()
        elif resource_share.resource_type == "knowledgebase":
            resource = db.query(Knowledgebase).filter(
                Knowledgebase.id == resource_share.resource_id
            ).first()
        
        if not resource:
            logger.warning("Resource not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        logger.info(f"Shared resource accessed successfully")
        
        # Return resource details (read-only view)
        return {
            "resource_type": resource_share.resource_type,
            "resource_id": str(resource_share.resource_id),
            "permissions": resource_share.permissions,
            "resource": {
                "id": str(resource.id),
                "name": resource.name,
                "description": resource.description if hasattr(resource, "description") else None,
                "created_at": resource.created_at.isoformat() if hasattr(resource, "created_at") else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to access shared resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access shared resource"
        )
