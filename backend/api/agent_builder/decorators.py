"""Decorators for Agent Builder API endpoints."""

import logging
from functools import wraps
from typing import Callable, Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.db.models.user import User
from backend.services.agent_builder.permission_system import PermissionSystem

logger = logging.getLogger(__name__)


def require_resource_permission(
    resource_type: Literal["agent", "block", "workflow", "knowledgebase"],
    action: Literal["read", "write", "execute", "delete", "share", "admin"]
):
    """
    Decorator to check resource permissions.
    
    Args:
        resource_type: Type of resource
        action: Action to check permission for
        
    Returns:
        Decorated function
        
    Usage:
        @router.get("/{block_id}")
        @require_resource_permission("block", "read")
        async def get_block(
            block_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            resource_id = kwargs.get(f"{resource_type}_id")
            if not resource_id:
                # Try alternative parameter names
                resource_id = kwargs.get("id") or kwargs.get("resource_id")
            
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {resource_type}_id parameter"
                )
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check permission
            try:
                permission_system = PermissionSystem(db)
                
                has_permission = permission_system.check_permission(
                    user_id=str(current_user.id),
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action
                )
                
                if not has_permission:
                    logger.warning(
                        f"Permission denied: user {current_user.id} "
                        f"attempted {action} on {resource_type} {resource_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You don't have permission to {action} this {resource_type}"
                    )
                
                # Permission granted, call original function
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Permission check failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed"
                )
        
        return wrapper
    return decorator


def require_ownership(
    resource_type: Literal["agent", "block", "workflow", "knowledgebase"]
):
    """
    Decorator to check resource ownership.
    
    Args:
        resource_type: Type of resource
        
    Returns:
        Decorated function
        
    Usage:
        @router.put("/{block_id}")
        @require_ownership("block")
        async def update_block(
            block_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            resource_id = kwargs.get(f"{resource_type}_id")
            if not resource_id:
                resource_id = kwargs.get("id") or kwargs.get("resource_id")
            
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {resource_type}_id parameter"
                )
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check ownership
            try:
                from backend.services.agent_builder.agent_service import AgentService
                from backend.services.agent_builder.block_service import BlockService
                from backend.services.agent_builder.workflow_service import WorkflowService
                from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
                
                # Get appropriate service
                if resource_type == "agent":
                    service = AgentService(db)
                    resource = service.get_agent(resource_id)
                elif resource_type == "block":
                    service = BlockService(db)
                    resource = service.get_block(resource_id)
                elif resource_type == "workflow":
                    service = WorkflowService(db)
                    resource = service.get_workflow(resource_id)
                elif resource_type == "knowledgebase":
                    service = KnowledgebaseService(db)
                    resource = service.get_knowledgebase(resource_id)
                else:
                    raise ValueError(f"Unknown resource type: {resource_type}")
                
                if not resource:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource_type.capitalize()} not found"
                    )
                
                # Check if user is owner
                if str(resource.user_id) != str(current_user.id):
                    logger.warning(
                        f"Ownership check failed: user {current_user.id} "
                        f"is not owner of {resource_type} {resource_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You don't own this {resource_type}"
                    )
                
                # Ownership confirmed, call original function
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Ownership check failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ownership check failed"
                )
        
        return wrapper
    return decorator


def require_public_or_permission(
    resource_type: Literal["agent", "block", "workflow", "knowledgebase"],
    action: Literal["read", "execute"] = "read"
):
    """
    Decorator to check if resource is public or user has permission.
    
    Args:
        resource_type: Type of resource
        action: Action to check permission for
        
    Returns:
        Decorated function
        
    Usage:
        @router.get("/{block_id}")
        @require_public_or_permission("block", "read")
        async def get_block(
            block_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            resource_id = kwargs.get(f"{resource_type}_id")
            if not resource_id:
                resource_id = kwargs.get("id") or kwargs.get("resource_id")
            
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {resource_type}_id parameter"
                )
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check if public or has permission
            try:
                from backend.services.agent_builder.agent_service import AgentService
                from backend.services.agent_builder.block_service import BlockService
                from backend.services.agent_builder.workflow_service import WorkflowService
                from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
                
                # Get appropriate service
                if resource_type == "agent":
                    service = AgentService(db)
                    resource = service.get_agent(resource_id)
                elif resource_type == "block":
                    service = BlockService(db)
                    resource = service.get_block(resource_id)
                elif resource_type == "workflow":
                    service = WorkflowService(db)
                    resource = service.get_workflow(resource_id)
                elif resource_type == "knowledgebase":
                    service = KnowledgebaseService(db)
                    resource = service.get_knowledgebase(resource_id)
                else:
                    raise ValueError(f"Unknown resource type: {resource_type}")
                
                if not resource:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource_type.capitalize()} not found"
                    )
                
                # Check if public
                if getattr(resource, 'is_public', False):
                    return await func(*args, **kwargs)
                
                # Check if owner
                if str(resource.user_id) == str(current_user.id):
                    return await func(*args, **kwargs)
                
                # Check permission
                permission_system = PermissionSystem(db)
                has_permission = permission_system.check_permission(
                    user_id=str(current_user.id),
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action
                )
                
                if not has_permission:
                    logger.warning(
                        f"Access denied: user {current_user.id} "
                        f"attempted to access {resource_type} {resource_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You don't have permission to access this {resource_type}"
                    )
                
                # Permission granted, call original function
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Access check failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Access check failed"
                )
        
        return wrapper
    return decorator
