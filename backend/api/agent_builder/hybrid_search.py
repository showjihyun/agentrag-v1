"""
Hybrid Search API endpoints.

Provides REST API for hybrid vector + knowledge graph search functionality.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.hybrid_search_service import HybridSearchService
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/hybrid-search", tags=["Hybrid Search"])


class HybridSearchRequest(BaseModel):
    """Schema for hybrid search request."""
    
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    search_strategy: str = Field(default="hybrid", description="Search strategy: vector, graph, hybrid, auto")
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for vector search")
    graph_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for graph search")
    include_entities: bool = Field(default=True, description="Include entity matches")
    include_relationships: bool = Field(default=True, description="Include relationship matches")
    entity_expansion_depth: int = Field(default=1, ge=0, le=3, description="Depth for entity expansion")


class EntityContextRequest(BaseModel):
    """Schema for entity context request."""
    
    entity_id: str = Field(..., description="Entity ID")
    context_depth: int = Field(default=2, ge=1, le=3, description="Context depth")


class EntityPathRequest(BaseModel):
    """Schema for entity path finding request."""
    
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum path depth")


class HybridSearchResponse(BaseModel):
    """Schema for hybrid search response."""
    
    documents: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/{knowledgebase_id}/search", response_model=HybridSearchResponse)
async def hybrid_search(
    knowledgebase_id: str,
    request: HybridSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform hybrid search combining vector and knowledge graph results."""
    
    try:
        service = HybridSearchService(db)
        
        results = await service.search(
            knowledgebase_id=knowledgebase_id,
            query=request.query,
            limit=request.limit,
            search_strategy=request.search_strategy,
            vector_weight=request.vector_weight,
            graph_weight=request.graph_weight,
            include_entities=request.include_entities,
            include_relationships=request.include_relationships,
            entity_expansion_depth=request.entity_expansion_depth,
        )
        
        return HybridSearchResponse(**results)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in hybrid search: {str(e)}")
        raise HTTPException(status_code=500, detail="Hybrid search failed")


@router.post("/{knowledgebase_id}/entity-context")
async def get_entity_context(
    knowledgebase_id: str,
    request: EntityContextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get rich context for an entity including related entities and relationships."""
    
    try:
        service = HybridSearchService(db)
        
        context = await service.get_entity_context(
            knowledgebase_id=knowledgebase_id,
            entity_id=request.entity_id,
            context_depth=request.context_depth,
        )
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting entity context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get entity context")


@router.post("/{knowledgebase_id}/entity-paths")
async def find_entity_paths(
    knowledgebase_id: str,
    request: EntityPathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find paths between two entities in the knowledge graph."""
    
    try:
        service = HybridSearchService(db)
        
        paths = await service.find_entity_paths(
            knowledgebase_id=knowledgebase_id,
            source_entity_id=request.source_entity_id,
            target_entity_id=request.target_entity_id,
            max_depth=request.max_depth,
        )
        
        return {
            "paths": paths,
            "source_entity_id": request.source_entity_id,
            "target_entity_id": request.target_entity_id,
            "max_depth": request.max_depth,
        }
        
    except Exception as e:
        logger.error(f"Error finding entity paths: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to find entity paths")


@router.get("/{knowledgebase_id}/search-strategies")
async def get_search_strategies(
    knowledgebase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get available search strategies for a knowledgebase."""
    
    from backend.db.models.agent_builder import Knowledgebase
    
    # Check knowledgebase exists and get configuration
    kb = db.query(Knowledgebase).filter(
        Knowledgebase.id == knowledgebase_id,
        Knowledgebase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledgebase not found")
    
    strategies = [
        {
            "value": "vector",
            "label": "Vector Search",
            "description": "Semantic similarity search using embeddings",
            "available": True,
        }
    ]
    
    if kb.kg_enabled:
        strategies.extend([
            {
                "value": "graph",
                "label": "Knowledge Graph",
                "description": "Entity and relationship-based search",
                "available": True,
            },
            {
                "value": "hybrid",
                "label": "Hybrid Search",
                "description": "Combined vector and knowledge graph search",
                "available": True,
            },
            {
                "value": "auto",
                "label": "Auto Strategy",
                "description": "Automatically choose the best strategy",
                "available": True,
            },
        ])
    
    return {
        "strategies": strategies,
        "default_strategy": kb.search_strategy or "vector",
        "kg_enabled": kb.kg_enabled,
        "kb_type": kb.kb_type or "vector",
    }


@router.get("/{knowledgebase_id}/search-config")
async def get_search_config(
    knowledgebase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get search configuration for a knowledgebase."""
    
    from backend.db.models.agent_builder import Knowledgebase
    
    # Check knowledgebase exists and get configuration
    kb = db.query(Knowledgebase).filter(
        Knowledgebase.id == knowledgebase_id,
        Knowledgebase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledgebase not found")
    
    return {
        "knowledgebase_id": knowledgebase_id,
        "kb_type": kb.kb_type or "vector",
        "search_strategy": kb.search_strategy or "vector",
        "kg_enabled": kb.kg_enabled,
        "hybrid_weight_vector": kb.hybrid_weight_vector or 0.7,
        "hybrid_weight_graph": kb.hybrid_weight_graph or 0.3,
        "embedding_model": kb.embedding_model,
        "kg_entity_extraction_model": kb.kg_entity_extraction_model,
        "kg_relation_extraction_model": kb.kg_relation_extraction_model,
        "kg_auto_extraction": kb.kg_auto_extraction,
    }