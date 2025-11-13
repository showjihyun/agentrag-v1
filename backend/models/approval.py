"""
Approval Request Model

Database model for human approval requests in workflows.
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class ApprovalRequest(Base):
    """Model for workflow approval requests."""
    
    __tablename__ = "approval_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, nullable=False, index=True)
    workflow_execution_id = Column(String, nullable=True, index=True)
    node_id = Column(String, nullable=False)
    
    # Approvers
    approvers = Column(JSON, nullable=False)  # List of approver emails/IDs
    require_all = Column(Boolean, default=True)
    
    # Status
    status = Column(String, default="pending", index=True)  # pending, approved, rejected, timeout
    
    # Content
    message = Column(String)
    data_for_review = Column(JSON)  # Data to show to approvers
    
    # Notification
    notification_method = Column(String, default="email")  # email, slack, webhook
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    timeout_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution
    approved_by = Column(JSON, default=list)  # List of approvers who approved
    rejected_by = Column(JSON, default=list)  # List of approvers who rejected
    resolution_comment = Column(String, nullable=True)
    
    # Auto-approval
    auto_approve_after_timeout = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<ApprovalRequest {self.id} status={self.status}>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_execution_id": self.workflow_execution_id,
            "node_id": self.node_id,
            "approvers": self.approvers,
            "require_all": self.require_all,
            "status": self.status,
            "message": self.message,
            "data_for_review": self.data_for_review,
            "notification_method": self.notification_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "approved_by": self.approved_by,
            "rejected_by": self.rejected_by,
            "resolution_comment": self.resolution_comment,
            "auto_approve_after_timeout": self.auto_approve_after_timeout,
        }
    
    def can_approve(self, approver: str) -> bool:
        """Check if approver can approve this request."""
        return (
            self.status == "pending" and
            approver in self.approvers and
            approver not in self.approved_by and
            approver not in self.rejected_by
        )
    
    def add_approval(self, approver: str) -> bool:
        """
        Add an approval.
        
        Returns:
            True if request is now fully approved
        """
        if not self.can_approve(approver):
            return False
        
        if approver not in self.approved_by:
            self.approved_by.append(approver)
        
        # Check if fully approved
        if self.require_all:
            return set(self.approved_by) == set(self.approvers)
        else:
            return len(self.approved_by) > 0
    
    def add_rejection(self, approver: str) -> bool:
        """
        Add a rejection.
        
        Returns:
            True (rejection is immediate)
        """
        if not self.can_approve(approver):
            return False
        
        if approver not in self.rejected_by:
            self.rejected_by.append(approver)
        
        return True
