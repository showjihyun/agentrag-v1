"""Query processing API endpoints with streaming support."""

import logging
import json
import uuid
import asyncio
from typing import AsyncGenerator, Optional, Dict
from datetime import datetime
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.agents.aggregator import AggregatorAgent
from backend.memory.manager import MemoryManager
from backend.models.query import QueryRequest, QueryResponse
from backend.models.hybrid import HybridQueryRequest, QueryMode, ResponseChunk
from backend.models.agent import AgentStep, AgentState
from backend.services.llm_manager import LLMManager
from backend.core.auth_dependencies import get_optional_user
from backend.core.dependencies import (
    get_aggregator_agent,
    get_memory_manager,
    get_hybrid_query_router,
    get_intelligent_mode_router,
    get_llm_manager,
)
from backend.db.models.user import User
from backend.db.database import get_db
from backend.services.intelligent_mode_router import (
    IntelligentModeRouter,
    RoutingDecision,
)
from backend.services.source_highlighter import get_source_highlighter
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["query"])


# Rate Limiting (메모리 기반)
class RateLimiter:
    """간단한 메모리 기반 Rate Limiter"""
    
    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.window = 60  # 60초 윈도우
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Rate limit 체크. True면 허용, False면 거부"""
        now = time()
        
        # 윈도우 밖의 요청 제거
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip] 
            if now - t < self.window
        ]
        
        # 제한 확인
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            return False
        
        # 요청 기록
        self.request_counts[client_ip].append(now)
        return True
    
    def get_remaining(self, client_ip: str) -> int:
        """남은 요청 수 반환"""
        now = time()
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip] 
            if now - t < self.window
        ]
        return max(0, self.requests_per_minute - len(self.request_counts[client_ip]))


# Rate Limiter 인스턴스
rate_limiter = RateLimiter(requests_per_minute=20)


def serialize_for_json(obj):
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        return serialize_for_json(obj.model_dump())
    elif hasattr(obj, "__dict__"):
        return serialize_for_json(obj.__dict__)
    return obj


# Response models
class StreamChunk(BaseModel):
    """Single chunk in the streaming response."""

    type: str = Field(..., description="Chunk type: step, response, error, done")
    data: dict = Field(..., description="Chunk data")
    timestamp: str = Field(..., description="Timestamp")


class QueryComplexityRequest(BaseModel):
    """Request model for query complexity analysis."""

    query: str = Field(..., description="Query text to analyze", min_length=1)


class QueryStatusResponse(BaseModel):
    """Response model for query status."""

    query_id: str = Field(..., description="Query identifier")
    status: str = Field(..., description="Query status")
    session_id: str | None = Field(None, description="Session identifier")
    created_at: str = Field(..., description="Creation timestamp")


async def stream_agent_response(
    query: str,
    session_id: str,
    aggregator_agent: AggregatorAgent,
    memory_manager: MemoryManager,
    user: User | None = None,
    db: Session | None = None,
    top_k: int = 10,
) -> AsyncGenerator[str, None]:
    """
    Stream agent processing steps as Server-Sent Events.

    Yields SSE-formatted messages with agent steps and final response.

    If user is authenticated, saves messages to database.
    """
    query_id = str(uuid.uuid4())
    start_time = datetime.now()

    # Buffer for accumulating response content
    response_buffer = []
    sources_list = []
    confidence_score = None
    cache_hit = False
    cache_match_type = None
    cache_similarity = None

    try:
        logger.info(f"Starting query processing: {query_id}")

        # Save user message if authenticated
        conversation_service = None
        db_session = None
        if user is not None and db is not None:
            try:
                from backend.services.conversation_service import ConversationService

                conversation_service = ConversationService(db)

                # Get or create session
                db_session = conversation_service.get_or_create_session(
                    user_id=user.id,
                    session_id=uuid.UUID(session_id) if session_id else None,
                )

                # Save user message before processing
                conversation_service.save_message_with_sources(
                    session_id=db_session.id,
                    user_id=user.id,
                    role="user",
                    content=query,
                    sources=None,
                    metadata={},
                )

                logger.info(f"Saved user message for session {db_session.id}")
            except Exception as e:
                logger.error(f"Failed to save user message: {e}", exc_info=True)
                # Continue processing even if database save fails

        # Send initial status
        yield f"data: {json.dumps({'type': 'status', 'data': {'status': 'processing', 'query_id': query_id}, 'timestamp': datetime.now().isoformat()})}\n\n"

        # Process query through aggregator agent
        async for step in aggregator_agent.process_query(
            query=query, session_id=session_id, top_k=top_k
        ):
            # Convert AgentStep to dict
            step_data = {
                "step_id": step.step_id,
                "type": step.type,
                "content": step.content,
                "timestamp": step.timestamp.isoformat(),
                "metadata": step.metadata,
            }

            # Accumulate response content
            if step.type == "response":
                response_buffer.append(step.content)

            # Extract sources from metadata
            if "sources" in step.metadata:
                step_sources = step.metadata.get("sources", [])
                if isinstance(step_sources, list):
                    sources_list.extend(step_sources)
            
            # Apply source highlighting if response is available
            if step.type == "response" and response_buffer and sources_list:
                try:
                    highlighter = get_source_highlighter()
                    accumulated_response = "\n".join(response_buffer)
                    highlighted_sources = highlighter.highlight_sources(
                        answer=accumulated_response,
                        sources=sources_list,
                        method="auto"
                    )
                    # Update sources with highlights
                    sources_list = highlighted_sources
                    # Update step metadata with highlighted sources
                    step_data["metadata"]["sources"] = serialize_for_json(highlighted_sources)
                except Exception as e:
                    logger.warning(f"Failed to highlight sources: {e}")
                    # Continue without highlighting

            # Extract confidence score
            if "confidence_score" in step.metadata:
                confidence_score = step.metadata.get("confidence_score")

            # Extract cache information
            if "cache_hit" in step.metadata:
                cache_hit = step.metadata.get("cache_hit", False)
            if "cache_match_type" in step.metadata:
                cache_match_type = step.metadata.get("cache_match_type")
            if "cache_similarity" in step.metadata:
                cache_similarity = step.metadata.get("cache_similarity")

            # Send step as SSE
            chunk = StreamChunk(
                type="step", data=step_data, timestamp=datetime.now().isoformat()
            )

            yield f"data: {chunk.model_dump_json()}\n\n"

            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)

        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        processing_time_ms = int(processing_time * 1000)

        # Save assistant message if authenticated
        if (
            user is not None
            and conversation_service is not None
            and db_session is not None
        ):
            try:
                # Combine accumulated response
                accumulated_response = (
                    "\n".join(response_buffer)
                    if response_buffer
                    else "No response generated"
                )

                # Prepare sources for database
                db_sources = []
                for source in sources_list:
                    if isinstance(source, dict):
                        db_sources.append(
                            {
                                "document_id": source.get("document_id", ""),
                                "document_name": source.get("document_name", ""),
                                "chunk_id": source.get("chunk_id", ""),
                                "score": source.get("score", 0.0),
                                "text": source.get("text", ""),
                            }
                        )

                # Prepare metadata
                message_metadata = {
                    "query_mode": "agentic",  # Legacy mode
                    "processing_time_ms": processing_time_ms,
                    "query_id": query_id,
                }

                if confidence_score is not None:
                    message_metadata["confidence_score"] = confidence_score
                if cache_hit:
                    message_metadata["cache_hit"] = cache_hit
                if cache_match_type:
                    message_metadata["cache_match_type"] = cache_match_type
                if cache_similarity is not None:
                    message_metadata["cache_similarity"] = cache_similarity

                # Save assistant message with sources
                conversation_service.save_message_with_sources(
                    session_id=db_session.id,
                    user_id=user.id,
                    role="assistant",
                    content=accumulated_response,
                    sources=db_sources if db_sources else None,
                    metadata=message_metadata,
                )

                logger.info(
                    f"Saved assistant message with {len(db_sources)} sources "
                    f"for session {db_session.id}"
                )
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}", exc_info=True)
                # Continue even if database save fails

        # Send completion message
        completion_data = {
            "query_id": query_id,
            "session_id": session_id,
            "processing_time": processing_time,
            "status": "completed",
        }

        yield f"data: {json.dumps({'type': 'done', 'data': completion_data, 'timestamp': datetime.now().isoformat()})}\n\n"

        logger.info(f"Query processing completed: {query_id} in {processing_time:.2f}s")

    except asyncio.CancelledError:
        logger.info(f"Query processing cancelled: {query_id}")
        yield f"data: {json.dumps({'type': 'error', 'data': {'error': 'Query processing cancelled'}, 'timestamp': datetime.now().isoformat()})}\n\n"

    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)

        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "query_id": query_id,
        }

        yield f"data: {json.dumps({'type': 'error', 'data': error_data, 'timestamp': datetime.now().isoformat()})}\n\n"


async def stream_web_search_response(
    query: str,
    session_id: str,
    user: User | None = None,
    db: Session | None = None,
    top_k: int = 10,
) -> AsyncGenerator[str, None]:
    """
    Stream Web Search + RAG hybrid response.
    
    Combines internal RAG search with external web search for comprehensive answers.
    """
    query_id = str(uuid.uuid4())
    
    try:
        from backend.agents.web_search_agent import get_web_search_agent
        
        logger.info(f"Starting Web Search + RAG hybrid query: '{query[:50]}...'")
        
        # Get Web Search Agent
        web_search_agent = await get_web_search_agent()
        
        # Save user message to database if authenticated
        if user and db:
            try:
                from backend.db.models.conversation import Message, MessageRole
                from backend.db.models.conversation import Conversation
                
                # Get or create conversation
                conversation = (
                    db.query(Conversation)
                    .filter(Conversation.session_id == session_id)
                    .first()
                )
                
                if not conversation:
                    conversation = Conversation(
                        session_id=session_id,
                        user_id=user.id,
                        title=query[:100],
                    )
                    db.add(conversation)
                    db.flush()
                
                # Save user message
                user_message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=query,
                )
                db.add(user_message)
                db.commit()
                
            except Exception as e:
                logger.warning(f"Failed to save user message: {e}")
                db.rollback()
        
        # Process query through Web Search Agent
        response_buffer = []
        sources = []
        
        async for chunk in web_search_agent.process_query(
            query=query,
            session_id=session_id,
            top_k=top_k,
            web_results=5
        ):
            chunk_type = chunk.get("type")
            chunk_data = chunk.get("data", {})
            
            # Forward chunk to client
            yield f"data: {json.dumps({'type': chunk_type, 'data': chunk_data, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Collect response content
            if chunk_type == "response":
                content = chunk_data.get("content", "")
                if content:
                    response_buffer.append(content)
            
            # Collect sources
            if chunk_type == "final":
                sources = chunk_data.get("sources", [])
        
        # Save assistant message to database if authenticated
        if user and db and response_buffer:
            try:
                full_response = "".join(response_buffer)
                
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    metadata={
                        "query_id": query_id,
                        "mode": "web_search",
                        "sources": sources,
                    },
                )
                db.add(assistant_message)
                db.commit()
                
            except Exception as e:
                logger.warning(f"Failed to save assistant message: {e}")
                db.rollback()
        
        logger.info("Web Search + RAG query completed")
        
    except asyncio.CancelledError:
        logger.info("Web Search query cancelled")
        yield f"data: {json.dumps({'type': 'error', 'data': {'error': 'Query processing cancelled'}, 'timestamp': datetime.now().isoformat()})}\n\n"
    
    except Exception as e:
        logger.error(f"Web Search query failed: {e}", exc_info=True)
        error_data = {"error": str(e), "error_type": type(e).__name__}
        yield f"data: {json.dumps({'type': 'error', 'data': error_data, 'timestamp': datetime.now().isoformat()})}\n\n"


async def stream_hybrid_response(
    query: str,
    session_id: str,
    mode: QueryMode,
    user: User | None = None,
    db: Session | None = None,
    top_k: int = 10,
    enable_cache: bool = True,
    speculative_timeout: Optional[float] = None,
    agentic_timeout: Optional[float] = None,
    routing_decision: Optional[RoutingDecision] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream hybrid query response with progressive updates.

    Supports three modes:
    - FAST: Speculative path only (~2s)
    - BALANCED: Both paths with progressive refinement (~5s)
    - DEEP: Agentic path only with full reasoning (~10s+)

    Yields SSE-formatted messages with:
    - Preliminary responses (speculative path)
    - Refinement updates (agentic path)
    - Final merged response
    - Confidence scores and metadata

    If user is authenticated, saves messages to database.

    Requirements: 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, 5.6, 6.2, 6.3, 6.4
    """
    start_time = datetime.now()
    final_chunk = None

    try:
        hybrid_router = await get_hybrid_query_router()

        logger.info(
            f"Starting hybrid query in {mode.value.upper()} mode: '{query[:50]}...'"
        )

        # Save user message if authenticated
        conversation_service = None
        db_session = None
        if user is not None and db is not None:
            try:
                from backend.services.conversation_service import ConversationService

                conversation_service = ConversationService(db)

                # Get or create session
                db_session = conversation_service.get_or_create_session(
                    user_id=user.id,
                    session_id=uuid.UUID(session_id) if session_id else None,
                )

                # Save user message before processing
                conversation_service.save_message_with_sources(
                    session_id=db_session.id,
                    user_id=user.id,
                    role="user",
                    content=query,
                    sources=None,
                    metadata={},
                )

                logger.info(f"Saved user message for session {db_session.id}")
            except Exception as e:
                logger.error(f"Failed to save user message: {e}", exc_info=True)
                # Continue processing even if database save fails

        # Process query through hybrid router
        async for chunk in hybrid_router.process_query(
            query=query,
            mode=mode,
            session_id=session_id,
            top_k=top_k,
            enable_cache=enable_cache,
            speculative_timeout=speculative_timeout,
            agentic_timeout=agentic_timeout,
        ):
            # Store final chunk for database saving
            if chunk.type.value == "final":
                final_chunk = chunk

            # Apply source highlighting for final responses
            highlighted_sources = chunk.sources
            if chunk.type.value == "final" and chunk.content and chunk.sources:
                try:
                    highlighter = get_source_highlighter()
                    sources_for_highlighting = [
                        source.model_dump() if hasattr(source, "model_dump") else source
                        for source in chunk.sources
                    ]
                    highlighted_sources_list = highlighter.highlight_sources(
                        answer=chunk.content,
                        sources=sources_for_highlighting,
                        method="auto"
                    )
                    # Convert back to source objects if needed
                    highlighted_sources = highlighted_sources_list
                    logger.info(f"Applied source highlighting: {sum(s.get('highlight_count', 0) for s in highlighted_sources_list)} total highlights")
                except Exception as e:
                    logger.warning(f"Failed to highlight sources: {e}")
                    # Continue without highlighting

            # Convert ResponseChunk to SSE format
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "type": chunk.type.value,
                "content": chunk.content,
                "path_source": chunk.path_source.value,
                "confidence_score": chunk.confidence_score,
                "sources": serialize_for_json(
                    [source.model_dump() if hasattr(source, "model_dump") else source for source in highlighted_sources]
                ),
                "reasoning_steps": serialize_for_json(chunk.reasoning_steps),
                "timestamp": chunk.timestamp.isoformat(),
                "metadata": serialize_for_json(chunk.metadata),
            }

            # Add routing metadata if available
            if routing_decision:
                chunk_data["routing"] = {
                    "mode_used": routing_decision.mode.value,
                    "complexity": routing_decision.complexity.value,
                    "complexity_score": routing_decision.complexity_score,
                    "routing_confidence": routing_decision.routing_confidence,
                    "forced": routing_decision.forced,
                }

            # Determine SSE event type based on response type
            if chunk.type.value == "preliminary":
                event_type = "preliminary"
            elif chunk.type.value == "refinement":
                event_type = "refinement"
            elif chunk.type.value == "final":
                event_type = "final"
            else:
                event_type = "chunk"

            # Send as SSE
            yield f"data: {json.dumps({'type': event_type, 'data': chunk_data, 'timestamp': datetime.now().isoformat()})}\n\n"

            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)

        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        processing_time_ms = int(processing_time * 1000)

        # Save assistant message if authenticated
        if (
            user is not None
            and conversation_service is not None
            and db_session is not None
            and final_chunk is not None
        ):
            try:
                # Prepare sources for database
                db_sources = []
                for source in final_chunk.sources:
                    source_dict = (
                        source.model_dump() if hasattr(source, "model_dump") else source
                    )
                    db_sources.append(
                        {
                            "document_id": source_dict.get("document_id", ""),
                            "document_name": source_dict.get("document_name", ""),
                            "chunk_id": source_dict.get("chunk_id", ""),
                            "score": source_dict.get("score", 0.0),
                            "text": source_dict.get("text", ""),
                        }
                    )

                # Prepare metadata
                message_metadata = {
                    "query_mode": mode.value,
                    "processing_time_ms": processing_time_ms,
                    "confidence_score": final_chunk.confidence_score,
                    "path_source": final_chunk.path_source.value,
                }

                # Add cache information if available
                if final_chunk.metadata:
                    if "cache_hit" in final_chunk.metadata:
                        message_metadata["cache_hit"] = final_chunk.metadata[
                            "cache_hit"
                        ]
                    if "cache_match_type" in final_chunk.metadata:
                        message_metadata["cache_match_type"] = final_chunk.metadata[
                            "cache_match_type"
                        ]
                    if "cache_similarity" in final_chunk.metadata:
                        message_metadata["cache_similarity"] = final_chunk.metadata[
                            "cache_similarity"
                        ]

                # Save assistant message with sources
                conversation_service.save_message_with_sources(
                    session_id=db_session.id,
                    user_id=user.id,
                    role="assistant",
                    content=final_chunk.content,
                    sources=db_sources if db_sources else None,
                    metadata=message_metadata,
                )

                logger.info(
                    f"Saved assistant message with {len(db_sources)} sources "
                    f"for session {db_session.id}"
                )
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}", exc_info=True)
                # Continue even if database save fails

        logger.info(f"Hybrid query completed in {mode.value.upper()} mode")

    except asyncio.CancelledError:
        logger.info(f"Hybrid query cancelled")
        yield f"data: {json.dumps({'type': 'error', 'data': {'error': 'Query processing cancelled'}, 'timestamp': datetime.now().isoformat()})}\n\n"

    except Exception as e:
        logger.error(f"Hybrid query failed: {e}", exc_info=True)

        error_data = {"error": str(e), "error_type": type(e).__name__}

        yield f"data: {json.dumps({'type': 'error', 'data': error_data, 'timestamp': datetime.now().isoformat()})}\n\n"


