"""
Unit tests for Human-in-the-Loop system.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from backend.services.agent_builder.human_in_loop import (
    HumanInTheLoop,
    ApprovalWorkflow,
    ApprovalRequest,
    FeedbackRequest,
    ApprovalStatus,
    ApprovalPriority
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    service = Mock()
    service.create_notification = AsyncMock()
    return service


@pytest.fixture
def hitl(mock_db, mock_notification_service):
    """Create HumanInTheLoop instance."""
    return HumanInTheLoop(
        db=mock_db,
        notification_service=mock_notification_service
    )


@pytest.mark.asyncio
async def test_request_approval(hitl, mock_notification_service):
    """Test creating approval request."""
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Deploy to production",
        context={"environment": "production"},
        requester_id="user_1",
        approver_ids=["manager_1", "manager_2"],
        priority=ApprovalPriority.HIGH,
        timeout_seconds=3600
    )
    
    assert request.request_id is not None
    assert request.status == ApprovalStatus.PENDING
    assert request.agent_id == "agent_123"
    assert request.action == "Deploy to production"
    assert len(request.approver_ids) == 2
    
    # Verify notifications sent
    assert mock_notification_service.create_notification.call_count == 2


@pytest.mark.asyncio
async def test_approve_request(hitl):
    """Test approving a request."""
    # Create request
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Test action",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        timeout_seconds=3600
    )
    
    # Approve
    result = await hitl.approve(
        request_id=request.request_id,
        approver_id="manager_1",
        comment="Looks good"
    )
    
    assert result is True
    assert request.status == ApprovalStatus.APPROVED
    assert request.approved_by == "manager_1"
    assert request.approved_at is not None


@pytest.mark.asyncio
async def test_reject_request(hitl):
    """Test rejecting a request."""
    # Create request
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Test action",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        timeout_seconds=3600
    )
    
    # Reject
    result = await hitl.reject(
        request_id=request.request_id,
        approver_id="manager_1",
        reason="Not ready for production",
        comment="Need more testing"
    )
    
    assert result is True
    assert request.status == ApprovalStatus.REJECTED
    assert request.approved_by == "manager_1"
    assert request.rejection_reason == "Not ready for production"


@pytest.mark.asyncio
async def test_unauthorized_approval(hitl):
    """Test that unauthorized user cannot approve."""
    # Create request
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Test action",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        timeout_seconds=3600
    )
    
    # Try to approve with unauthorized user
    with pytest.raises(ValueError, match="not authorized"):
        await hitl.approve(
            request_id=request.request_id,
            approver_id="unauthorized_user",
            comment="Trying to approve"
        )


@pytest.mark.asyncio
async def test_cancel_approval(hitl):
    """Test cancelling approval request."""
    # Create request
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Test action",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        timeout_seconds=3600
    )
    
    # Cancel
    result = await hitl.cancel_approval(
        request_id=request.request_id,
        canceller_id="user_1"
    )
    
    assert result is True
    assert request.status == ApprovalStatus.CANCELLED


@pytest.mark.asyncio
async def test_collect_feedback(hitl):
    """Test creating feedback request."""
    questions = [
        {
            "id": "q1",
            "type": "rating",
            "question": "How satisfied are you?",
            "scale": [1, 5]
        },
        {
            "id": "q2",
            "type": "text",
            "question": "What could be improved?"
        }
    ]
    
    request = await hitl.collect_feedback(
        execution_id="exec_456",
        questions=questions,
        responder_ids=["user_1", "user_2"],
        timeout_seconds=86400
    )
    
    assert request.request_id is not None
    assert len(request.questions) == 2
    assert len(request.responder_ids) == 2
    assert request.completed is False


@pytest.mark.asyncio
async def test_submit_feedback(hitl):
    """Test submitting feedback."""
    questions = [
        {"id": "q1", "type": "rating", "question": "Rate this"},
        {"id": "q2", "type": "text", "question": "Comments"}
    ]
    
    request = await hitl.collect_feedback(
        execution_id="exec_456",
        questions=questions,
        responder_ids=["user_1", "user_2"]
    )
    
    # Submit feedback from user_1
    result = await hitl.submit_feedback(
        request_id=request.request_id,
        responder_id="user_1",
        responses={"q1": 5, "q2": "Great!"}
    )
    
    assert result is True
    assert "user_1" in request.responses
    assert request.completed is False  # Not all responses collected
    
    # Submit feedback from user_2
    await hitl.submit_feedback(
        request_id=request.request_id,
        responder_id="user_2",
        responses={"q1": 4, "q2": "Good"}
    )
    
    assert request.completed is True  # All responses collected


@pytest.mark.asyncio
async def test_get_feedback_results(hitl):
    """Test getting aggregated feedback results."""
    questions = [
        {"id": "q1", "type": "rating", "question": "Rate this"},
        {"id": "q2", "type": "choice", "question": "Choose", "options": ["A", "B", "C"]}
    ]
    
    request = await hitl.collect_feedback(
        execution_id="exec_456",
        questions=questions,
        responder_ids=["user_1", "user_2", "user_3"]
    )
    
    # Submit responses
    await hitl.submit_feedback(request.request_id, "user_1", {"q1": 5, "q2": "A"})
    await hitl.submit_feedback(request.request_id, "user_2", {"q1": 4, "q2": "A"})
    await hitl.submit_feedback(request.request_id, "user_3", {"q1": 3, "q2": "B"})
    
    # Get results
    results = await hitl.get_feedback_results(request.request_id)
    
    assert results["responses_received"] == 3
    assert results["completed"] is True
    
    # Check rating aggregation
    q1_agg = results["aggregated_data"]["q1"]
    assert q1_agg["average"] == 4.0
    assert q1_agg["min"] == 3
    assert q1_agg["max"] == 5
    
    # Check choice aggregation
    q2_agg = results["aggregated_data"]["q2"]
    assert q2_agg["A"] == 2
    assert q2_agg["B"] == 1


@pytest.mark.asyncio
async def test_get_pending_approvals(hitl):
    """Test getting pending approvals."""
    # Create multiple requests
    await hitl.request_approval(
        agent_id="agent_1",
        execution_id="exec_1",
        action="Action 1",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        priority=ApprovalPriority.HIGH
    )
    
    await hitl.request_approval(
        agent_id="agent_2",
        execution_id="exec_2",
        action="Action 2",
        context={},
        requester_id="user_2",
        approver_ids=["manager_1", "manager_2"],
        priority=ApprovalPriority.CRITICAL
    )
    
    # Get pending for manager_1
    pending = hitl.get_pending_approvals(approver_id="manager_1")
    
    assert len(pending) == 2
    # Should be sorted by priority (CRITICAL first)
    assert pending[0].priority == ApprovalPriority.CRITICAL


@pytest.mark.asyncio
async def test_approval_workflow(hitl):
    """Test multi-level approval workflow."""
    workflow = ApprovalWorkflow(hitl)
    
    approval_chain = [
        {"approver_ids": ["lead_1"], "timeout": 3600},
        {"approver_ids": ["manager_1"], "timeout": 3600}
    ]
    
    workflow_id = await workflow.create_approval_chain(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Deploy to production",
        context={},
        requester_id="user_1",
        approval_chain=approval_chain
    )
    
    assert workflow_id is not None
    assert workflow_id in workflow.workflows


@pytest.mark.asyncio
async def test_approval_callback(hitl):
    """Test approval callback execution."""
    callback_called = False
    approval_result = None
    
    def callback(approved: bool):
        nonlocal callback_called, approval_result
        callback_called = True
        approval_result = approved
    
    # Create request
    request = await hitl.request_approval(
        agent_id="agent_123",
        execution_id="exec_456",
        action="Test action",
        context={},
        requester_id="user_1",
        approver_ids=["manager_1"],
        timeout_seconds=3600
    )
    
    # Register callback
    hitl.register_approval_callback(request.request_id, callback)
    
    # Approve
    await hitl.approve(
        request_id=request.request_id,
        approver_id="manager_1"
    )
    
    assert callback_called is True
    assert approval_result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
