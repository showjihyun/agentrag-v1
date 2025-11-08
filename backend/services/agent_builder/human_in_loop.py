"""
Human-in-the-Loop System for Agent Builder.

Enables human approval and feedback in agent execution workflows.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalPriority(str, Enum):
    """Priority levels for approval requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest:
    """Represents a human approval request."""
    
    def __init__(
        self,
        request_id: str,
        agent_id: str,
        execution_id: str,
        action: str,
        context: Dict[str, Any],
        requester_id: str,
        approver_ids: List[str],
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        timeout_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.request_id = request_id
        self.agent_id = agent_id
        self.execution_id = execution_id
        self.action = action
        self.context = context
        self.requester_id = requester_id
        self.approver_ids = approver_ids
        self.priority = priority
        self.timeout_seconds = timeout_seconds
        self.metadata = metadata or {}
        
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=timeout_seconds)
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.rejection_reason: Optional[str] = None
        self.response_data: Optional[Dict[str, Any]] = None


class FeedbackRequest:
    """Represents a feedback collection request."""
    
    def __init__(
        self,
        request_id: str,
        execution_id: str,
        questions: List[Dict[str, Any]],
        responder_ids: List[str],
        timeout_seconds: int = 86400,  # 24 hours
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.request_id = request_id
        self.execution_id = execution_id
        self.questions = questions
        self.responder_ids = responder_ids
        self.timeout_seconds = timeout_seconds
        self.metadata = metadata or {}
        
        self.responses: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=timeout_seconds)
        self.completed = False


