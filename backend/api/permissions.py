"""Document permission management API endpoints."""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.permission import PermissionType
from backend.services.document_acl_service import (
    DocumentACLService,
    DocumentACLServiceError,
    get_document_acl_service,
)
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


# Request/Response Models
class GrantPermissionRequest(BaseModel):
    """Request to grant permission."""

    document_id: UUID = Field(..., description="Document UUID")
    target_user_id: Optional[UUID] = Field(
        None, description="Target user ID (for user permission)"
    )
    target_group_id: Optional[UUID] = Field(
        None, description="Target group ID (for group permission)"
    )
    permission_type: PermissionType = Field(
        PermissionType.READ, description="Permission level"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Optional expiration timestamp"
    )


class PermissionResponse(BaseModel):
    """Permission response."""

    id: UUID
    document_id: UUID
    user_id: Optional[UUID]
    group_id: Optional[UUID]
    permission_type: PermissionType
    granted_by: Optional[UUID]
    granted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateGroupRequest(BaseModel):
    """Request to create group."""

    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(
        None, max_length=500, description="Group description"
    )


class GroupResponse(BaseModel):
    """Group response."""

    id: UUID
    name: str
    description: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class AddGroupMemberRequest(BaseModel):
    """Request to add group member."""

    group_id: UUID = Field(..., description="Group UUID")
    user_id: UUID = Field(..., description="User UUID to add")


class GroupMemberResponse(BaseModel):
    """Group member response."""

    id: UUID
    group_id: UUID
    user_id: UUID
    added_by: Optional[UUID]
    added_at: datetime

    class Config:
        from_attributes = True


# Permission Endpoints
@router.post(
    "/grant", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED
)
async def grant_permission(
    request: GrantPermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Grant permission to user or group.

    Requires admin permission on the document.
    """
    try:
        acl_service = get_document_acl_service(db)

        permission = await acl_service.grant_permission(
            document_id=request.document_id,
            owner_id=current_user.id,
            target_user_id=request.target_user_id,
            target_group_id=request.target_group_id,
            permission_type=request.permission_type,
            expires_at=request.expires_at,
        )

        return PermissionResponse.from_orm(permission)

    except DocumentACLServiceError as e:
        logger.warning(f"Permission grant failed: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error granting permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant permission",
        )


@router.delete("/revoke/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a permission.

    Requires admin permission on the document.
    """
    try:
        acl_service = get_document_acl_service(db)

        await acl_service.revoke_permission(
            permission_id=permission_id, owner_id=current_user.id
        )

        return None

    except DocumentACLServiceError as e:
        logger.warning(f"Permission revoke failed: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error revoking permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke permission",
        )


@router.get("/document/{document_id}", response_model=List[PermissionResponse])
async def list_document_permissions(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all permissions for a document.

    Requires admin permission on the document.
    """
    try:
        acl_service = get_document_acl_service(db)

        permissions = await acl_service.list_document_permissions(
            document_id=document_id, owner_id=current_user.id
        )

        return [PermissionResponse.from_orm(p) for p in permissions]

    except DocumentACLServiceError as e:
        logger.warning(f"Permission listing failed: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list permissions",
        )


@router.get("/check/{document_id}/{permission_type}")
async def check_permission(
    document_id: UUID,
    permission_type: PermissionType,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if current user has specific permission for document.
    """
    try:
        acl_service = get_document_acl_service(db)

        has_permission = await acl_service.check_permission(
            user_id=current_user.id,
            document_id=document_id,
            required_permission=permission_type,
        )

        return {
            "document_id": str(document_id),
            "user_id": str(current_user.id),
            "permission_type": permission_type,
            "has_permission": has_permission,
        }

    except Exception as e:
        logger.error(f"Unexpected error checking permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check permission",
        )


# Group Endpoints
@router.post(
    "/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED
)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new group.

    Creator is automatically added as first member.
    """
    try:
        acl_service = get_document_acl_service(db)

        group = await acl_service.create_group(
            name=request.name,
            description=request.description,
            creator_id=current_user.id,
        )

        return GroupResponse.from_orm(group)

    except DocumentACLServiceError as e:
        logger.warning(f"Group creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating group: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group",
        )


@router.post(
    "/groups/members",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_group_member(
    request: AddGroupMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add user to group.
    """
    try:
        acl_service = get_document_acl_service(db)

        member = await acl_service.add_group_member(
            group_id=request.group_id, user_id=request.user_id, added_by=current_user.id
        )

        return GroupMemberResponse.from_orm(member)

    except DocumentACLServiceError as e:
        logger.warning(f"Add group member failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding group member: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add group member",
        )


@router.delete(
    "/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove user from group.

    Only group creator can remove members.
    """
    try:
        acl_service = get_document_acl_service(db)

        await acl_service.remove_group_member(
            group_id=group_id, user_id=user_id, removed_by=current_user.id
        )

        return None

    except DocumentACLServiceError as e:
        logger.warning(f"Remove group member failed: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error removing group member: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove group member",
        )


class BulkGrantPermissionRequest(BaseModel):
    """Request to grant permission to multiple users."""

    document_id: UUID = Field(..., description="Document UUID")
    user_ids: List[UUID] = Field(..., description="List of user IDs")
    permission_type: PermissionType = Field(
        PermissionType.READ, description="Permission level"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Optional expiration timestamp"
    )


@router.post(
    "/grant/bulk",
    response_model=List[PermissionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def grant_bulk_permissions(
    request: BulkGrantPermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Grant permission to multiple users at once.

    Requires admin permission on the document.
    """
    try:
        acl_service = get_document_acl_service(db)

        permissions = await acl_service.grant_bulk_permissions(
            document_id=request.document_id,
            owner_id=current_user.id,
            user_ids=request.user_ids,
            permission_type=request.permission_type,
            expires_at=request.expires_at,
        )

        return [PermissionResponse.from_orm(p) for p in permissions]

    except DocumentACLServiceError as e:
        logger.warning(f"Bulk permission grant failed: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error granting bulk permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant bulk permissions",
        )


@router.get("/user/documents")
async def get_accessible_documents(
    permission_type: PermissionType = PermissionType.READ,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of documents that current user can access.
    """
    try:
        acl_service = get_document_acl_service(db)

        document_ids = await acl_service.get_user_accessible_documents(
            user_id=current_user.id, permission_type=permission_type
        )

        return {
            "user_id": str(current_user.id),
            "permission_type": permission_type,
            "document_count": len(document_ids),
            "document_ids": [str(doc_id) for doc_id in document_ids],
        }

    except Exception as e:
        logger.error(
            f"Unexpected error getting accessible documents: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get accessible documents",
        )


@router.post("/cleanup/expired")
async def cleanup_expired_permissions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Cleanup expired permissions (admin only).

    This endpoint should be called periodically or by admin users.
    """
    try:
        # TODO: Add admin check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin only")

        acl_service = get_document_acl_service(db)

        count = await acl_service.cleanup_expired_permissions()

        return {"cleaned_up": count, "message": f"Removed {count} expired permissions"}

    except Exception as e:
        logger.error(f"Unexpected error cleaning up permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired permissions",
        )
