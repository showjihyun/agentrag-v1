"""
Knowledge Graph API endpoints.

Provides REST API for knowledge graph operations including entity search,
relationship discovery, path finding, and graph visualization.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.knowledge_graph import KnowledgeGraph, EntityType, RelationType
from backend.services.agent_builder.knowledge_graph_service import KnowledgeGraphService
from backend.models.agent_builder import (
    KnowledgeGraphCreateRequest,
    KnowledgeGraphResponse,
    KGEntitySearchRequest,
    KGEntitySearchResponse,
    KGRelationshipSearchRequest,
    KGRelationshipSearchResponse,
    KGPathFindingRequest,
    KGPathFindingResponse,
    KGSubgraphRequest,
    KGSubgraphResponse,
    KGExtractionJobResponse,
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/knowledge-graphs", tags=["Knowledge Graphs"])


@router.get("", response_model=List[KnowledgeGraphResponse])
async def list_knowledge_graphs(
    knowledgebase_id: Optional[UUID] = Query(None, description="Filter by knowledgebase ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List knowledge graphs, optionally filtered by knowledgebase."""
    
    query = db.query(KnowledgeGraph).filter(KnowledgeGraph.user_id == current_user.id)
    
    if knowledgebase_id:
        query = query.filter(KnowledgeGraph.knowledgebase_id == knowledgebase_id)
    
    kgs = query.order_by(KnowledgeGraph.created_at.desc()).all()
    
    return [
        KnowledgeGraphResponse(
            id=str(kg.id),
            knowledgebase_id=str(kg.knowledgebase_id),
            name=kg.name,
            description=kg.description,
            auto_extraction_enabled=kg.auto_extraction_enabled,
            entity_extraction_model=kg.entity_extraction_model,
            relation_extraction_model=kg.relation_extraction_model,
            entity_count=kg.entity_count,
            relationship_count=kg.relationship_count,
            processing_status=kg.processing_status,
            processing_error=kg.processing_error,
            last_processed_at=kg.last_processed_at,
            created_at=kg.created_at,
            updated_at=kg.updated_at,
        )
        for kg in kgs
    ]


