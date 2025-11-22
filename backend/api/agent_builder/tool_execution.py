"""
Tool execution API endpoints.
"""
from typing import Any, Dict, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import ToolExecution, ToolCredential, ToolUsageMetric
from backend.db.database import get_db
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry
from backend.models.error import ErrorResponse

router = APIRouter(prefix="/api/agent-builder/tool-execution", tags=["tool-execution"])


class ToolExecutionRequest(BaseModel):
    """Tool execution request."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool configuration")


class ToolExecutionResponse(BaseModel):
    """Tool execution response."""
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float | None = None


@router.post(
    "/execute",
    response_model=ToolExecutionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ToolExecutionResponse:
    """
    Execute a tool with given parameters and save execution history.
    
    Args:
        request: Tool execution request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Tool execution response
    """
    import time
    import uuid
    
    start_time = time.time()
    started_at = datetime.utcnow()
    
    try:
        # Get executor first (before creating DB record)
        executor = ToolExecutorRegistry.get_executor(request.tool_name)
        
        if not executor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {request.tool_name}",
            )
        
        # Verify tool exists in database (for FK constraint)
        from backend.db.models.agent_builder import Tool
        tool = db.query(Tool).filter(Tool.id == request.tool_name).first()
        if not tool:
            # Tool exists in registry but not in DB - skip execution record
            result = await executor.execute_with_error_handling(
                params=request.parameters,
                credentials=request.config
            )
            execution_time = time.time() - start_time
            
            return ToolExecutionResponse(
                success=result.success,
                result=result.output,
                error=result.error,
                execution_time=execution_time,
            )
        
        # Create execution record (only if tool exists in DB)
        execution_record = ToolExecution(
            id=uuid.uuid4(),
            tool_id=request.tool_name,
            user_id=current_user.id,
            parameters=request.parameters,
            credentials_used=bool(request.config),
            started_at=started_at,
            success=False,  # Will update after execution
        )
        
        # Execute tool
        result = await executor.execute_with_error_handling(
            params=request.parameters,
            credentials=request.config
        )
        
        execution_time = time.time() - start_time
        
        # Update execution record
        execution_record.success = result.success
        execution_record.output = result.output
        execution_record.error = result.error
        execution_record.execution_time = execution_time
        execution_record.completed_at = datetime.utcnow()
        
        db.add(execution_record)
        db.commit()
        
        return ToolExecutionResponse(
            success=result.success,
            result=result.output,
            error=result.error,
            execution_time=execution_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Update execution record with error
        execution_record.success = False
        execution_record.error = str(e)
        execution_record.execution_time = execution_time
        execution_record.completed_at = datetime.utcnow()
        
        db.add(execution_record)
        db.commit()
        
        return ToolExecutionResponse(
            success=False,
            error=str(e),
            execution_time=execution_time,
        )


@router.get("/available-tools")
async def get_available_tools(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get list of available tools by category.
    
    Returns:
        Dictionary of category -> tool names
    """
    executors = ToolExecutorRegistry.list_executors()
    
    # Group by category
    by_category: Dict[str, list[str]] = {}
    for tool_id, executor in executors.items():
        category = getattr(executor, 'category', 'other')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool_id)
    
    return by_category


@router.post("/validate")
async def validate_tool_config(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate tool configuration without executing.
    
    Args:
        request: Tool execution request
        current_user: Current authenticated user
        
    Returns:
        Validation result
    """
    try:
        executor = ToolExecutorRegistry.get_executor(request.tool_name)
        
        if not executor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {request.tool_name}",
            )
        
        # Try to validate by executing with dry-run
        try:
            executor.validate_params(request.parameters, [])
            return {
                "valid": True,
                "tool_name": request.tool_name,
                "message": "Configuration is valid",
            }
        except ValueError as ve:
            return {
                "valid": False,
                "tool_name": request.tool_name,
                "message": str(ve),
            }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "valid": False,
            "tool_name": request.tool_name,
            "message": str(e),
        }



class ToolExecutionHistoryResponse(BaseModel):
    """Tool execution history response."""
    id: str
    tool_id: str
    success: bool
    execution_time: float | None
    started_at: str
    completed_at: str | None
    error: str | None
    parameters: Dict[str, Any] | None


@router.get("/history")
async def get_execution_history(
    tool_id: Optional[str] = Query(None, description="Filter by tool ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get tool execution history for the current user.
    
    Args:
        tool_id: Optional tool ID filter
        success: Optional success status filter
        limit: Maximum number of results
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Execution history with pagination info
    """
    # Build query
    query = db.query(ToolExecution).filter(
        ToolExecution.user_id == current_user.id
    )
    
    if tool_id:
        query = query.filter(ToolExecution.tool_id == tool_id)
    
    if success is not None:
        query = query.filter(ToolExecution.success == success)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    executions = query.order_by(desc(ToolExecution.started_at)).offset(offset).limit(limit).all()
    
    # Format response
    history = [
        ToolExecutionHistoryResponse(
            id=str(exec.id),
            tool_id=exec.tool_id,
            success=exec.success,
            execution_time=exec.execution_time,
            started_at=exec.started_at.isoformat(),
            completed_at=exec.completed_at.isoformat() if exec.completed_at else None,
            error=exec.error,
            parameters=exec.parameters,
        )
        for exec in executions
    ]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "history": [h.model_dump() for h in history],
    }


