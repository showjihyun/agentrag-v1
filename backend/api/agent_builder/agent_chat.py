"""
Agent Chat API with Knowledgebase Integration.

This module provides chat endpoints for agents with automatic knowledgebase utilization.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.agent_builder import Agent, AgentExecution
from backend.services.speculative_processor import SpeculativeProcessor
from backend.core.dependencies import (
    get_embedding_service,
    get_milvus_manager,
    get_llm_manager,
    get_redis_client
)
from backend.core.rate_limiter_enhanced import get_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/agents",
    tags=["agent-chat"],
)


class ChatMessage(BaseModel):
    """Chat message request"""
    content: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response"""
    answer: str
    confidence: float
    sources: list
    knowledgebases_used: list
    execution_id: str
    processing_time: float
    metadata: Dict[str, Any]


@router.post(
    "/{agent_id}/chat",
    response_model=ChatResponse,
    summary="Chat with agent (KB-aware)",
    description="Send a message to an agent. Automatically uses agent's knowledgebases."
)
async def chat_with_agent(
    agent_id: str,
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    embedding_service = Depends(get_embedding_service),
    milvus_manager = Depends(get_milvus_manager),
    llm_manager = Depends(get_llm_manager),
    redis_client = Depends(get_redis_client),
):
    # Rate limiting: 30 requests per minute per user
    rate_limiter = get_rate_limiter(redis_client)
    rate_limit_key = f"chat:user:{current_user.id}"
    
    allowed = await rate_limiter.check_rate_limit(
        key=rate_limit_key,
        max_requests=30,
        window_seconds=60
    )
    
    if not allowed:
        remaining = await rate_limiter.get_remaining_requests(
            key=rate_limit_key,
            max_requests=30,
            window_seconds=60
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum 30 requests per minute. Try again in a moment."
        )
    """
    Chat with an agent using its knowledgebases.
    
    **Workflow**:
    1. Load agent and its knowledgebases
    2. Run speculative RAG with KB integration
    3. Return fast response with KB attribution
    4. Log execution
    
    **Features**:
    - Automatic KB utilization
    - Fast response (<1s with cache)
    - KB result prioritization
    - Execution tracking
    
    **Request Body**:
    - content: Message text (required)
    - session_id: Optional session ID for conversation context
    - metadata: Optional metadata
    
    **Returns**:
    - answer: Agent's response
    - confidence: Confidence score (0-1)
    - sources: Source documents with KB attribution
    - knowledgebases_used: List of KB IDs used
    - execution_id: Execution record ID
    - processing_time: Time taken (seconds)
    - metadata: Additional metadata
    
    **Errors**:
    - 404: Agent not found
    - 403: No permission to access agent
    - 500: Processing error
    """
    # Input validation
    if not message.content or not message.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    if len(message.content) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message too long (maximum 10,000 characters)"
        )
    
    # Validate agent_id format
    try:
        import uuid
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent ID format"
        )
    
    try:
        logger.info(
            f"Chat request: agent={agent_id}, user={current_user.id}, "
            f"query_len={len(message.content)}, session={message.session_id}"
        )
        
        # 1. Load agent with knowledgebases
        agent = db.query(Agent).options(
            joinedload(Agent.knowledgebases)
        ).filter(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None)
        ).first()
        
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Check permission
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this agent"
            )
        
        # 2. Extract KB IDs
        kb_ids = [str(kb.knowledgebase_id) for kb in agent.knowledgebases]
        
        logger.info(
            f"Processing chat: agent='{agent.name}' (id={agent_id}), "
            f"kb_count={len(kb_ids)}, query='{message.content[:50]}...'"
        )
        
        # 3. Initialize Speculative Processor
        speculative_processor = SpeculativeProcessor(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager,
            redis_client=redis_client,
            cache_ttl=3600,
            cache_prefix="agent_chat:",
        )
        
        # 4. Process with KB integration
        start_time = datetime.utcnow()
        
        result = await speculative_processor.process_with_knowledgebase(
            query=message.content,
            knowledgebase_ids=kb_ids if kb_ids else None,
            session_id=message.session_id,
            top_k=5,
            enable_cache=True
        )
        
        # 5. Create execution record
        execution = AgentExecution(
            id=uuid.uuid4(),
            agent_id=uuid.UUID(agent_id),
            user_id=uuid.UUID(str(current_user.id)),
            session_id=message.session_id or str(uuid.uuid4()),
            input_data={'query': message.content, 'metadata': message.metadata},
            output_data={
                'answer': result.response,
                'confidence': result.confidence_score,
                'sources': result.sources
            },
            execution_context={
                'knowledgebases_used': kb_ids,
                'kb_results_count': result.metadata.get('kb_results_count', 0),
                'cache_hit': result.cache_hit,
                'search_method': result.metadata.get('search_method', 'unknown')
            },
            status='completed',
            started_at=start_time,
            completed_at=datetime.utcnow(),
            duration_ms=int(result.processing_time * 1000)
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        logger.info(
            f"Chat completed: execution_id={execution.id}, "
            f"agent='{agent.name}', "
            f"confidence={result.confidence_score:.3f}, "
            f"kb_count={len(kb_ids)}, "
            f"kb_results={result.metadata.get('kb_results_count', 0)}, "
            f"cache_hit={result.cache_hit}, "
            f"time={result.processing_time:.3f}s"
        )
        
        # 6. Build response
        return ChatResponse(
            answer=result.response,
            confidence=result.confidence_score,
            sources=result.sources,
            knowledgebases_used=kb_ids,
            execution_id=str(execution.id),
            processing_time=result.processing_time,
            metadata={
                **result.metadata,
                'agent_id': agent_id,
                'agent_name': agent.name,
                'cache_hit': result.cache_hit,
                'session_id': message.session_id
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid input for chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Chat processing failed: agent={agent_id}, "
            f"user={current_user.id}, error={str(e)}",
            exc_info=True
        )
        
        # Try to log failed execution
        try:
            execution = AgentExecution(
                id=uuid.uuid4(),
                agent_id=uuid.UUID(agent_id),
                user_id=uuid.UUID(str(current_user.id)),
                session_id=message.session_id or str(uuid.uuid4()),
                input_data={'query': message.content},
                output_data={},
                execution_context={
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                status='failed',
                started_at=start_time if 'start_time' in locals() else datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
            db.add(execution)
            db.commit()
            logger.info(f"Logged failed execution: {execution.id}")
        except Exception as log_error:
            logger.error(f"Failed to log execution error: {log_error}")
        
        # Return user-friendly error message
        error_detail = "An error occurred while processing your message"
        if "timeout" in str(e).lower():
            error_detail = "Request timed out. Please try again."
        elif "connection" in str(e).lower():
            error_detail = "Service temporarily unavailable. Please try again."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get(
    "/{agent_id}/chat/history",
    summary="Get chat history",
    description="Retrieve chat history for an agent session"
)
async def get_chat_history(
    agent_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for an agent.
    
    **Query Parameters**:
    - session_id: Optional session ID to filter
    - limit: Maximum number of messages (default: 50)
    
    **Returns**:
    - List of chat executions with messages
    """
    try:
        # Check agent access
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None)
        ).first()
        
        if not agent:
            raise HTTPException(404, "Agent not found")
        
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(403, "No permission")
        
        # Query executions
        query = db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.user_id == current_user.id
        )
        
        if session_id:
            query = query.filter(AgentExecution.session_id == session_id)
        
        executions = query.order_by(
            AgentExecution.started_at.desc()
        ).limit(limit).all()
        
        # Format response
        history = []
        for exec in executions:
            history.append({
                'execution_id': str(exec.id),
                'session_id': exec.session_id,
                'query': exec.input_data.get('query', ''),
                'answer': exec.output_data.get('answer', ''),
                'confidence': exec.output_data.get('confidence', 0),
                'status': exec.status,
                'started_at': exec.started_at.isoformat() if exec.started_at else None,
                'duration_ms': exec.duration_ms,
                'kb_count': len(exec.execution_context.get('knowledgebases_used', [])),
                'cache_hit': exec.execution_context.get('cache_hit', False)
            })
        
        return {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'session_id': session_id,
            'total': len(history),
            'history': history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve chat history")