@router.post("", response_model=KnowledgeGraphResponse)
async def create_knowledge_graph(
    request: KnowledgeGraphCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge graph for a knowledgebase."""
    
    try:
        service = KnowledgeGraphService(db)
        
        kg = await service.create_knowledge_graph(
            knowledgebase_id=str(request.knowledgebase_id),
            user_id=str(current_user.id),
            name=request.name,
            description=request.description,
            auto_extraction_enabled=request.auto_extraction_enabled,
            entity_extraction_model=request.entity_extraction_model,
            relation_extraction_model=request.relation_extraction_model,
        )
        
        return KnowledgeGraphResponse(
            id=str(kg.id),
            knowledgebase_id=str(kg.knowledgebase_id),
            name=kg.name,
            description=kg.description,
            auto_extraction_enabled=kg.auto_extraction_enabled,
            entity_extraction_model=kg.entity_extraction_model,
            relation_extraction_model=kg.relation_extraction_model,
            entity_count=kg.entity_count,
            relationship_count=kg.relationship_count,
            processing_status=kg.processing_status,
            processing_error=kg.processing_error,
            last_processed_at=kg.last_processed_at,
            created_at=kg.created_at,
            updated_at=kg.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating knowledge graph: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create knowledge graph")


@router.get("/{kg_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    kg_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get knowledge graph details."""
    
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    return KnowledgeGraphResponse(
        id=str(kg.id),
        knowledgebase_id=str(kg.knowledgebase_id),
        name=kg.name,
        description=kg.description,
        auto_extraction_enabled=kg.auto_extraction_enabled,
        entity_extraction_model=kg.entity_extraction_model,
        relation_extraction_model=kg.relation_extraction_model,
        entity_count=kg.entity_count,
        relationship_count=kg.relationship_count,
        processing_status=kg.processing_status,
        processing_error=kg.processing_error,
        last_processed_at=kg.last_processed_at,
        created_at=kg.created_at,
        updated_at=kg.updated_at,
    )


@router.post("/{kg_id}/entities/search", response_model=KGEntitySearchResponse)
async def search_entities(
    kg_id: UUID,
    request: KGEntitySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for entities in the knowledge graph."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KnowledgeGraphService(db)
        
        entities = await service.search_entities(
            kg_id=str(kg_id),
            query=request.query,
            entity_types=request.entity_types,
            limit=request.limit,
        )
        
        return KGEntitySearchResponse(
            entities=entities,
            total_count=len(entities),
            query=request.query,
            entity_types=request.entity_types,
        )
        
    except Exception as e:
        logger.error(f"Error searching entities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search entities")


@router.post("/{kg_id}/relationships/search", response_model=KGRelationshipSearchResponse)
async def search_relationships(
    kg_id: UUID,
    request: KGRelationshipSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for relationships in the knowledge graph."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KnowledgeGraphService(db)
        
        relationships = await service.find_relationships(
            kg_id=str(kg_id),
            entity_id=str(request.entity_id) if request.entity_id else None,
            relation_types=request.relation_types,
            limit=request.limit,
        )
        
        return KGRelationshipSearchResponse(
            relationships=relationships,
            total_count=len(relationships),
            entity_id=request.entity_id,
            relation_types=request.relation_types,
        )
        
    except Exception as e:
        logger.error(f"Error searching relationships: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search relationships")


@router.post("/{kg_id}/paths/find", response_model=KGPathFindingResponse)
async def find_paths(
    kg_id: UUID,
    request: KGPathFindingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find paths between two entities in the knowledge graph."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KnowledgeGraphService(db)
        
        paths = await service.find_path(
            kg_id=str(kg_id),
            source_entity_id=str(request.source_entity_id),
            target_entity_id=str(request.target_entity_id),
            max_depth=request.max_depth,
        )
        
        return KGPathFindingResponse(
            paths=paths,
            source_entity_id=request.source_entity_id,
            target_entity_id=request.target_entity_id,
            max_depth=request.max_depth,
        )
        
    except Exception as e:
        logger.error(f"Error finding paths: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to find paths")


@router.post("/{kg_id}/subgraph", response_model=KGSubgraphResponse)
async def get_subgraph(
    kg_id: UUID,
    request: KGSubgraphRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a subgraph around specified entities."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KnowledgeGraphService(db)
        
        subgraph = await service.get_subgraph(
            kg_id=str(kg_id),
            entity_ids=[str(eid) for eid in request.entity_ids],
            depth=request.depth,
        )
        
        return KGSubgraphResponse(
            entities=subgraph["entities"],
            relationships=subgraph["relationships"],
            entity_ids=request.entity_ids,
            depth=request.depth,
        )
        
    except Exception as e:
        logger.error(f"Error getting subgraph: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subgraph")


@router.post("/{kg_id}/extract")
async def trigger_extraction(
    kg_id: UUID,
    document_ids: Optional[List[UUID]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger knowledge graph extraction for specific documents or all documents."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KnowledgeGraphService(db)
        
        # Get documents to process
        if document_ids:
            # Process specific documents
            job_type = "document_specific"
            # In production, you would fetch document texts here
            document_texts = []  # Placeholder
        else:
            # Process all documents in knowledgebase
            job_type = "full_extraction"
            # In production, you would fetch all document texts here
            document_texts = []  # Placeholder
        
        # Start extraction
        stats = await service.extract_entities_and_relationships(
            kg_id=str(kg_id),
            document_texts=document_texts
        )
        
        return {
            "message": "Extraction completed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error triggering extraction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger extraction")


@router.get("/{kg_id}/stats")
async def get_knowledge_graph_stats(
    kg_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get knowledge graph statistics."""
    
    # Verify access
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    # Get entity type distribution
    entity_type_stats = db.execute("""
        SELECT entity_type, COUNT(*) as count
        FROM kg_entities 
        WHERE knowledge_graph_id = :kg_id
        GROUP BY entity_type
        ORDER BY count DESC
    """, {"kg_id": str(kg_id)}).fetchall()
    
    # Get relationship type distribution
    relation_type_stats = db.execute("""
        SELECT relation_type, COUNT(*) as count
        FROM kg_relationships 
        WHERE knowledge_graph_id = :kg_id
        GROUP BY relation_type
        ORDER BY count DESC
    """, {"kg_id": str(kg_id)}).fetchall()
    
    return {
        "entity_count": kg.entity_count,
        "relationship_count": kg.relationship_count,
        "entity_types": [{"type": row[0], "count": row[1]} for row in entity_type_stats],
        "relationship_types": [{"type": row[0], "count": row[1]} for row in relation_type_stats],
        "last_processed_at": kg.last_processed_at,
        "processing_status": kg.processing_status,
    }


@router.get("/entity-types")
async def get_entity_types():
    """Get available entity types."""
    return [{"value": et.value, "label": et.value.replace("_", " ").title()} for et in EntityType]


@router.get("/relation-types")
async def get_relation_types():
    """Get available relationship types."""
    return [{"value": rt.value, "label": rt.value.replace("_", " ").title()} for rt in RelationType]