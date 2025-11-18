"""Chat API endpoints for workflow triggers."""

import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import Workflow
from backend.db.query_helpers import get_workflow_with_relations
from backend.core.triggers.manager import TriggerManager
from backend.core.triggers.chat import ChatTrigger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Chat message request schema."""
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""
    response: str
    session_id: str
    execution_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/{workflow_id}/message")
async def send_chat_message(
    workflow_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message to a workflow.
    
    This endpoint sends a message to a workflow's chat interface and
    returns the workflow's response.
    
    Args:
        workflow_id: Workflow identifier
        request: Chat message request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Chat response
    """
    logger.info(
        f"Received chat message for workflow {workflow_id} "
        f"from user {current_user.id}"
    )
    
    try:
        # Get workflow with all relations (prevents N+1 queries)
        workflow = get_workflow_with_relations(db, workflow_id)
        
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            logger.warning(
                f"User {current_user.id} does not have permission "
                f"to access workflow {workflow_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this workflow"
            )
        
        # Create chat trigger instance
        chat_trigger = ChatTrigger(
            workflow_id=workflow_id,
            config={
                "session_id": request.session_id,
                "enable_streaming": False,  # Non-streaming for REST API
                "max_history": 10,
            },
            db_session=db
        )
        
        # Handle message
        message_result = chat_trigger.handle_message(
            message=request.message,
            user_id=str(current_user.id),
            metadata=request.metadata
        )
        
        if not message_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to handle message: {message_result.get('error')}"
            )
        
        # Execute workflow
        trigger_manager = TriggerManager(db)
        result = await trigger_manager.execute_trigger(
            workflow_id=workflow_id,
            trigger_type="chat",
            trigger_data=message_result.get("trigger_data"),
            user_id=str(current_user.id)
        )
        
        if result.get("success"):
            # Extract response from workflow outputs
            outputs = result.get("outputs", {})
            
            # Try to find response in outputs
            response_text = None
            if isinstance(outputs, dict):
                # Look for common response keys
                for key in ["response", "output", "result", "message"]:
                    if key in outputs:
                        response_text = str(outputs[key])
                        break
                
                # If no common key found, use first output value
                if not response_text and outputs:
                    response_text = str(next(iter(outputs.values())))
            
            if not response_text:
                response_text = "Workflow executed successfully"
            
            # Add response to conversation history
            chat_trigger.add_response(
                response=response_text,
                metadata={"execution_id": result.get("execution_id")}
            )
            
            logger.info(
                f"Chat message processed successfully: workflow_id={workflow_id}, "
                f"execution_id={result.get('execution_id')}"
            )
            
            return ChatMessageResponse(
                response=response_text,
                session_id=chat_trigger.session_id,
                execution_id=result.get("execution_id"),
                metadata={"status": result.get("status")}
            )
        else:
            logger.error(
                f"Workflow execution failed: workflow_id={workflow_id}, "
                f"error={result.get('error')}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {result.get('error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Chat message handler error: workflow_id={workflow_id}, "
            f"error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{workflow_id}/history")
async def get_chat_history(
    workflow_id: str,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat conversation history for a workflow.
    
    Args:
        workflow_id: Workflow identifier
        session_id: Optional session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Conversation history
    """
    logger.info(
        f"Fetching chat history for workflow {workflow_id}, "
        f"session_id={session_id}"
    )
    
    try:
        # Get workflow with all relations (prevents N+1 queries)
        workflow = get_workflow_with_relations(db, workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this workflow"
            )
        
        # TODO: Implement persistent chat history storage
        # For now, return empty history
        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "history": [],
            "message": "Chat history not yet implemented"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get chat history: workflow_id={workflow_id}, "
            f"error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.websocket("/{workflow_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat with workflow.
    
    This endpoint provides streaming chat responses via WebSocket.
    
    Args:
        websocket: WebSocket connection
        workflow_id: Workflow identifier
        db: Database session
    """
    await websocket.accept()
    
    logger.info(f"WebSocket connection established for workflow {workflow_id}")
    
    try:
        # Get workflow with all relations (prevents N+1 queries)
        workflow = get_workflow_with_relations(db, workflow_id)
        
        if not workflow:
            await websocket.send_json({
                "error": "Workflow not found"
            })
            await websocket.close()
            return
        
        # Create chat trigger instance
        chat_trigger = ChatTrigger(
            workflow_id=workflow_id,
            config={
                "enable_streaming": True,
                "max_history": 10,
            },
            db_session=db
        )
        
        # Register chat trigger
        await chat_trigger.register()
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": chat_trigger.session_id,
            "workflow_id": workflow_id
        })
        
        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message = data.get("message")
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "error": "Message is required"
                })
                continue
            
            logger.info(f"Received WebSocket message for workflow {workflow_id}")
            
            # Handle message
            message_result = chat_trigger.handle_message(
                message=message,
                user_id=data.get("user_id"),
                metadata=data.get("metadata")
            )
            
            if not message_result.get("success"):
                await websocket.send_json({
                    "type": "error",
                    "error": message_result.get("error")
                })
                continue
            
            # Execute workflow
            trigger_manager = TriggerManager(db)
            result = await trigger_manager.execute_trigger(
                workflow_id=workflow_id,
                trigger_type="chat",
                trigger_data=message_result.get("trigger_data"),
                user_id=str(workflow.user_id)
            )
            
            if result.get("success"):
                # Extract response
                outputs = result.get("outputs", {})
                response_text = None
                
                if isinstance(outputs, dict):
                    for key in ["response", "output", "result", "message"]:
                        if key in outputs:
                            response_text = str(outputs[key])
                            break
                    
                    if not response_text and outputs:
                        response_text = str(next(iter(outputs.values())))
                
                if not response_text:
                    response_text = "Workflow executed successfully"
                
                # Add response to history
                chat_trigger.add_response(response_text)
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "response": response_text,
                    "execution_id": result.get("execution_id"),
                    "session_id": chat_trigger.session_id
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": result.get("error")
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")
    except Exception as e:
        logger.error(
            f"WebSocket error for workflow {workflow_id}: {str(e)}",
            exc_info=True
        )
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
