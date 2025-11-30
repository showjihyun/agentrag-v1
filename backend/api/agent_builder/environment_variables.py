"""
Environment Variables API for Agent Builder

Provides endpoints for managing user-defined environment variables
that can be used in workflows.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/environment-variables", tags=["Environment Variables"])


class EnvironmentVariable(BaseModel):
    """Environment variable model"""
    id: str
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., max_length=10000)
    description: str = Field(default="", max_length=500)
    is_secret: bool = Field(default=False, alias="isSecret")
    
    class Config:
        populate_by_name = True


class EnvironmentVariablesRequest(BaseModel):
    """Request model for updating environment variables"""
    variables: List[EnvironmentVariable]


class EnvironmentVariablesResponse(BaseModel):
    """Response model for environment variables"""
    variables: List[EnvironmentVariable]
    total: int
    updated_at: Optional[datetime] = None


# In-memory storage for demo (in production, use database)
_user_env_vars: dict[int, List[dict]] = {}


@router.get("", response_model=EnvironmentVariablesResponse)
async def get_environment_variables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all environment variables for the current user.
    """
    try:
        user_id = current_user.id
        variables = _user_env_vars.get(user_id, [])
        
        return EnvironmentVariablesResponse(
            variables=[EnvironmentVariable(**v) for v in variables],
            total=len(variables),
            updated_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error getting environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=EnvironmentVariablesResponse)
async def update_environment_variables(
    request: EnvironmentVariablesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update all environment variables for the current user.
    This replaces all existing variables with the provided list.
    """
    try:
        user_id = current_user.id
        
        # Validate unique keys
        keys = [v.key for v in request.variables]
        if len(keys) != len(set(keys)):
            raise HTTPException(status_code=400, detail="Duplicate variable keys are not allowed")
        
        # Store variables (mask secret values in logs)
        variables_data = []
        for v in request.variables:
            var_dict = v.model_dump(by_alias=True)
            variables_data.append(var_dict)
            
            # Log without exposing secret values
            log_value = "***" if v.is_secret else v.value[:20] + "..." if len(v.value) > 20 else v.value
            logger.info(f"User {user_id} updated env var: {v.key}={log_value}")
        
        _user_env_vars[user_id] = variables_data
        
        return EnvironmentVariablesResponse(
            variables=request.variables,
            total=len(request.variables),
            updated_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}")
async def get_environment_variable(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific environment variable by key.
    """
    try:
        user_id = current_user.id
        variables = _user_env_vars.get(user_id, [])
        
        for v in variables:
            if v.get("key") == key:
                return EnvironmentVariable(**v)
        
        raise HTTPException(status_code=404, detail=f"Variable '{key}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting environment variable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key}")
async def delete_environment_variable(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific environment variable by key.
    """
    try:
        user_id = current_user.id
        variables = _user_env_vars.get(user_id, [])
        
        original_count = len(variables)
        variables = [v for v in variables if v.get("key") != key]
        
        if len(variables) == original_count:
            raise HTTPException(status_code=404, detail=f"Variable '{key}' not found")
        
        _user_env_vars[user_id] = variables
        logger.info(f"User {user_id} deleted env var: {key}")
        
        return {"message": f"Variable '{key}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting environment variable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_user_env_value(user_id: int, key: str) -> Optional[str]:
    """
    Helper function to get an environment variable value for a user.
    Used by workflow executor to resolve {{$env.KEY}} references.
    """
    variables = _user_env_vars.get(user_id, [])
    for v in variables:
        if v.get("key") == key:
            return v.get("value")
    return None


def get_all_user_env_vars(user_id: int) -> dict[str, str]:
    """
    Helper function to get all environment variables for a user as a dict.
    Used by workflow executor to resolve all {{$env.*}} references.
    """
    variables = _user_env_vars.get(user_id, [])
    return {v.get("key"): v.get("value") for v in variables if v.get("key")}