class HumanInTheLoop:
    """
    Human-in-the-Loop system for agent execution.
    
    Features:
    - Approval workflows for critical actions
    - Multi-level approval chains
    - Feedback collection
    - Timeout handling
    - Notification integration
    """
    
    def __init__(
        self,
        db: Session,
        notification_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None
    ):
        """
        Initialize Human-in-the-Loop system.
        
        Args:
            db: Database session
            notification_service: Service for sending notifications
            cache_manager: Cache manager for storing requests
        """
        self.db = db
        self.notification_service = notification_service
        self.cache_manager = cache_manager
        
        # In-memory storage for active requests (use Redis in production)
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.feedback_requests: Dict[str, FeedbackRequest] = {}
        
        # Callbacks for approval events
        self.approval_callbacks: Dict[str, List[Callable]] = {}
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("HumanInTheLoop system initialized")
    
    async def start(self):
        """Start background tasks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Started cleanup task")
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired requests."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self._cleanup_expired_requests()
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    async def _cleanup_expired_requests(self):
        """Remove expired approval requests."""
        now = datetime.now(timezone.utc)
        
        # Clean approval requests
        expired_approvals = [
            req_id for req_id, req in self.approval_requests.items()
            if now >= req.expires_at and req.status == ApprovalStatus.PENDING
        ]
        
        for req_id in expired_approvals:
            req = self.approval_requests[req_id]
            req.status = ApprovalStatus.TIMEOUT
            await self._notify_timeout(req)
            logger.info(f"Auto-expired approval request: {req_id}")
        
        # Clean feedback requests
        expired_feedback = [
            req_id for req_id, req in self.feedback_requests.items()
            if now >= req.expires_at and not req.completed
        ]
        
        for req_id in expired_feedback:
            logger.info(f"Feedback request expired: {req_id}")
    
    async def close(self):
        """Clean up resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("HumanInTheLoop system closed")
    
    async def request_approval(
        self,
        agent_id: str,
        execution_id: str,
        action: str,
        context: Dict[str, Any],
        requester_id: str,
        approver_ids: List[str],
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        timeout_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        Request human approval for an action.
        
        Args:
            agent_id: Agent ID
            execution_id: Execution ID
            action: Action requiring approval
            context: Context information
            requester_id: User requesting approval
            approver_ids: List of user IDs who can approve
            priority: Priority level
            timeout_seconds: Timeout in seconds
            metadata: Additional metadata
            
        Returns:
            ApprovalRequest object
        """
        request_id = str(uuid.uuid4())
        
        request = ApprovalRequest(
            request_id=request_id,
            agent_id=agent_id,
            execution_id=execution_id,
            action=action,
            context=context,
            requester_id=requester_id,
            approver_ids=approver_ids,
            priority=priority,
            timeout_seconds=timeout_seconds,
            metadata=metadata
        )
        
        # Store request
        self.approval_requests[request_id] = request
        
        # Cache in Redis if available
        if self.cache_manager:
            await self._cache_approval_request(request)
        
        # Send notifications to approvers
        await self._notify_approvers(request)
        
        logger.info(
            f"Approval request created: {request_id} for action '{action}' "
            f"by {requester_id}, approvers: {approver_ids}"
        )
        
        return request
    
    async def wait_for_approval(
        self,
        request_id: str,
        poll_interval: float = 1.0
    ) -> bool:
        """
        Wait for approval decision.
        
        Args:
            request_id: Approval request ID
            poll_interval: Polling interval in seconds
            
        Returns:
            True if approved, False if rejected/timeout
        """
        request = self.approval_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")
        
        logger.info(f"Waiting for approval: {request_id}")
        
        while request.status == ApprovalStatus.PENDING:
            # Check timeout
            if datetime.now(timezone.utc) >= request.expires_at:
                request.status = ApprovalStatus.TIMEOUT
                logger.warning(f"Approval request timeout: {request_id}")
                await self._notify_timeout(request)
                return False
            
            # Poll for status change
            await asyncio.sleep(poll_interval)
            
            # Refresh from cache if available
            if self.cache_manager:
                cached_request = await self._get_cached_approval_request(request_id)
                if cached_request:
                    request = cached_request
                    self.approval_requests[request_id] = request
        
        approved = request.status == ApprovalStatus.APPROVED
        
        logger.info(
            f"Approval request {request_id} {request.status.value} "
            f"by {request.approved_by}"
        )
        
        return approved
    
    async def approve(
        self,
        request_id: str,
        approver_id: str,
        response_data: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Approve a request.
        
        Args:
            request_id: Approval request ID
            approver_id: User ID approving
            response_data: Optional response data
            comment: Optional comment
            
        Returns:
            True if approval successful
        """
        request = self.approval_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already {request.status.value}")
        
        if approver_id not in request.approver_ids:
            raise ValueError(f"User {approver_id} not authorized to approve")
        
        # Update request
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.now(timezone.utc)
        request.response_data = response_data or {}
        
        if comment:
            request.response_data["comment"] = comment
        
        # Update cache
        if self.cache_manager:
            await self._cache_approval_request(request)
        
        # Notify requester
        await self._notify_approval_decision(request, approved=True)
        
        # Execute callbacks
        await self._execute_callbacks(request_id, approved=True)
        
        logger.info(f"Approval request {request_id} approved by {approver_id}")
        
        return True
    
    async def reject(
        self,
        request_id: str,
        approver_id: str,
        reason: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Reject a request.
        
        Args:
            request_id: Approval request ID
            approver_id: User ID rejecting
            reason: Rejection reason
            comment: Optional comment
            
        Returns:
            True if rejection successful
        """
        request = self.approval_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already {request.status.value}")
        
        if approver_id not in request.approver_ids:
            raise ValueError(f"User {approver_id} not authorized to reject")
        
        # Update request
        request.status = ApprovalStatus.REJECTED
        request.approved_by = approver_id
        request.approved_at = datetime.now(timezone.utc)
        request.rejection_reason = reason
        request.response_data = {"comment": comment} if comment else {}
        
        # Update cache
        if self.cache_manager:
            await self._cache_approval_request(request)
        
        # Notify requester
        await self._notify_approval_decision(request, approved=False)
        
        # Execute callbacks
        await self._execute_callbacks(request_id, approved=False)
        
        logger.info(f"Approval request {request_id} rejected by {approver_id}: {reason}")
        
        return True
    
    async def cancel_approval(
        self,
        request_id: str,
        canceller_id: str
    ) -> bool:
        """
        Cancel an approval request.
        
        Args:
            request_id: Approval request ID
            canceller_id: User ID cancelling
            
        Returns:
            True if cancellation successful
        """
        request = self.approval_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already {request.status.value}")
        
        if canceller_id != request.requester_id:
            raise ValueError(f"Only requester can cancel")
        
        request.status = ApprovalStatus.CANCELLED
        
        # Update cache
        if self.cache_manager:
            await self._cache_approval_request(request)
        
        logger.info(f"Approval request {request_id} cancelled by {canceller_id}")
        
        return True
    
    async def collect_feedback(
        self,
        execution_id: str,
        questions: List[Dict[str, Any]],
        responder_ids: List[str],
        timeout_seconds: int = 86400,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackRequest:
        """
        Collect feedback from users.
        
        Args:
            execution_id: Execution ID
            questions: List of questions with format:
                [{"id": "q1", "type": "text|rating|choice", "question": "...", "options": [...]}]
            responder_ids: List of user IDs to collect feedback from
            timeout_seconds: Timeout in seconds
            metadata: Additional metadata
            
        Returns:
            FeedbackRequest object
        """
        request_id = str(uuid.uuid4())
        
        request = FeedbackRequest(
            request_id=request_id,
            execution_id=execution_id,
            questions=questions,
            responder_ids=responder_ids,
            timeout_seconds=timeout_seconds,
            metadata=metadata
        )
        
        # Store request
        self.feedback_requests[request_id] = request
        
        # Send notifications
        await self._notify_feedback_request(request)
        
        logger.info(
            f"Feedback request created: {request_id} for execution {execution_id}, "
            f"responders: {responder_ids}"
        )
        
        return request
    
    async def submit_feedback(
        self,
        request_id: str,
        responder_id: str,
        responses: Dict[str, Any]
    ) -> bool:
        """
        Submit feedback responses.
        
        Args:
            request_id: Feedback request ID
            responder_id: User ID submitting feedback
            responses: Dictionary of question_id -> answer
            
        Returns:
            True if submission successful
        """
        request = self.feedback_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Feedback request not found: {request_id}")
        
        if responder_id not in request.responder_ids:
            raise ValueError(f"User {responder_id} not authorized to respond")
        
        if request.completed:
            raise ValueError("Feedback request already completed")
        
        # Store responses
        request.responses[responder_id] = {
            "responses": responses,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if all responses collected
        if len(request.responses) == len(request.responder_ids):
            request.completed = True
            logger.info(f"Feedback request {request_id} completed")
        
        logger.info(f"Feedback submitted by {responder_id} for request {request_id}")
        
        return True
    
    async def get_feedback_results(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated feedback results.
        
        Args:
            request_id: Feedback request ID
            
        Returns:
            Aggregated feedback results
        """
        request = self.feedback_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Feedback request not found: {request_id}")
        
        # Aggregate responses
        aggregated = {
            "request_id": request_id,
            "execution_id": request.execution_id,
            "total_responders": len(request.responder_ids),
            "responses_received": len(request.responses),
            "completed": request.completed,
            "questions": request.questions,
            "responses": request.responses,
            "aggregated_data": {}
        }
        
        # Aggregate by question
        for question in request.questions:
            q_id = question["id"]
            q_type = question["type"]
            
            answers = [
                resp["responses"].get(q_id)
                for resp in request.responses.values()
                if q_id in resp["responses"]
            ]
            
            if q_type == "rating":
                # Calculate average rating
                ratings = [a for a in answers if isinstance(a, (int, float))]
                if ratings:
                    aggregated["aggregated_data"][q_id] = {
                        "average": sum(ratings) / len(ratings),
                        "min": min(ratings),
                        "max": max(ratings),
                        "count": len(ratings)
                    }
            elif q_type == "choice":
                # Count choices
                from collections import Counter
                counts = Counter(answers)
                aggregated["aggregated_data"][q_id] = dict(counts)
            else:
                # Text responses
                aggregated["aggregated_data"][q_id] = answers
        
        return aggregated
    
    def register_approval_callback(
        self,
        request_id: str,
        callback: Callable[[bool], None]
    ):
        """
        Register callback for approval decision.
        
        Args:
            request_id: Approval request ID
            callback: Callback function receiving approval decision
        """
        if request_id not in self.approval_callbacks:
            self.approval_callbacks[request_id] = []
        
        self.approval_callbacks[request_id].append(callback)
    
    async def _execute_callbacks(
        self,
        request_id: str,
        approved: bool
    ):
        """Execute registered callbacks."""
        callbacks = self.approval_callbacks.get(request_id, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(approved)
                else:
                    callback(approved)
            except Exception as e:
                logger.error(f"Callback execution failed: {e}")
    
    async def _notify_approvers(self, request: ApprovalRequest):
        """Send notifications to approvers."""
        if not self.notification_service:
            return
        
        for approver_id in request.approver_ids:
            try:
                await self.notification_service.create_notification(
                    user_id=approver_id,
                    notification_type="approval_request",
                    title=f"Approval Required: {request.action}",
                    message=f"Action requires your approval. Priority: {request.priority.value}",
                    data={
                        "request_id": request.request_id,
                        "agent_id": request.agent_id,
                        "execution_id": request.execution_id,
                        "action": request.action,
                        "priority": request.priority.value,
                        "expires_at": request.expires_at.isoformat()
                    },
                    priority=request.priority.value
                )
            except Exception as e:
                logger.error(f"Failed to notify approver {approver_id}: {e}")
    
    async def _notify_approval_decision(
        self,
        request: ApprovalRequest,
        approved: bool
    ):
        """Notify requester of approval decision."""
        if not self.notification_service:
            return
        
        try:
            status = "approved" if approved else "rejected"
            await self.notification_service.create_notification(
                user_id=request.requester_id,
                notification_type="approval_decision",
                title=f"Approval {status.title()}",
                message=f"Your request for '{request.action}' was {status}",
                data={
                    "request_id": request.request_id,
                    "status": status,
                    "approved_by": request.approved_by,
                    "rejection_reason": request.rejection_reason
                }
            )
        except Exception as e:
            logger.error(f"Failed to notify requester: {e}")
    
    async def _notify_timeout(self, request: ApprovalRequest):
        """Notify about timeout."""
        if not self.notification_service:
            return
        
        # Notify requester
        try:
            await self.notification_service.create_notification(
                user_id=request.requester_id,
                notification_type="approval_timeout",
                title="Approval Request Timeout",
                message=f"Approval request for '{request.action}' has timed out",
                data={"request_id": request.request_id}
            )
        except Exception as e:
            logger.error(f"Failed to notify timeout: {e}")
    
    async def _notify_feedback_request(self, request: FeedbackRequest):
        """Send feedback request notifications."""
        if not self.notification_service:
            return
        
        for responder_id in request.responder_ids:
            try:
                await self.notification_service.create_notification(
                    user_id=responder_id,
                    notification_type="feedback_request",
                    title="Feedback Requested",
                    message=f"Your feedback is requested for execution {request.execution_id}",
                    data={
                        "request_id": request.request_id,
                        "execution_id": request.execution_id,
                        "questions_count": len(request.questions),
                        "expires_at": request.expires_at.isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to notify responder {responder_id}: {e}")
    
    async def _cache_approval_request(self, request: ApprovalRequest):
        """Cache approval request in Redis."""
        if not self.cache_manager:
            return
        
        try:
            cache_key = f"approval_request:{request.request_id}"
            cache_data = {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "execution_id": request.execution_id,
                "action": request.action,
                "status": request.status.value,
                "approved_by": request.approved_by,
                "approved_at": request.approved_at.isoformat() if request.approved_at else None,
                "rejection_reason": request.rejection_reason,
                "response_data": request.response_data
            }
            
            await self.cache_manager.set(
                cache_key,
                json.dumps(cache_data),
                expire=request.timeout_seconds
            )
        except Exception as e:
            logger.error(f"Failed to cache approval request: {e}")
    
    async def _get_cached_approval_request(
        self,
        request_id: str
    ) -> Optional[ApprovalRequest]:
        """Get approval request from cache."""
        if not self.cache_manager:
            return None
        
        try:
            cache_key = f"approval_request:{request_id}"
            cached_data = await self.cache_manager.get(cache_key)
            
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            
            # Reconstruct request (simplified)
            request = self.approval_requests.get(request_id)
            if request:
                request.status = ApprovalStatus(data["status"])
                request.approved_by = data.get("approved_by")
                if data.get("approved_at"):
                    request.approved_at = datetime.fromisoformat(data["approved_at"])
                request.rejection_reason = data.get("rejection_reason")
                request.response_data = data.get("response_data")
                return request
            
            return None
        except Exception as e:
            logger.error(f"Failed to get cached approval request: {e}")
            return None
    
    def get_pending_approvals(
        self,
        approver_id: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """
        Get pending approval requests.
        
        Args:
            approver_id: Filter by approver ID
            
        Returns:
            List of pending approval requests
        """
        pending = [
            req for req in self.approval_requests.values()
            if req.status == ApprovalStatus.PENDING
        ]
        
        if approver_id:
            pending = [
                req for req in pending
                if approver_id in req.approver_ids
            ]
        
        # Sort by priority and creation time
        priority_order = {
            ApprovalPriority.CRITICAL: 0,
            ApprovalPriority.HIGH: 1,
            ApprovalPriority.MEDIUM: 2,
            ApprovalPriority.LOW: 3
        }
        
        pending.sort(
            key=lambda r: (priority_order[r.priority], r.created_at)
        )
        
        return pending


class ApprovalWorkflow:
    """
    Multi-level approval workflow manager.
    
    Supports sequential approval chains where multiple approvers
    must approve in order.
    """
    
    def __init__(self, hitl: HumanInTheLoop):
        """
        Initialize approval workflow.
        
        Args:
            hitl: HumanInTheLoop instance
        """
        self.hitl = hitl
        self.workflows: Dict[str, Dict[str, Any]] = {}
    
    async def create_approval_chain(
        self,
        agent_id: str,
        execution_id: str,
        action: str,
        context: Dict[str, Any],
        requester_id: str,
        approval_chain: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create multi-level approval chain.
        
        Args:
            agent_id: Agent ID
            execution_id: Execution ID
            action: Action requiring approval
            context: Context information
            requester_id: User requesting approval
            approval_chain: List of approval levels:
                [{"approver_ids": [...], "required_approvals": 1, "timeout": 3600}]
            metadata: Additional metadata
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        self.workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "execution_id": execution_id,
            "action": action,
            "context": context,
            "requester_id": requester_id,
            "approval_chain": approval_chain,
            "current_level": 0,
            "completed": False,
            "approved": False,
            "metadata": metadata or {}
        }
        
        logger.info(
            f"Approval chain created: {workflow_id} with {len(approval_chain)} levels"
        )
        
        return workflow_id
    
    async def execute_approval_chain(
        self,
        workflow_id: str
    ) -> bool:
        """
        Execute approval chain.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if all approvals granted
        """
        workflow = self.workflows.get(workflow_id)
        
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        approval_chain = workflow["approval_chain"]
        
        for level_idx, level in enumerate(approval_chain):
            workflow["current_level"] = level_idx
            
            logger.info(
                f"Executing approval level {level_idx + 1}/{len(approval_chain)} "
                f"for workflow {workflow_id}"
            )
            
            # Request approval from this level
            request = await self.hitl.request_approval(
                agent_id=workflow["agent_id"],
                execution_id=workflow["execution_id"],
                action=f"{workflow['action']} (Level {level_idx + 1})",
                context=workflow["context"],
                requester_id=workflow["requester_id"],
                approver_ids=level["approver_ids"],
                timeout_seconds=level.get("timeout", 3600),
                metadata={
                    "workflow_id": workflow_id,
                    "level": level_idx,
                    **workflow["metadata"]
                }
            )
            
            # Wait for approval
            approved = await self.hitl.wait_for_approval(request.request_id)
            
            if not approved:
                workflow["completed"] = True
                workflow["approved"] = False
                logger.info(f"Approval chain {workflow_id} rejected at level {level_idx + 1}")
                return False
        
        # All levels approved
        workflow["completed"] = True
        workflow["approved"] = True
        logger.info(f"Approval chain {workflow_id} fully approved")
        
        return True


# Example usage
EXAMPLE_APPROVAL = {
    "agent_id": "agent_123",
    "execution_id": "exec_456",
    "action": "Deploy to production",
    "context": {"environment": "production", "version": "1.2.3"},
    "requester_id": "user_789",
    "approver_ids": ["manager_1", "manager_2"],
    "priority": "high",
    "timeout_seconds": 7200
}

EXAMPLE_FEEDBACK = {
    "execution_id": "exec_456",
    "questions": [
        {
            "id": "q1",
            "type": "rating",
            "question": "How satisfied are you with the result?",
            "scale": [1, 5]
        },
        {
            "id": "q2",
            "type": "text",
            "question": "What could be improved?"
        },
        {
            "id": "q3",
            "type": "choice",
            "question": "Would you use this agent again?",
            "options": ["Yes", "No", "Maybe"]
        }
    ],
    "responder_ids": ["user_1", "user_2", "user_3"]
}

EXAMPLE_APPROVAL_CHAIN = {
    "approval_chain": [
        {
            "approver_ids": ["team_lead"],
            "required_approvals": 1,
            "timeout": 3600
        },
        {
            "approver_ids": ["manager_1", "manager_2"],
            "required_approvals": 1,
            "timeout": 7200
        },
        {
            "approver_ids": ["director"],
            "required_approvals": 1,
            "timeout": 86400
        }
    ]
}