@router.post("/", response_class=StreamingResponse)
async def process_query(
    http_request: Request,
    request: HybridQueryRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
    aggregator_agent: AggregatorAgent = Depends(lambda: None),
    memory_manager: MemoryManager = Depends(lambda: None),
):
    """
    Process a user query with streaming response and intelligent routing.

    Supports both legacy (agentic-only) and hybrid (speculative + agentic) modes
    with intelligent query-complexity-based routing.

    **Query Modes:**
    - `auto`: Intelligent routing based on query complexity (default) - NEW!
    - `fast`: Speculative path only, returns results within ~2 seconds
    - `balanced`: Both paths in parallel with progressive refinement (~5s)
    - `deep`: Agentic path only with full reasoning (~10s+)

    **Intelligent Routing (AUTO mode):**
    When mode is set to 'auto' (default), the system automatically selects the
    optimal processing mode based on query complexity analysis:
    - Simple queries (score < 0.35) ??FAST mode (<1s)
    - Medium queries (0.35 ??score ??0.70) ??BALANCED mode (<3s)
    - Complex queries (score > 0.70) ??DEEP mode (<15s)

    **Routing Metadata:**
    All responses include routing metadata:
    - `mode_used`: Actual mode executed (fast/balanced/deep)
    - `complexity`: Query complexity level (simple/medium/complex)
    - `complexity_score`: Normalized complexity score (0.0-1.0)
    - `routing_confidence`: Confidence in routing decision (0.0-1.0)
    - `forced`: Whether mode was explicitly specified by user

    **Backward Compatibility:**
    - Accepts both QueryRequest and HybridQueryRequest formats (Requirements: 12.2, 12.3)
    - If `mode` is not specified, defaults to 'auto' (intelligent routing)
    - When ENABLE_SPECULATIVE_RAG=false, always uses agentic-only mode
    - Old QueryRequest format works without any changes
    - Existing clients continue to work without modifications
    - New fields (mode, enable_cache, timeouts) are optional extensions

    **Response Stream:**
    Returns a Server-Sent Events (SSE) stream with:
    - Preliminary responses (fast initial results) - only in hybrid mode
    - Refinement updates (progressive improvements) - only in hybrid mode
    - Agent reasoning steps (thoughts, actions, observations)
    - Final merged response with sources
    - Confidence scores and metadata

    The stream sends JSON objects with the following structure:
    ```json
    {
        "type": "preliminary|refinement|final|step|error",
        "data": {
            "chunk_id": "unique_id",
            "type": "preliminary|refinement|final",
            "content": "response text",
            "path_source": "speculative|agentic|hybrid",
            "confidence_score": 0.85,
            "sources": [...],
            "reasoning_steps": [...],
            "metadata": {...}
        },
        "timestamp": "ISO-8601 timestamp"
    }
    ```

    **Event Types:**
    - `preliminary`: Initial fast response from speculative path (hybrid mode only)
    - `refinement`: Incremental updates from agentic path (hybrid mode only)
    - `step`: Agent reasoning step (legacy and hybrid modes)
    - `final`: Complete final response
    - `error`: Error occurred

    **Legacy Mode (ENABLE_SPECULATIVE_RAG=false):**
    When hybrid mode is disabled, the endpoint behaves exactly like the original
    agentic-only system, streaming only agent reasoning steps and final response.

    Example usage:
    ```javascript
    // Intelligent routing (AUTO mode - recommended)
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: 'What are the benefits of machine learning?',
            mode: 'auto',  // or omit for default intelligent routing
            session_id: 'session_123'
        })
    });

    // Explicit mode selection
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: 'What are the benefits of machine learning?',
            mode: 'balanced',  // force specific mode
            session_id: 'session_123'
        })
    });

    // Legacy request (still works, uses AUTO mode)
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: 'What are the benefits of machine learning?',
            session_id: 'session_123'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const chunk = JSON.parse(decoder.decode(value));

        // Access routing metadata
        if (chunk.data.routing) {
            console.log('Mode used:', chunk.data.routing.mode_used);
            console.log('Complexity:', chunk.data.routing.complexity);
            console.log('Complexity score:', chunk.data.routing.complexity_score);
            console.log('Routing confidence:', chunk.data.routing.routing_confidence);
        }

        console.log(chunk.type, chunk.data);
    }
    ```

    Requirements: 6.5, 6.10, 12.2, 12.3
    """
    try:
        # Rate Limiting 체크
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not rate_limiter.check_rate_limit(client_ip):
            remaining = rate_limiter.get_remaining(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {60 - int(time() % 60)} seconds.",
                headers={"X-RateLimit-Remaining": str(remaining)}
            )
        
        # Validate request
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
            )

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Determine if hybrid mode is enabled and available
        hybrid_enabled = settings.ENABLE_SPECULATIVE_RAG
        hybrid_router = None

        if hybrid_enabled:
            try:
                hybrid_router = await get_hybrid_query_router()
                if hybrid_router is None:
                    logger.warning(
                        "Hybrid mode enabled but router not initialized, falling back to legacy mode"
                    )
                    hybrid_enabled = False
            except Exception as e:
                logger.warning(
                    f"Hybrid router not available, falling back to legacy mode: {e}"
                )
                hybrid_enabled = False

        # Initialize routing decision variable
        routing_decision = None

        # Get mode - use intelligent routing if AUTO mode, otherwise use specified mode
        if hybrid_enabled:
            # Get mode from request or use AUTO (intelligent routing)
            requested_mode = getattr(request, "mode", QueryMode.AUTO)

            # If AUTO mode, use IntelligentModeRouter for routing
            if requested_mode == QueryMode.AUTO:
                try:
                    mode_router = await get_intelligent_mode_router()

                    # Route query to optimal mode
                    routing_decision = await mode_router.route_query(
                        query=request.query,
                        session_id=session_id,
                        user_prefs=None,  # Could be extracted from user profile
                        forced_mode=None,
                        language="auto",
                    )

                    mode = routing_decision.mode

                    logger.info(
                        f"Intelligent routing: {mode.value.upper()} mode selected "
                        f"(complexity={routing_decision.complexity.value}, "
                        f"score={routing_decision.complexity_score:.3f}, "
                        f"confidence={routing_decision.routing_confidence:.3f})"
                    )
                except Exception as e:
                    logger.error(
                        f"Intelligent routing failed, falling back to BALANCED: {e}",
                        exc_info=True,
                    )
                    mode = QueryMode.BALANCED
            else:
                # Use explicitly specified mode
                mode = requested_mode
                logger.info(f"Using explicitly specified mode: {mode.value.upper()}")
        else:
            # Hybrid disabled - always use DEEP mode (agentic-only)
            mode = QueryMode.DEEP

        logger.info(
            f"Received query request: '{request.query[:50]}...' "
            f"(session: {session_id}, mode: {mode.value}, hybrid_enabled: {hybrid_enabled})"
        )

        # Route to appropriate handler based on mode
        if mode == QueryMode.WEB_SEARCH:
            # Use Web Search + RAG hybrid mode
            logger.info("Using Web Search + RAG hybrid mode")
            
            from backend.agents.web_search_agent import get_web_search_agent
            
            return StreamingResponse(
                stream_web_search_response(
                    query=request.query,
                    session_id=session_id,
                    user=user,
                    db=db,
                    top_k=request.top_k,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        elif hybrid_enabled and hybrid_router is not None:
            # Use hybrid query router (Requirements: 12.1, 12.4)
            logger.info(f"Using hybrid query router in {mode.value.upper()} mode")

            # Use routing decision's top_k if available, otherwise use request's top_k
            top_k = routing_decision.top_k if routing_decision else request.top_k

            return StreamingResponse(
                stream_hybrid_response(
                    query=request.query,
                    session_id=session_id,
                    mode=mode,
                    user=user,
                    db=db,
                    top_k=top_k,
                    enable_cache=getattr(request, "enable_cache", True),
                    speculative_timeout=getattr(request, "speculative_timeout", None),
                    agentic_timeout=getattr(request, "agentic_timeout", None),
                    routing_decision=routing_decision,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable buffering in nginx
                },
            )
        else:
            # Fall back to legacy agentic-only mode (Requirements: 12.1, 12.4)
            # This ensures backward compatibility when ENABLE_SPECULATIVE_RAG=false
            logger.info(
                "Using legacy agentic-only mode (hybrid disabled or unavailable)"
            )
            aggregator_agent = await get_aggregator_agent()
            memory_manager = await get_memory_manager()

            return StreamingResponse(
                stream_agent_response(
                    query=request.query,
                    session_id=session_id,
                    aggregator_agent=aggregator_agent,
                    memory_manager=memory_manager,
                    user=user,
                    db=db,
                    top_k=request.top_k,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}",
        )


@router.post("/sync", response_model=QueryResponse)
async def process_query_sync(
    request: QueryRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
    aggregator_agent: AggregatorAgent = Depends(lambda: None),
    memory_manager: MemoryManager = Depends(lambda: None),
):
    """
    Process a user query with synchronous response (non-streaming).

    This endpoint waits for the complete response before returning.
    Use the streaming endpoint (`POST /api/query`) for real-time updates.

    Returns the complete query response with all reasoning steps and sources.
    """
    try:
        aggregator_agent = await get_aggregator_agent()
        memory_manager = await get_memory_manager()

        # Validate request
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
            )

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        query_id = str(uuid.uuid4())

        logger.info(
            f"Received sync query request: '{request.query[:50]}...' (session: {session_id})"
        )

        start_time = datetime.now()

        # Collect all steps
        reasoning_steps = []
        final_response = None
        sources = []

        async for step in aggregator_agent.process_query(
            query=request.query, session_id=session_id, top_k=request.top_k
        ):
            reasoning_steps.append(
                {
                    "step_id": step.step_id,
                    "type": step.type,
                    "content": step.content,
                    "timestamp": step.timestamp.isoformat(),
                    "metadata": step.metadata,
                }
            )

            # Extract final response
            if step.type == "response":
                final_response = step.content

            # Extract sources from metadata
            if "sources" in step.metadata:
                sources.extend(step.metadata["sources"])

        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        logger.info(f"Sync query completed: {query_id} in {processing_time:.2f}s")

        return QueryResponse(
            query_id=query_id,
            query=request.query,
            response=final_response or "No response generated",
            sources=sources,
            reasoning_steps=reasoning_steps,
            session_id=session_id,
            processing_time=processing_time,
            metadata={"top_k": request.top_k, "filters": request.filters},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process sync query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}",
        )