class ToolCredentialCreate(BaseModel):
    """Tool credential creation request."""
    tool_id: str
    name: str
    credentials: Dict[str, Any]


class ToolCredentialResponse(BaseModel):
    """Tool credential response."""
    id: str
    tool_id: str
    name: str
    is_active: bool
    last_used_at: str | None
    created_at: str


@router.post("/credentials")
async def create_credential(
    request: ToolCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ToolCredentialResponse:
    """
    Save tool credentials for the current user.
    
    Args:
        request: Credential creation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created credential info
    """
    import uuid
    
    # Check if credential with same name already exists
    existing = db.query(ToolCredential).filter(
        and_(
            ToolCredential.user_id == current_user.id,
            ToolCredential.tool_id == request.tool_id,
            ToolCredential.name == request.name,
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credential with name '{request.name}' already exists for this tool",
        )
    
    # Encrypt credentials before storing
    from backend.core.security import get_encryption
    encryption = get_encryption()
    encrypted_credentials = encryption.encrypt_credentials(request.credentials)
    
    # Create credential
    credential = ToolCredential(
        id=uuid.uuid4(),
        user_id=current_user.id,
        tool_id=request.tool_id,
        name=request.name,
        credentials={"encrypted": encrypted_credentials},  # Store encrypted
        is_active=True,
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    return ToolCredentialResponse(
        id=str(credential.id),
        tool_id=credential.tool_id,
        name=credential.name,
        is_active=credential.is_active,
        last_used_at=credential.last_used_at.isoformat() if credential.last_used_at else None,
        created_at=credential.created_at.isoformat(),
    )


@router.get("/credentials")
async def list_credentials(
    tool_id: Optional[str] = Query(None, description="Filter by tool ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ToolCredentialResponse]:
    """
    List tool credentials for the current user.
    
    Args:
        tool_id: Optional tool ID filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of credentials
    """
    query = db.query(ToolCredential).filter(
        ToolCredential.user_id == current_user.id,
        ToolCredential.is_active == True,
    )
    
    if tool_id:
        query = query.filter(ToolCredential.tool_id == tool_id)
    
    credentials = query.order_by(desc(ToolCredential.created_at)).all()
    
    return [
        ToolCredentialResponse(
            id=str(cred.id),
            tool_id=cred.tool_id,
            name=cred.name,
            is_active=cred.is_active,
            last_used_at=cred.last_used_at.isoformat() if cred.last_used_at else None,
            created_at=cred.created_at.isoformat(),
        )
        for cred in credentials
    ]


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Delete a tool credential.
    
    Args:
        credential_id: Credential ID to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    import uuid
    
    try:
        cred_uuid = uuid.UUID(credential_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credential ID format",
        )
    
    credential = db.query(ToolCredential).filter(
        and_(
            ToolCredential.id == cred_uuid,
            ToolCredential.user_id == current_user.id,
        )
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )
    
    db.delete(credential)
    db.commit()
    
    return {"message": "Credential deleted successfully"}


@router.get("/metrics")
async def get_tool_metrics(
    tool_id: Optional[str] = Query(None, description="Filter by tool ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get tool usage metrics for the current user.
    
    Args:
        tool_id: Optional tool ID filter
        days: Number of days to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Usage metrics
    """
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = db.query(ToolExecution).filter(
        and_(
            ToolExecution.user_id == current_user.id,
            ToolExecution.started_at >= start_date,
        )
    )
    
    if tool_id:
        query = query.filter(ToolExecution.tool_id == tool_id)
    
    # Get aggregated metrics
    total_executions = query.count()
    successful_executions = query.filter(ToolExecution.success == True).count()
    failed_executions = query.filter(ToolExecution.success == False).count()
    
    # Get average execution time
    avg_time_result = query.filter(
        ToolExecution.execution_time.isnot(None)
    ).with_entities(
        func.avg(ToolExecution.execution_time)
    ).scalar()
    
    avg_execution_time = float(avg_time_result) if avg_time_result else 0.0
    
    # Get executions by tool
    by_tool = db.query(
        ToolExecution.tool_id,
        func.count(ToolExecution.id).label('count'),
        func.avg(ToolExecution.execution_time).label('avg_time'),
    ).filter(
        and_(
            ToolExecution.user_id == current_user.id,
            ToolExecution.started_at >= start_date,
        )
    ).group_by(ToolExecution.tool_id).all()
    
    tools_metrics = [
        {
            "tool_id": tool_id,
            "execution_count": count,
            "avg_execution_time": float(avg_time) if avg_time else 0.0,
        }
        for tool_id, count, avg_time in by_tool
    ]
    
    return {
        "period_days": days,
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0.0,
        "avg_execution_time": avg_execution_time,
        "by_tool": tools_metrics,
    }



def decrypt_tool_credentials(credential: ToolCredential) -> Dict[str, Any]:
    """
    Decrypt tool credentials.
    
    Args:
        credential: ToolCredential model instance
        
    Returns:
        Decrypted credentials dictionary
    """
    from backend.core.security import get_encryption
    
    if not credential.credentials:
        return {}
    
    # Check if credentials are encrypted
    if isinstance(credential.credentials, dict) and "encrypted" in credential.credentials:
        encryption = get_encryption()
        return encryption.decrypt_credentials(credential.credentials["encrypted"])
    
    # Legacy: unencrypted credentials (for backward compatibility)
    return credential.credentials
