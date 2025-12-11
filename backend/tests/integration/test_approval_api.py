"""
Integration tests for Approval API
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.main import app
from backend.models.approval import ApprovalRequest
from backend.db.database import get_db


client = TestClient(app)


def test_create_approval(db_session):
    """Test creating approval request."""
    approval = ApprovalRequest(
        workflow_id="test_workflow_123",
        node_id="approval_node_1",
        approvers=["user1@example.com", "user2@example.com"],
        require_all=True,
        message="Please approve this test request",
        data_for_review={"amount": 1000, "type": "payment"},
        timeout_at=datetime.utcnow() + timedelta(hours=24),
    )
    
    db_session.add(approval)
    db_session.commit()
    
    assert approval.id is not None
    assert approval.status == "pending"


def test_get_approval(db_session):
    """Test getting approval request."""
    # Create approval
    approval = ApprovalRequest(
        workflow_id="test_workflow_456",
        node_id="approval_node_2",
        approvers=["user@example.com"],
        message="Test approval",
    )
    
    db_session.add(approval)
    db_session.commit()
    
    # Get approval
    response = client.get(f"/api/approvals/{approval.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == approval.id
    assert data["status"] == "pending"


def test_approve_request(db_session):
    """Test approving request."""
    # Create approval
    approval = ApprovalRequest(
        workflow_id="test_workflow_789",
        node_id="approval_node_3",
        approvers=["approver@example.com"],
        require_all=False,
        message="Test approval",
    )
    
    db_session.add(approval)
    db_session.commit()
    
    # Approve
    response = client.post(
        f"/api/approvals/{approval.id}/approve",
        json={"approver": "approver@example.com"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert "approver@example.com" in data["approved_by"]


def test_reject_request(db_session):
    """Test rejecting request."""
    # Create approval
    approval = ApprovalRequest(
        workflow_id="test_workflow_101",
        node_id="approval_node_4",
        approvers=["approver@example.com"],
        message="Test approval",
    )
    
    db_session.add(approval)
    db_session.commit()
    
    # Reject
    response = client.post(
        f"/api/approvals/{approval.id}/reject",
        json={"approver": "approver@example.com", "comment": "Not approved"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


def test_list_approvals(db_session):
    """Test listing approvals."""
    # Create multiple approvals
    for i in range(3):
        approval = ApprovalRequest(
            workflow_id=f"test_workflow_{i}",
            node_id=f"node_{i}",
            approvers=["user@example.com"],
            message=f"Test {i}",
        )
        db_session.add(approval)
    
    db_session.commit()
    
    # List
    response = client.get("/api/approvals?status=pending")
    
    assert response.status_code == 200
    data = response.json()
    assert "approvals" in data
    assert len(data["approvals"]) >= 3
