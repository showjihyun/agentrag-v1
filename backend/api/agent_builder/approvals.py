"""
API endpoints for Human-in-the-Loop approval system.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.services.agent_builder.human_in_loop import (
    HumanInTheLoop,
    ApprovalWorkflow,
    ApprovalPriority,
    ApprovalStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/approvals", tags=["approvals"])


# Pydantic models
class ApprovalRequestCreate(BaseModel):
    """Request to create approval."""
    agent_id: str
    execution_id: str
    action: str
    context: dict
    approver_ids: List[str]
    priority: str = "medium"
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)
    metadata: Optional[dict] = None


class ApprovalDecision(BaseModel):
    """Approval decision."""
    response_data: Optional[dict] = None
    comment: Optional[str] = None


class RejectionDecision(BaseModel):
    """Rejection decision."""
    reason: str
    comment: Optional[str] = None


class FeedbackRequestCreate(BaseModel):
    """Request to create feedback collection."""
    execution_id: str
    questions: List[dict]
    responder_ids: List[str]
    timeout_seconds: int = Field(default=86400, ge=3600, le=604800)
    metadata: Optional[dict] = None


class FeedbackSubmission(BaseModel):
    """Feedback submission."""
    responses: dict


class ApprovalChainCreate(BaseModel):
    """Request to create approval chain."""
    agent_id: str
    execution_id: str
    action: str
    context: dict
    approval_chain: List[dict]
    metadata: Optional[dict] = None


# Dependency to get HumanInTheLoop instance
def get_hitl(db: Session = Depends(get_db)) -> HumanInTheLoop:
    """Get HumanInTheLoop instance."""
    # In production, inject notification_service and cache_manager
    return HumanInTheLoop(db=db)


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    request: ApprovalRequestCreate,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Create an approval request.
    
    Requires authentication.
    """
    try:
        approval_request = await hitl.request_approval(
            agent_id=request.agent_id,
            execution_id=request.execution_id,
            action=request.action,
            context=request.context,
            requester_id=current_user["user_id"],
            approver_ids=request.approver_ids,
            priority=ApprovalPriority(request.priority),
            timeout_seconds=request.timeout_seconds,
            metadata=request.metadata
        )
        
        return {
            "request_id": approval_request.request_id,
            "status": approval_request.status.value,
            "created_at": approval_request.created_at.isoformat(),
            "expires_at": approval_request.expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create approval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/{request_id}")
async def get_approval_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Get approval request details.
    
    Requires authentication.
    """
    approval_request = hitl.approval_requests.get(request_id)
    
    if not approval_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )
    
    # Check authorization
    user_id = current_user["user_id"]
    if (user_id != approval_request.requester_id and 
        user_id not in approval_request.approver_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )
    
    return {
        "request_id": approval_request.request_id,
        "agent_id": approval_request.agent_id,
        "execution_id": approval_request.execution_id,
        "action": approval_request.action,
        "context": approval_request.context,
        "requester_id": approval_request.requester_id,
        "approver_ids": approval_request.approver_ids,
        "priority": approval_request.priority.value,
        "status": approval_request.status.value,
        "created_at": approval_request.created_at.isoformat(),
        "expires_at": approval_request.expires_at.isoformat(),
        "approved_by": approval_request.approved_by,
        "approved_at": approval_request.approved_at.isoformat() if approval_request.approved_at else None,
        "rejection_reason": approval_request.rejection_reason,
        "response_data": approval_request.response_data,
        "metadata": approval_request.metadata
    }


@router.get("/requests")
async def list_approval_requests(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    List approval requests for current user.
    
    Returns requests where user is requester or approver.
    """
    user_id = current_user["user_id"]
    
    # Get all requests for user
    user_requests = [
        req for req in hitl.approval_requests.values()
        if req.requester_id == user_id or user_id in req.approver_ids
    ]
    
    # Filter by status
    if status_filter:
        user_requests = [
            req for req in user_requests
            if req.status.value == status_filter
        ]
    
    return {
        "requests": [
            {
                "request_id": req.request_id,
                "agent_id": req.agent_id,
                "execution_id": req.execution_id,
                "action": req.action,
                "priority": req.priority.value,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
                "is_requester": req.requester_id == user_id,
                "is_approver": user_id in req.approver_ids
            }
            for req in user_requests
        ],
        "total": len(user_requests)
    }


@router.post("/requests/{request_id}/approve")
async def approve_request(
    request_id: str,
    decision: ApprovalDecision,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Approve an approval request.
    
    Requires user to be in approver list.
    """
    try:
        await hitl.approve(
            request_id=request_id,
            approver_id=current_user["user_id"],
            response_data=decision.response_data,
            comment=decision.comment
        )
        
        return {"message": "Request approved successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to approve request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: str,
    decision: RejectionDecision,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Reject an approval request.
    
    Requires user to be in approver list.
    """
    try:
        await hitl.reject(
            request_id=request_id,
            approver_id=current_user["user_id"],
            reason=decision.reason,
            comment=decision.comment
        )
        
        return {"message": "Request rejected successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to reject request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/requests/{request_id}")
async def cancel_approval_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Cancel an approval request.
    
    Only requester can cancel.
    """
    try:
        await hitl.cancel_approval(
            request_id=request_id,
            canceller_id=current_user["user_id"]
        )
        
        return {"message": "Request cancelled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/pending")
async def get_pending_approvals(
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Get pending approvals for current user.
    
    Returns approvals where user is an approver.
    """
    user_id = current_user["user_id"]
    pending = hitl.get_pending_approvals(approver_id=user_id)
    
    return {
        "pending_approvals": [
            {
                "request_id": req.request_id,
                "agent_id": req.agent_id,
                "execution_id": req.execution_id,
                "action": req.action,
                "priority": req.priority.value,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
                "time_remaining_seconds": int((req.expires_at - datetime.now(req.expires_at.tzinfo)).total_seconds())
            }
            for req in pending
        ],
        "total": len(pending)
    }


# Feedback endpoints
@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def create_feedback_request(
    request: FeedbackRequestCreate,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Create a feedback collection request.
    
    Requires authentication.
    """
    try:
        feedback_request = await hitl.collect_feedback(
            execution_id=request.execution_id,
            questions=request.questions,
            responder_ids=request.responder_ids,
            timeout_seconds=request.timeout_seconds,
            metadata=request.metadata
        )
        
        return {
            "request_id": feedback_request.request_id,
            "execution_id": feedback_request.execution_id,
            "created_at": feedback_request.created_at.isoformat(),
            "expires_at": feedback_request.expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create feedback request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/feedback/{request_id}/submit")
async def submit_feedback(
    request_id: str,
    submission: FeedbackSubmission,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Submit feedback responses.
    
    Requires user to be in responder list.
    """
    try:
        await hitl.submit_feedback(
            request_id=request_id,
            responder_id=current_user["user_id"],
            responses=submission.responses
        )
        
        return {"message": "Feedback submitted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/feedback/{request_id}/results")
async def get_feedback_results(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Get aggregated feedback results.
    
    Requires authentication.
    """
    try:
        results = await hitl.get_feedback_results(request_id)
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get feedback results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Approval chain endpoints
@router.post("/chains", status_code=status.HTTP_201_CREATED)
async def create_approval_chain(
    request: ApprovalChainCreate,
    current_user: dict = Depends(get_current_user),
    hitl: HumanInTheLoop = Depends(get_hitl)
):
    """
    Create multi-level approval chain.
    
    Requires authentication.
    """
    try:
        workflow = ApprovalWorkflow(hitl)
        
        workflow_id = await workflow.create_approval_chain(
            agent_id=request.agent_id,
            execution_id=request.execution_id,
            action=request.action,
            context=request.context,
            requester_id=current_user["user_id"],
            approval_chain=request.approval_chain,
            metadata=request.metadata
        )
        
        return {
            "workflow_id": workflow_id,
            "levels": len(request.approval_chain)
        }
    except Exception as e:
        logger.error(f"Failed to create approval chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
