"""
Approval API Endpoints

Handles approval requests for human-in-the-loop workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.db.session import get_db
from backend.models.approval import ApprovalRequest

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ApprovalResponse(BaseModel):
    """Response model for approval actions."""
    approver: str
    comment: Optional[str] = None


class ApprovalListResponse(BaseModel):
    """Response model for listing approvals."""
    approvals: List[dict]
    total: int


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    db: Session = Depends(get_db),
):
    """
    Get approval request details.
    
    Args:
        approval_id: Approval request ID
        db: Database session
        
    Returns:
        Approval request details
    """
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id
    ).first()
    
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )
    
    return approval.to_dict()


@router.get("/")
async def list_approvals(
    status_filter: Optional[str] = None,
    approver: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List approval requests.
    
    Args:
        status_filter: Filter by status (pending, approved, rejected, timeout)
        approver: Filter by approver email
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of approval requests
    """
    query = db.query(ApprovalRequest)
    
    if status_filter:
        query = query.filter(ApprovalRequest.status == status_filter)
    
    if approver:
        # Filter where approver is in the approvers list
        query = query.filter(ApprovalRequest.approvers.contains([approver]))
    
    total = query.count()
    
    approvals = query.order_by(
        ApprovalRequest.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return {
        "approvals": [a.to_dict() for a in approvals],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    response: ApprovalResponse,
    db: Session = Depends(get_db),
):
    """
    Approve an approval request.
    
    Args:
        approval_id: Approval request ID
        response: Approval response with approver info
        db: Database session
        
    Returns:
        Updated approval status
    """
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id
    ).first()
    
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )
    
    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval request is already {approval.status}"
        )
    
    if not approval.can_approve(response.approver):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to approve this request"
        )
    
    # Add approval
    is_fully_approved = approval.add_approval(response.approver)
    
    if is_fully_approved:
        approval.status = "approved"
        approval.resolved_at = datetime.utcnow()
        approval.resolution_comment = response.comment
        
        # TODO: Resume workflow execution
        # This would trigger the workflow to continue from the approval node
    
    db.commit()
    
    return {
        "success": True,
        "status": approval.status,
        "approved_by": approval.approved_by,
        "message": "Approval recorded successfully",
    }


@router.post("/{approval_id}/reject")
async def reject_request(
    approval_id: str,
    response: ApprovalResponse,
    db: Session = Depends(get_db),
):
    """
    Reject an approval request.
    
    Args:
        approval_id: Approval request ID
        response: Rejection response with approver info
        db: Database session
        
    Returns:
        Updated approval status
    """
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id
    ).first()
    
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )
    
    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval request is already {approval.status}"
        )
    
    if not approval.can_approve(response.approver):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to reject this request"
        )
    
    # Add rejection
    approval.add_rejection(response.approver)
    approval.status = "rejected"
    approval.resolved_at = datetime.utcnow()
    approval.resolution_comment = response.comment
    
    # TODO: Resume workflow execution with rejection
    # This would trigger the workflow to continue via the "rejected" path
    
    db.commit()
    
    return {
        "success": True,
        "status": approval.status,
        "rejected_by": approval.rejected_by,
        "message": "Rejection recorded successfully",
    }


@router.get("/pending/count")
async def get_pending_count(
    approver: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get count of pending approvals.
    
    Args:
        approver: Optional filter by approver
        db: Database session
        
    Returns:
        Count of pending approvals
    """
    query = db.query(ApprovalRequest).filter(
        ApprovalRequest.status == "pending"
    )
    
    if approver:
        query = query.filter(ApprovalRequest.approvers.contains([approver]))
    
    count = query.count()
    
    return {
        "pending_count": count,
        "approver": approver,
    }