@router.get("/{query_id}", response_model=QueryStatusResponse)
async def get_query_status(
    query_id: str, memory_manager: MemoryManager = Depends(lambda: None)
):
    """
    Get the status of a query.

    This endpoint can be used to check if a query is still processing
    or to retrieve metadata about a completed query.

    Note: This is a placeholder implementation. Full query history
    tracking would require additional storage.
    """
    try:
        memory_manager = await get_memory_manager()

        logger.info(f"Getting status for query: {query_id}")

        # This is a simplified implementation
        # In a production system, you would store query metadata in Redis or a database

        return QueryStatusResponse(
            query_id=query_id,
            status="unknown",
            session_id=None,
            created_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to get query status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query status: {str(e)}",
        )


# Adaptive Mode Selection Endpoint
@router.post("/analyze-complexity")
async def analyze_query_complexity(request: QueryComplexityRequest) -> dict:
    """
    Analyze query complexity and recommend optimal processing mode.

    This endpoint uses the QueryComplexityAnalyzer to:
    - Analyze query structure, keywords, and length
    - Classify complexity level (simple/moderate/complex)
    - Recommend optimal mode (FAST/BALANCED/DEEP)
    - Provide reasoning for the recommendation

    Args:
        request: Request with 'query' field

    Returns:
        Dictionary with:
        - recommended_mode: Suggested QueryMode
        - complexity_level: Complexity classification
        - confidence: Confidence in recommendation (0-1)
        - reasoning: Detailed analysis breakdown
        - explanation: Human-readable explanation

    Example:
        POST /api/query/analyze-complexity
        {
            "query": "Compare supervised and unsupervised learning"
        }

        Response:
        {
            "recommended_mode": "deep",
            "complexity_level": "complex",
            "confidence": 0.85,
            "reasoning": {
                "complexity_score": 0.78,
                "length_score": 0.5,
                "keyword_score": 0.9,
                "structure_score": 0.4,
                "question_type_score": 0.9,
                "factors": [
                    "Contains analytical keywords (compare, analyze)",
                    "Analytical question type"
                ]
            },
            "explanation": "Recommended DEEP mode (~10-15s): Your query requires comprehensive analysis..."
        }
    """
    from backend.services.query_complexity_analyzer import get_analyzer

    # Extract query from request
    query = request.query

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query field is required"
        )

    # Analyze complexity
    analyzer = get_analyzer()
    complexity_level, recommended_mode, confidence, reasoning = analyzer.analyze(query)

    # Get explanation
    explanation = analyzer.get_mode_explanation(recommended_mode, reasoning)

    return {
        "recommended_mode": recommended_mode.value,
        "complexity_level": complexity_level.value,
        "confidence": confidence,
        "reasoning": reasoning,
        "explanation": explanation,
    }


