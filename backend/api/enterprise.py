# Enterprise Features API
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_optional_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])


# Knowledge Graph Models
class RelatedDocumentsResponse(BaseModel):
    """Related documents response"""

    document_id: str
    related_documents: List[Dict[str, float]]
    graph_stats: Dict


class EntityConnectionsResponse(BaseModel):
    """Entity connections response"""

    entity: str
    connected_entities: List[str]
    connection_count: int


# A/B Testing Models
class CreateExperimentRequest(BaseModel):
    """Create experiment request"""

    experiment_id: str
    name: str
    description: str
    variants: List[str]
    traffic_split: Dict[str, float]


class ExperimentStatsResponse(BaseModel):
    """Experiment statistics response"""

    experiment_id: str
    stats: Dict


# ACL Models
class GrantPermissionRequest(BaseModel):
    """Grant permission request"""

    document_id: str
    user_id: str
    permissions: List[str]


class CheckPermissionRequest(BaseModel):
    """Check permission request"""

    document_id: str
    permission: str


# Knowledge Graph Endpoints
@router.get(
    "/knowledge-graph/related/{document_id}", response_model=RelatedDocumentsResponse
)
async def get_related_documents(
    document_id: str,
    max_results: int = 5,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get documents related to given document based on knowledge graph.
    """
    from backend.services.knowledge_graph import get_knowledge_graph

    kg = get_knowledge_graph()
    related = kg.find_related_documents(document_id, max_results)

    return RelatedDocumentsResponse(
        document_id=document_id,
        related_documents=[
            {"document_id": doc_id, "similarity": score} for doc_id, score in related
        ],
        graph_stats=kg.get_graph_stats(),
    )


@router.get(
    "/knowledge-graph/entity/{entity}", response_model=EntityConnectionsResponse
)
async def get_entity_connections(
    entity: str,
    max_depth: int = 2,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get entities connected to given entity in knowledge graph.
    """
    from backend.services.knowledge_graph import get_knowledge_graph

    kg = get_knowledge_graph()
    connected = kg.find_entity_connections(entity, max_depth)

    return EntityConnectionsResponse(
        entity=entity, connected_entities=connected, connection_count=len(connected)
    )


# A/B Testing Endpoints
@router.post("/ab-testing/experiment")
async def create_experiment(
    request: CreateExperimentRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Create new A/B test experiment.

    Requires admin privileges in production.
    """
    from backend.services.ab_testing import get_ab_testing_service

    ab_service = get_ab_testing_service()

    experiment = ab_service.create_experiment(
        experiment_id=request.experiment_id,
        name=request.name,
        description=request.description,
        variants=request.variants,
        traffic_split=request.traffic_split,
    )

    return {
        "success": True,
        "experiment_id": experiment.id,
        "message": f"Experiment '{experiment.name}' created",
    }


@router.get(
    "/ab-testing/experiment/{experiment_id}/stats",
    response_model=ExperimentStatsResponse,
)
async def get_experiment_stats(
    experiment_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get statistics for A/B test experiment.
    """
    from backend.services.ab_testing import get_ab_testing_service

    ab_service = get_ab_testing_service()
    stats = ab_service.get_experiment_stats(experiment_id)

    return ExperimentStatsResponse(experiment_id=experiment_id, stats=stats)


@router.post("/ab-testing/experiment/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Stop A/B test experiment.
    """
    from backend.services.ab_testing import get_ab_testing_service

    ab_service = get_ab_testing_service()
    ab_service.stop_experiment(experiment_id)

    return {"success": True, "message": f"Experiment {experiment_id} stopped"}


# ACL Endpoints
@router.post("/acl/grant")
async def grant_permission(
    request: GrantPermissionRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Grant permissions to user for document.
    """
    from backend.services.document_acl import get_document_acl, Permission

    acl = get_document_acl()

    # Convert string permissions to Permission enum
    permissions = set()
    for perm_str in request.permissions:
        try:
            permissions.add(Permission(perm_str))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission: {perm_str}",
            )

    acl.grant_permission(
        document_id=request.document_id,
        user_id=request.user_id,
        permissions=permissions,
        granted_by=str(current_user.id) if current_user else "system",
    )

    return {
        "success": True,
        "message": f"Permissions granted to user {request.user_id}",
    }


@router.post("/acl/check")
async def check_permission(
    request: CheckPermissionRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Check if current user has permission for document.
    """
    from backend.services.document_acl import get_document_acl, Permission

    if not current_user:
        return {"has_permission": False}

    acl = get_document_acl()

    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {request.permission}",
        )

    has_permission = acl.check_permission(
        document_id=request.document_id,
        user_id=str(current_user.id),
        permission=permission,
    )

    return {"has_permission": has_permission}


@router.get("/acl/documents")
async def get_accessible_documents(
    permission: str = "read", current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get list of documents user can access.
    """
    if not current_user:
        return {"documents": []}

    from backend.services.document_acl import get_document_acl, Permission

    acl = get_document_acl()

    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {permission}",
        )

    documents = acl.get_accessible_documents(
        user_id=str(current_user.id), permission=perm
    )

    return {"documents": documents}
