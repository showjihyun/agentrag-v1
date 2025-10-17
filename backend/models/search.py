"""Search result models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Represents a search result from vector similarity search."""

    id: str = Field(..., description="Unique identifier for the result")
    document_id: str = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    text: str = Field(..., description="The matched text content")
    score: float = Field(..., description="Similarity score (0-1)")
    chunk_index: int = Field(..., description="Position of chunk in document")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk_123",
                "document_id": "doc_456",
                "document_name": "example.pdf",
                "text": "This is the matched text content.",
                "score": 0.92,
                "chunk_index": 5,
                "metadata": {"page": 2},
            }
        }