# Update the main query endpoint to support auto mode recommendation
class QueryWithAutoMode(HybridQueryRequest):
    """Extended query request with auto mode option"""

    auto_mode: bool = Field(
        default=False,
        description="If true, automatically select mode based on query complexity",
    )


@router.post("/auto", response_class=StreamingResponse)
async def process_query_auto_mode(
    request: QueryWithAutoMode,
    aggregator_agent: AggregatorAgent = Depends(get_aggregator_agent),
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> StreamingResponse:
    """
    Process query with automatic mode selection.

    If auto_mode is True, analyzes query complexity and selects optimal mode.
    Otherwise, uses the specified mode (or default BALANCED).

    This provides a seamless UX where users don't need to manually select modes
    for most queries, but can still override if desired.

    Args:
        request: Query request with auto_mode flag
        aggregator_agent: Injected aggregator agent
        memory_manager: Injected memory manager

    Returns:
        StreamingResponse with SSE events

    Example:
        POST /api/query/auto
        {
            "query": "What is machine learning?",
            "auto_mode": true
        }

        The system will analyze the query, determine it's simple,
        and automatically use FAST mode for quick response.
    """
    from backend.services.query_complexity_analyzer import get_analyzer

    # Determine mode
    if request.auto_mode:
        # Analyze and recommend mode
        analyzer = get_analyzer()
        complexity_level, recommended_mode, confidence, reasoning = analyzer.analyze(
            request.query
        )

        mode = recommended_mode

        logger.info(
            f"Auto-selected {mode.value.upper()} mode for query "
            f"(complexity: {complexity_level.value}, confidence: {confidence:.2f})"
        )
    else:
        # Use specified mode or default
        mode = request.mode or QueryMode.BALANCED
        logger.info(f"Using user-specified {mode.value.upper()} mode")

    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Stream response
    return StreamingResponse(
        stream_hybrid_response(
            query=request.query,
            session_id=session_id,
            mode=mode,
            top_k=request.options.top_k if request.options else 10,
            enable_cache=True,
            speculative_timeout=(
                request.options.speculative_timeout if request.options else None
            ),
            agentic_timeout=(
                request.options.agentic_timeout if request.options else None
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# Related Questions Generation Endpoint
class RelatedQuestionsRequest(BaseModel):
    """Request model for generating related questions."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: list[str] = Field(default_factory=list, description="Source document names")


class RelatedQuestionsResponse(BaseModel):
    """Response model for related questions."""
    questions: list[str] = Field(..., description="List of related questions")
    generated_at: str = Field(..., description="Generation timestamp")


@router.post("/related-questions", response_model=RelatedQuestionsResponse)
async def generate_related_questions(
    request: RelatedQuestionsRequest,
    llm_manager: LLMManager = Depends(get_llm_manager),
) -> RelatedQuestionsResponse:
    """
    Generate related follow-up questions based on the query and answer.
    
    This helps users continue the conversation naturally by suggesting
    relevant questions they might want to ask next.
    
    Args:
        request: Request with query, answer, and sources
        llm_manager: LLM manager for generating questions
        
    Returns:
        List of 3-5 related questions
    """
    try:
        logger.info(f"Generating related questions for query: {request.query[:50]}...")
        
        # Create prompt for generating related questions
        prompt = f"""Based on the following question and answer, generate 4 related follow-up questions that a user might want to ask next.

Original Question: {request.query}

Answer: {request.answer[:500]}...

{"Sources: " + ", ".join(request.sources[:3]) if request.sources else ""}

Generate 4 specific, relevant follow-up questions that:
1. Dive deeper into specific aspects mentioned in the answer
2. Ask for examples or practical applications
3. Compare or contrast related concepts
4. Explore implications or consequences

Format: Return only the questions, one per line, without numbering or bullets.
"""

        # Generate questions using LLM
        response = await llm_manager.generate(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant follow-up questions to help users explore topics more deeply."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        # Parse questions from response
        questions = [
            q.strip() 
            for q in response.split('\n') 
            if q.strip() and len(q.strip()) > 10 and '?' in q
        ]
        
        # Limit to 4 questions
        questions = questions[:4]
        
        # Fallback if generation failed
        if len(questions) < 2:
            questions = [
                "Can you explain this in more detail?",
                "What are some practical examples?",
                "How does this compare to related concepts?",
                "What are the implications of this?",
            ]
        
        logger.info(f"Generated {len(questions)} related questions")
        
        return RelatedQuestionsResponse(
            questions=questions,
            generated_at=datetime.now().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Failed to generate related questions: {e}", exc_info=True)
        # Return fallback questions instead of error
        return RelatedQuestionsResponse(
            questions=[
                "Can you provide more details about this?",
                "What are some examples?",
                "How can this be applied in practice?",
            ],
            generated_at=datetime.now().isoformat(),
        )
