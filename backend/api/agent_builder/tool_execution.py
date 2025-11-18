"""
Tool Execution API endpoints.

Provides endpoints for executing agent tools.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/tools",
    tags=["agent-builder-tool-execution"]
)


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    tool_id: str = Field(..., description="Tool ID to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    tool_id: str
    result: Any = None
    error: str = None
    duration_ms: int


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a tool with given parameters.
    
    **Request:**
    - tool_id: Tool identifier (e.g., 'calculator', 'http_request')
    - parameters: Tool-specific parameters
    - context: Optional execution context
    
    **Returns:**
    - Execution result with success status and data
    
    **Errors:**
    - 400: Invalid parameters
    - 401: Unauthorized
    - 500: Execution failed
    """
    try:
        logger.info(f"Executing tool {request.tool_id} for user {current_user.id}")
        
        # Add user context
        context = {
            **request.context,
            'user_id': str(current_user.id)
        }
        
        # Execute tool
        executor = ToolExecutor()
        result = await executor.execute_tool(
            tool_id=request.tool_id,
            parameters=request.parameters,
            context=context
        )
        
        return ToolExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.post("/test/{tool_id}")
async def test_tool(
    tool_id: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """
    Test a tool with sample parameters.
    
    **Path Parameters:**
    - tool_id: Tool identifier
    
    **Request Body:**
    - parameters: Tool parameters to test
    
    **Returns:**
    - Test execution result
    
    **Errors:**
    - 400: Invalid parameters
    - 401: Unauthorized
    - 404: Tool not found
    """
    try:
        logger.info(f"Testing tool {tool_id} for user {current_user.id}")
        
        context = {'user_id': str(current_user.id)}
        
        executor = ToolExecutor()
        result = await executor.execute_tool(
            tool_id=tool_id,
            parameters=parameters,
            context=context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Tool test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool test failed: {str(e)}"
        )
