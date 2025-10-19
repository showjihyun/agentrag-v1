"""Hybrid system models for Speculative + Agentic RAG."""

from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from .query import QueryRequest, SearchResult


class QueryMode(str, Enum):
    """Query processing mode for hybrid system.

    - AUTO: Intelligent routing based on query complexity (default)
    - FAST: Speculative path only, returns results within ~2 seconds
    - BALANCED: Both speculative and agentic paths in parallel, progressive refinement
    - DEEP: Agentic path only, full reasoning with comprehensive analysis
    - WEB_SEARCH: RAG + Web Search hybrid mode for comprehensive analysis
    """

    AUTO = "auto"
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"
    WEB_SEARCH = "web_search"


class ResponseType(str, Enum):
    """Type of response chunk in progressive streaming.

    - PRELIMINARY: Initial fast response from speculative path
    - REFINEMENT: Incremental updates from agentic path
    - FINAL: Complete final response
    """

    PRELIMINARY = "preliminary"
    REFINEMENT = "refinement"
    FINAL = "final"


class PathSource(str, Enum):
    """Source path that generated the response.

    - SPECULATIVE: Fast vector search + simple LLM generation
    - AGENTIC: Full ReAct/CoT reasoning with agent orchestration
    - HYBRID: Merged results from both paths
    - WEB_SEARCH: RAG + Web Search combined analysis
    """

    SPECULATIVE = "speculative"
    AGENTIC = "agentic"
    HYBRID = "hybrid"
    WEB_SEARCH = "web_search"


class ResponseChunk(BaseModel):
    """A chunk of streaming response with metadata for progressive display.

    Used for Server-Sent Events (SSE) streaming to provide real-time updates
    as the system processes queries through speculative and agentic paths.
    """

    chunk_id: str = Field(..., description="Unique identifier for this chunk")
    type: ResponseType = Field(..., description="Type of response chunk")
    content: str = Field(..., description="The actual response content")
    path_source: PathSource = Field(..., description="Which path generated this chunk")
    confidence_score: Optional[float] = Field(
        None, description="Confidence score (0-1) for this response", ge=0.0, le=1.0
    )
    sources: List[SearchResult] = Field(
        default_factory=list, description="Source documents used for this chunk"
    )
    reasoning_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent reasoning steps (for agentic path)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this chunk was generated"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (progress, status, etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "chunk_001",
                "type": "preliminary",
                "content": "Based on initial search, machine learning improves accuracy...",
                "path_source": "speculative",
                "confidence_score": 0.75,
                "sources": [],
                "reasoning_steps": [],
                "timestamp": "2024-01-01T12:00:00",
                "metadata": {"cache_hit": False, "search_time_ms": 150},
            }
        }
    )


class HybridQueryRequest(QueryRequest):
    """Extended query request with hybrid system parameters.

    Extends the base QueryRequest with mode selection and hybrid-specific options.
    Maintains backward compatibility - if mode is not specified, defaults to AUTO (intelligent routing).
    """

    mode: QueryMode = Field(
        default=QueryMode.AUTO,
        description="Query processing mode: auto (intelligent routing, default), web_search (web + RAG), fast, balanced, or deep",
    )
    enable_cache: bool = Field(
        default=True, description="Whether to use speculative response caching"
    )
    speculative_timeout: float = Field(
        default=2.0,
        description="Timeout for speculative path in seconds",
        ge=0.5,
        le=5.0,
    )
    agentic_timeout: float = Field(
        default=15.0, description="Timeout for agentic path in seconds", ge=5.0, le=60.0
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the benefits of machine learning?",
                "session_id": "session_abc123",
                "top_k": 10,
                "mode": "balanced",
                "enable_cache": True,
                "speculative_timeout": 2.0,
                "agentic_timeout": 15.0,
                "stream": True,
            }
        }
    )


class HybridQueryResponse(BaseModel):
    """Complete response from hybrid query processing.

    Contains the final merged response with metadata from both paths.
    """

    query_id: str = Field(..., description="Unique identifier for this query")
    query: str = Field(..., description="The original query text")
    mode: QueryMode = Field(..., description="Mode used for processing")
    response: str = Field(..., description="The final generated response")
    confidence_score: float = Field(
        ..., description="Final confidence score (0-1)", ge=0.0, le=1.0
    )
    sources: List[SearchResult] = Field(
        default_factory=list, description="All source documents used"
    )
    reasoning_steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Agent reasoning steps (if agentic path was used)",
    )
    session_id: Optional[str] = Field(None, description="Session ID")
    path_used: PathSource = Field(..., description="Which path(s) were used")
    speculative_time: Optional[float] = Field(
        None, description="Time taken by speculative path in seconds"
    )
    agentic_time: Optional[float] = Field(
        None, description="Time taken by agentic path in seconds"
    )
    total_time: float = Field(..., description="Total processing time in seconds")
    cache_hit: bool = Field(default=False, description="Whether cache was used")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "query_xyz789",
                "query": "What are the benefits of machine learning?",
                "mode": "balanced",
                "response": "Machine learning provides several key benefits...",
                "confidence_score": 0.92,
                "sources": [],
                "reasoning_steps": [],
                "session_id": "session_abc123",
                "path_used": "hybrid",
                "speculative_time": 1.8,
                "agentic_time": 8.5,
                "total_time": 8.5,
                "cache_hit": False,
                "metadata": {},
            }
        }
    )


class SpeculativeResponse(BaseModel):
    """Response from the speculative path.

    Contains the fast initial response with confidence scoring.
    """

    response: str = Field(..., description="The generated response text")
    confidence_score: float = Field(
        ...,
        description="Confidence score based on vector similarity and document count",
        ge=0.0,
        le=1.0,
    )
    sources: List[SearchResult] = Field(
        default_factory=list, description="Source documents from vector search"
    )
    cache_hit: bool = Field(
        default=False, description="Whether response came from cache"
    )
    processing_time: float = Field(..., description="Time taken in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (search stats, etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Based on the documents, machine learning...",
                "confidence_score": 0.78,
                "sources": [],
                "cache_hit": False,
                "processing_time": 1.5,
                "metadata": {"vector_search_time_ms": 120, "llm_time_ms": 1380},
            }
        }
    )


class StaticRAGResponse(BaseModel):
    """Response from the Static RAG pipeline.

    Contains the fast response from pure Static RAG without agent overhead.
    """

    response: str = Field(..., description="The generated response text")
    sources: List[SearchResult] = Field(
        default_factory=list, description="Source documents from vector search"
    )
    confidence_score: float = Field(
        ..., description="Preliminary confidence score (0-1)", ge=0.0, le=1.0
    )
    processing_time: float = Field(..., description="Time taken in seconds")
    cache_hit: bool = Field(
        default=False, description="Whether response came from cache"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (search stats, cache info, etc.)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Machine learning provides several key benefits...",
                "sources": [],
                "confidence_score": 0.82,
                "processing_time": 1.2,
                "cache_hit": False,
                "metadata": {
                    "embedding_time_ms": 50,
                    "search_time_ms": 150,
                    "llm_time_ms": 1000,
                    "num_sources": 5,
                },
            }
        }
    )
