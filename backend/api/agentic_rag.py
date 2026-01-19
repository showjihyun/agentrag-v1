"""
Agentic RAG API Endpoints

Provides REST API for Agentic RAG functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agentic_rag_service import AgenticRAGService
from backend.services.llm_manager import LLMManager
from backend.services.embedding_service import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agentic-rag", tags=["Agentic RAG"])


# Request/Response Models
class AgenticRAGQueryRequest(BaseModel):
    """Request model for agentic RAG query."""
    query: str = Field(..., description="User query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base to search")
    strategy: str = Field("adaptive", description="Retrieval strategy: adaptive, hybrid, vector_only, web_only")
    top_k: int = Field(10, ge=1, le=50, description="Number of documents to retrieve")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class SourceResponse(BaseModel):
    """Response model for a source."""
    content: str
    metadata: Dict[str, Any]
    source_type: str
    relevance_score: float
    url: Optional[str] = None


class AgenticRAGQueryResponse(BaseModel):
    """Response model for agentic RAG query."""
    answer: str
    sources: List[SourceResponse]
    metadata: Dict[str, Any]


class QueryComplexityResponse(BaseModel):
    """Response model for query complexity analysis."""
    query: str
    complexity: str
    recommended_strategy: str
    estimated_execution_time: float


class QueryDecompositionResponse(BaseModel):
    """Response model for query decomposition."""
    original_query: str
    sub_queries: List[Dict[str, Any]]
    total_sub_queries: int


# Dependency to get Agentic RAG Service
async def get_agentic_rag_service() -> AgenticRAGService:
    """Get Agentic RAG Service instance."""
    from backend.core.dependencies import (
        get_llm_manager,
        get_embedding_service,
        get_milvus_manager,
    )
    
    llm_manager = get_llm_manager()
    embedding_service = get_embedding_service()
    milvus_manager = get_milvus_manager()
    
    return AgenticRAGService(
        llm_manager=llm_manager,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )


@router.post("/query", response_model=AgenticRAGQueryResponse)
async def agentic_rag_query(
    request: AgenticRAGQueryRequest,
    current_user: User = Depends(get_current_user),
    service: AgenticRAGService = Depends(get_agentic_rag_service),
):
    """
    Execute Agentic RAG query with intelligent retrieval.
    
    Features:
    - Automatic query complexity analysis
    - Query decomposition for complex queries
    - Multi-source retrieval (vector, web, local)
    - Iterative retrieval with quality validation
    - Response synthesis with reflection
    """
    try:
        result = await service.execute_query(
            query=request.query,
            user_id=str(current_user.id),
            strategy=request.strategy,
            top_k=request.top_k,
            context=request.context or {},
        )
        
        # Format response
        return AgenticRAGQueryResponse(
            answer=result.get("answer", ""),
            sources=[
                SourceResponse(
                    content=src.get("content", ""),
                    metadata=src.get("metadata", {}),
                    source_type=src.get("source_type", "unknown"),
                    relevance_score=src.get("relevance_score", 0.0),
                    url=src.get("url"),
                )
                for src in result.get("sources", [])
            ],
            metadata={
                "query_complexity": result.get("query_complexity"),
                "sub_queries": result.get("sub_queries", []),
                "confidence_score": result.get("confidence_score", 0.0),
                "reflection_history": result.get("reflection_history", []),
                "total_sources": result.get("total_sources", 0),
                "execution_time": result.get("execution_time", 0.0),
            }
        )
        
    except Exception as e:
        logger.error(f"Agentic RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-complexity", response_model=QueryComplexityResponse)
async def analyze_query_complexity(
    query: str = Query(..., description="Query to analyze"),
    current_user: User = Depends(get_current_user),
    service: AgenticRAGService = Depends(get_agentic_rag_service),
):
    """
    Analyze query complexity without executing full RAG.
    
    Returns complexity level and recommended strategy.
    """
    try:
        result = await service.analyze_complexity(query=query)
        
        return QueryComplexityResponse(
            query=result.get("query", query),
            complexity=result.get("complexity", "simple"),
            recommended_strategy=result.get("recommended_strategy", "adaptive"),
            estimated_execution_time=result.get("estimated_execution_time", 1.0),
        )
        
    except Exception as e:
        logger.error(f"Complexity analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decompose-query", response_model=QueryDecompositionResponse)
async def decompose_query(
    query: str = Query(..., description="Query to decompose"),
    current_user: User = Depends(get_current_user),
    service: AgenticRAGService = Depends(get_agentic_rag_service),
):
    """
    Decompose complex query into sub-queries.
    
    Useful for understanding how the system will process a complex query.
    """
    try:
        result = await service.decompose_query(query=query)
        
        return QueryDecompositionResponse(
            original_query=result.get("original_query", query),
            sub_queries=result.get("sub_queries", []),
            total_sub_queries=result.get("total_sub_queries", 0),
        )
        
    except Exception as e:
        logger.error(f"Query decomposition failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_user),
    service: AgenticRAGService = Depends(get_agentic_rag_service),
):
    """
    Get Agentic RAG usage statistics.
    
    Returns metrics about query performance and usage.
    """
    try:
        stats = service.get_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
