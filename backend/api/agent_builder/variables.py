"""API endpoints for workflow variables management."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import Variable, Secret
from backend.models.agent_builder import (
    VariableCreate,
    VariableUpdate,
    VariableResponse,
    VariableListResponse,
    VariableResolveRequest,
    VariableResolveResponse,
)
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.secret_manager import SecretManager
from backend.models.agent_builder import ExecutionContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/variables", tags=["variables"])


@router.post("", response_model=VariableResponse, status_code=status.HTTP_201_CREATED)
async def create_variable(
    variable_data: VariableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new variable.
    
    Variables can be scoped to global, workspace, user, or agent level.
    Secret variables are encrypted before storage.
    """
    try:
        resolver = VariableResolver(db)
        secret_manager = SecretManager(db)
        
        # Validate scope_id based on scope
        if variable_data.scope in ["user", "agent", "workspace"] and not variable_data.scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"scope_id is required for scope '{variable_data.scope}'"
            )
        
        # Create variable
        variable = resolver.create_variable(
            name=variable_data.name,
            scope=variable_data.scope,
            scope_id=variable_data.scope_id,
            value=variable_data.value,
            value_type=variable_data.value_type,
            is_secret=variable_data.is_secret,
        )
        
        # If secret, encrypt the value
        if variable_data.is_secret:
            secret_manager.encrypt_variable(variable.id, variable_data.value)
            # Mask the value in response
            variable.value = "********"
        
        logger.info(f"Variable created: {variable.name} by user {current_user.id}")
        
        return VariableResponse(
            id=str(variable.id),
            name=variable.name,
            scope=variable.scope,
            scope_id=str(variable.scope_id) if variable.scope_id else None,
            value_type=variable.value_type,
            value=variable.value,
            is_secret=variable.is_secret,
            created_at=variable.created_at,
            updated_at=variable.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating variable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create variable"
        )


@router.get("", response_model=VariableListResponse)
async def list_variables(
    scope: Optional[str] = None,
    scope_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List variables with optional filtering.
    
    Secret variable values are masked in the response.
    """
    try:
        resolver = VariableResolver(db)
        
        # List variables
        variables = resolver.list_variables(
            scope=scope,
            scope_id=scope_id,
            include_deleted=False
        )
        
        # Apply pagination
        total = len(variables)
        variables = variables[offset:offset + limit]
        
        # Convert to response models
        variable_responses = []
        for var in variables:
            value = "********" if var.is_secret else var.value
            variable_responses.append(
                VariableResponse(
                    id=str(var.id),
                    name=var.name,
                    scope=var.scope,
                    scope_id=str(var.scope_id) if var.scope_id else None,
                    value_type=var.value_type,
                    value=value,
                    is_secret=var.is_secret,
                    created_at=var.created_at,
                    updated_at=var.updated_at,
                )
            )
        
        return VariableListResponse(
            variables=variable_responses,
            total=total,
            limit=limit,
            offset=offset,
        )
        
    except Exception as e:
        logger.error(f"Error listing variables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list variables"
        )


@router.get("/{variable_id}", response_model=VariableResponse)
async def get_variable(
    variable_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific variable by ID.
    
    Secret variable values are masked in the response.
    """
    try:
        variable = db.query(Variable).filter(
            Variable.id == UUID(variable_id),
            Variable.deleted_at.is_(None)
        ).first()
        
        if not variable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variable not found"
            )
        
        value = "********" if variable.is_secret else variable.value
        
        return VariableResponse(
            id=str(variable.id),
            name=variable.name,
            scope=variable.scope,
            scope_id=str(variable.scope_id) if variable.scope_id else None,
            value_type=variable.value_type,
            value=value,
            is_secret=variable.is_secret,
            created_at=variable.created_at,
            updated_at=variable.updated_at,
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid variable ID"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting variable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get variable"
        )


@router.put("/{variable_id}", response_model=VariableResponse)
async def update_variable(
    variable_id: str,
    variable_data: VariableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a variable.
    
    Can update value and value_type. Secret values are re-encrypted.
    """
    try:
        resolver = VariableResolver(db)
        secret_manager = SecretManager(db)
        
        # Get existing variable
        variable = db.query(Variable).filter(
            Variable.id == UUID(variable_id),
            Variable.deleted_at.is_(None)
        ).first()
        
        if not variable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variable not found"
            )
        
        # Update variable
        updated_variable = resolver.update_variable(
            variable_id=variable_id,
            value=variable_data.value,
            value_type=variable_data.value_type,
        )
        
        # If secret and value changed, re-encrypt
        if updated_variable.is_secret and variable_data.value:
            secret_manager.encrypt_variable(updated_variable.id, variable_data.value)
            updated_variable.value = "********"
        
        logger.info(f"Variable updated: {updated_variable.name} by user {current_user.id}")
        
        value = "********" if updated_variable.is_secret else updated_variable.value
        
        return VariableResponse(
            id=str(updated_variable.id),
            name=updated_variable.name,
            scope=updated_variable.scope,
            scope_id=str(updated_variable.scope_id) if updated_variable.scope_id else None,
            value_type=updated_variable.value_type,
            value=value,
            is_secret=updated_variable.is_secret,
            created_at=updated_variable.created_at,
            updated_at=updated_variable.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating variable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update variable"
        )


@router.delete("/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable(
    variable_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a variable (soft delete).
    """
    try:
        resolver = VariableResolver(db)
        
        success = resolver.delete_variable(variable_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variable not found"
            )
        
        logger.info(f"Variable deleted: {variable_id} by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting variable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete variable"
        )


@router.post("/resolve", response_model=VariableResolveResponse)
async def resolve_variables(
    request: VariableResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve variables in a template string.
    
    Replaces ${variable_name} placeholders with actual values.
    """
    try:
        resolver = VariableResolver(db)
        
        # Create execution context from request
        context = ExecutionContext(
            execution_id="resolve",
            user_id=str(current_user.id),
            agent_id=request.context.get("agent_id"),
            workflow_id=request.context.get("workflow_id"),
            workspace_id=request.context.get("workspace_id"),
        )
        
        # Resolve variables
        resolved = await resolver.resolve_variables(
            template=request.template,
            context=context,
            default_values=request.context
        )
        
        # Extract variable names used
        import re
        pattern = r'\$\{([^}]+)\}'
        variables_used = re.findall(pattern, request.template)
        
        return VariableResolveResponse(
            resolved=resolved,
            variables_used=list(set(variables_used))
        )
        
    except Exception as e:
        logger.error(f"Error resolving variables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve variables"
        )
