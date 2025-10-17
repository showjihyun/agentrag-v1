"""Query request and response models."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SearchResult(BaseModel):
    """Represents a search result from vector database."""

    chunk_id: str = Field(..., description="ID of the matching chunk")
    document_id: str = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    text: str = Field(..., description="The matching text content")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "doc123_chunk_5",
                "document_id": "doc123",
                "document_name": "research_paper.pdf",
                "text": "Machine learning models require large datasets for training.",
                "score": 0.92,
                "metadata": {"page": 3, "section": "Methodology"},
            }
        }
    )


class QueryRequest(BaseModel):
    """Request model for query processing."""

    query: str = Field(..., description="The user's query text", min_length=1)
    session_id: Optional[UUID] = Field(
        None, description="Session ID for conversation context"
    )
    top_k: int = Field(
        default=10, description="Number of results to retrieve", ge=1, le=50
    )
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Optional filters for search"
    )
    stream: bool = Field(default=True, description="Whether to stream the response")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the main findings about machine learning?",
                "session_id": "session_abc123",
                "top_k": 10,
                "filters": {"document_type": "pdf"},
                "stream": True,
            }
        }
    )


class QueryResponse(BaseModel):
    """Response model for query processing."""

    query_id: str = Field(..., description="Unique identifier for this query")
    query: str = Field(..., description="The original query text")
    response: str = Field(..., description="The generated response")
    sources: List[SearchResult] = Field(
        default_factory=list, description="Source documents used"
    )
    reasoning_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent reasoning steps"
    )
    session_id: Optional[UUID] = Field(None, description="Session ID")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "query_xyz789",
                "query": "What are the main findings?",
                "response": "The main findings indicate that...",
                "sources": [],
                "reasoning_steps": [],
                "session_id": "session_abc123",
                "processing_time": 2.5,
                "metadata": {},
            }
        }
    )
