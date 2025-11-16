"""
Approval API Endpoints

Handles approval requests for human-in-the-loop workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from backend.db.session import get_db
from backend.models.approval import ApprovalRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


async def _resume_workflow_execution(
    db: Session,
    workflow_id: str,
    execution_id: Optional[str],
    approval_result: str,
    approval_data: Dict[str, Any]
):
    """
    Resume workflow execution after approval/rejection.
    
    Args:
        db: Database session
        workflow_id: Workflow ID
        execution_id: Workflow execution ID
        approval_result: "approved" or "rejected"
        approval_data: Approval metadata
    """
    if not execution_id:
        logger.warning(f"No execution_id for workflow {workflow_id}, cannot resume")
        return
    
    try:
        from backend.db.models.agent_builder import WorkflowExecution, Workflow
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        import asyncio
        
        # Get execution record
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        logger.info(f"Resuming workflow execution {execution_id} with result: {approval_result}")
        
        # Update execution status
        execution.status = "running"
        execution.execution_context = execution.execution_context or {}
        execution.execution_context["approval_result"] = approval_result
        execution.execution_context["approval_data"] = approval_data
        execution.execution_context["resumed_at"] = datetime.utcnow().isoformat()
        db.commit()
        
        # Create executor and resume from approval node
        executor = WorkflowExecutor(workflow, db, execution_id)
        
        # Get the node that was waiting for approval
        graph = workflow.graph_definition
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        # Find the approval node and its next node
        approval_node_id = execution.execution_context.get("waiting_for_node_id")
        if not approval_node_id:
            logger.warning("No waiting_for_node_id in execution context")
            # Try to find from approval data
            approval_node = next(
                (n for n in nodes if n.get("node_type") == "human_approval"),
                None
            )
            if approval_node:
                approval_node_id = approval_node.get("id")
        
        if not approval_node_id:
            logger.error("Cannot find approval node to resume from")
            execution.status = "failed"
            execution.error_message = "Cannot find approval node to resume from"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Find next node based on approval result
        next_edges = [e for e in edges if e.get("source") == approval_node_id]
        
        # Look for edge with matching sourceHandle (approved/rejected)
        next_edge = next(
            (e for e in next_edges if e.get("sourceHandle") == approval_result),
            next_edges[0] if next_edges else None
        )
        
        if not next_edge:
            logger.info(f"No next node after approval, workflow complete")
            execution.status = "completed"
            execution.output_data = {
                "approval_result": approval_result,
                **approval_data
            }
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Get next node
        next_node = next((n for n in nodes if n["id"] == next_edge["target"]), None)
        
        if not next_node:
            logger.error(f"Next node {next_edge['target']} not found")
            execution.status = "failed"
            execution.error_message = f"Next node {next_edge['target']} not found"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Resume execution from next node
        input_data = execution.input_data or {}
        input_data["_approval_result"] = approval_result
        input_data["_approval_data"] = approval_data
        input_data["_user_id"] = str(execution.user_id)
        
        # Execute remaining workflow
        result = await executor._execute_from_node(next_node, nodes, edges, input_data)
        
        # Update execution with result
        execution.status = "completed"
        execution.output_data = result
        execution.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Workflow execution {execution_id} resumed and completed")
        
    except Exception as e:
        logger.error(f"Failed to resume workflow execution: {e}", exc_info=True)
        if execution:
            execution.status = "failed"
            execution.error_message = f"Resume failed: {str(e)}"
            execution.completed_at = datetime.utcnow()
            db.commit()


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
        
        # Resume workflow execution
        await _resume_workflow_execution(
            db=db,
            workflow_id=approval.workflow_id,
            execution_id=approval.workflow_execution_id,
            approval_result="approved",
            approval_data={
                "approved_by": approval.approved_by,
                "comment": response.comment,
            }
        )
    
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
    
    # Resume workflow execution with rejection
    await _resume_workflow_execution(
        db=db,
        workflow_id=approval.workflow_id,
        execution_id=approval.workflow_execution_id,
        approval_result="rejected",
        approval_data={
            "rejected_by": approval.rejected_by,
            "comment": response.comment,
        }
    )
    
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
