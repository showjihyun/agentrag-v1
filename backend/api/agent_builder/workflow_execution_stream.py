"""
Workflow Execution Streaming API
Server-Sent Events (SSE) for real-time workflow execution status
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime

from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.query_helpers import get_workflow_with_relations
from backend.core.auth_dependencies import get_current_user
from backend.services.agent_builder.workflow_executor import WorkflowExecutor

router = APIRouter()


async def execution_event_generator(
    workflow_id: str,
    execution_id: str,
    db: Session,
    current_user: User,
    input_data: dict = None
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for workflow execution status
    
    This generator executes the workflow and streams status updates in real-time.
    
    Event format:
    {
        "node_id": "node-123",
        "node_name": "Process Data",
        "status": "running" | "success" | "failed" | "pending" | "skipped",
        "start_time": 1234567890,
        "end_time": 1234567890,
        "error": "Error message if failed",
        "output": "Node output data",
        "timestamp": 1234567890
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get workflow from database with all relations (prevents N+1 queries)
        workflow = get_workflow_with_relations(db, workflow_id)
        
        if not workflow:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Workflow not found'})}\n\n"
            return
        
        # Initialize workflow executor
        executor = WorkflowExecutor(workflow, db, execution_id)
        
        # Send initial connection event
        logger.info(f"🔌 SSE connected for execution: {execution_id}")
        yield f"data: {json.dumps({'type': 'connected', 'execution_id': execution_id})}\n\n"
        
        # Start workflow execution in background
        execution_task = asyncio.create_task(
            executor.execute(input_data or {})
        )
        
        # Poll for execution status updates
        last_status = {}
        max_iterations = 600  # 10 minutes max (600 * 1 second)
        iteration = 0
        
        while iteration < max_iterations:
            try:
                # Get current execution status
                execution = await executor.get_execution_status(execution_id)
                
                if not execution:
                    logger.warning(f"⚠️ Execution not found: {execution_id}")
                    # Don't break immediately, execution might not have started yet
                    await asyncio.sleep(0.5)
                    iteration += 1
                    continue
                
                # Get node statuses
                node_statuses = execution.get('node_statuses', {})
                
                # Send updates for changed nodes
                for node_id, status in node_statuses.items():
                    # Check if status changed
                    if node_id not in last_status or last_status[node_id] != status:
                        event_data = {
                            'type': 'node_status',
                            'node_id': node_id,
                            'node_name': status.get('node_name', 'Unknown'),
                            'status': status.get('status', 'pending'),
                            'start_time': status.get('start_time'),
                            'end_time': status.get('end_time'),
                            'error': status.get('error'),
                            'output': status.get('output'),
                            'timestamp': datetime.now().timestamp(),
                        }
                        
                        logger.info(f"📨 Sending node status: {node_id} -> {status.get('status')}")
                        yield f"data: {json.dumps(event_data)}\n\n"
                        last_status[node_id] = status
                
                # Check if execution task is done
                if execution_task.done():
                    try:
                        result = execution_task.result()
                        final_status = 'completed' if result.get('success') else 'failed'
                        logger.info(f"✅ Execution completed: {final_status}")
                        yield f"data: {json.dumps({'type': 'completed', 'status': final_status})}\n\n"
                        break
                    except Exception as e:
                        logger.error(f"❌ Execution failed: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                        break
                
                # Check if execution is complete based on status
                if execution.get('status') in ['completed', 'failed', 'cancelled']:
                    logger.info(f"✅ Execution status: {execution.get('status')}")
                    yield f"data: {json.dumps({'type': 'completed', 'status': execution.get('status')})}\n\n"
                    break
                
                # Wait before next poll
                await asyncio.sleep(0.5)  # Poll every 500ms
                iteration += 1
                
            except Exception as e:
                logger.error(f"❌ Error in SSE loop: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
        
        # Send timeout if max iterations reached
        if iteration >= max_iterations:
            logger.warning(f"⏱️ Execution timeout: {execution_id}")
            yield f"data: {json.dumps({'type': 'timeout', 'message': 'Execution timeout'})}\n\n"
            
    except Exception as e:
        logger.error(f"❌ SSE generator error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        # Send close event
        logger.info(f"🔌 SSE disconnected: {execution_id}")
        yield f"data: {json.dumps({'type': 'close'})}\n\n"


@router.get("/workflows/{workflow_id}/executions/{execution_id}/stream")
async def stream_workflow_execution(
    workflow_id: str,
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream workflow execution status via Server-Sent Events (SSE)
    
    Returns:
        StreamingResponse with text/event-stream content type
    """
    
    # Verify workflow exists and user has access
    from backend.db.models.agent_builder import Workflow
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Check permissions (owner or public)
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this workflow execution stream"
        )
    
    logger.info(f"User {current_user.id} accessing execution stream for workflow {workflow_id}")
    
    return StreamingResponse(
        execution_event_generator(workflow_id, execution_id, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_execution_simple(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream workflow execution with automatic execution
    This endpoint both executes the workflow and streams status updates
    """
    
    # Get workflow from database with all relations (prevents N+1 queries)
    workflow = get_workflow_with_relations(db, workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Generate a new execution ID
    import uuid
    execution_id = str(uuid.uuid4())
    
    # Start execution and streaming
    return StreamingResponse(
        execution_event_generator(workflow_id, execution_id, db, current_user, input_data={}),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
