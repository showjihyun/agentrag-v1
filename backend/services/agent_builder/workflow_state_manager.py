"""
Workflow State Manager

Centralized state management for workflow executions with Redis-backed
distributed state and proper state machine transitions.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """Workflow execution states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# Valid state transitions
STATE_TRANSITIONS: Dict[WorkflowState, List[WorkflowState]] = {
    WorkflowState.PENDING: [WorkflowState.QUEUED, WorkflowState.CANCELLED],
    WorkflowState.QUEUED: [WorkflowState.RUNNING, WorkflowState.CANCELLED],
    WorkflowState.RUNNING: [
        WorkflowState.PAUSED,
        WorkflowState.WAITING_APPROVAL,
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
        WorkflowState.TIMEOUT,
    ],
    WorkflowState.PAUSED: [WorkflowState.RUNNING, WorkflowState.CANCELLED],
    WorkflowState.WAITING_APPROVAL: [
        WorkflowState.RUNNING,
        WorkflowState.CANCELLED,
        WorkflowState.TIMEOUT,
    ],
    WorkflowState.COMPLETED: [],  # Terminal state
    WorkflowState.FAILED: [],  # Terminal state
    WorkflowState.CANCELLED: [],  # Terminal state
    WorkflowState.TIMEOUT: [],  # Terminal state
}


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class WorkflowStateManager:
    """
    Manages workflow execution state with Redis-backed distributed state.
    
    Features:
    - State machine with valid transitions
    - Distributed state via Redis
    - Checkpoint/restore for long-running workflows
    - State history tracking
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize state manager.
        
        Args:
            redis_client: Optional Redis client for distributed state
        """
        self.redis = redis_client
        self._local_state: Dict[str, Dict[str, Any]] = {}
        self._state_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def initialize_execution(
        self,
        execution_id: str,
        workflow_id: str,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a new workflow execution state.
        
        Args:
            execution_id: Unique execution ID
            workflow_id: Workflow ID
            input_data: Input data for execution
            metadata: Optional metadata
            
        Returns:
            Initial state dict
        """
        state = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "state": WorkflowState.PENDING.value,
            "input_data": input_data,
            "output_data": None,
            "current_node_id": None,
            "node_results": {},
            "checkpoints": [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        
        await self._save_state(execution_id, state)
        await self._record_history(execution_id, WorkflowState.PENDING, "Execution initialized")
        
        return state
    
    async def transition_state(
        self,
        execution_id: str,
        new_state: WorkflowState,
        reason: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transition execution to a new state.
        
        Args:
            execution_id: Execution ID
            new_state: Target state
            reason: Optional reason for transition
            error: Optional error message (for failed state)
            
        Returns:
            Updated state dict
            
        Raises:
            InvalidStateTransitionError: If transition is not valid
        """
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
        
        current_state = WorkflowState(state["state"])
        
        # Validate transition
        valid_transitions = STATE_TRANSITIONS.get(current_state, [])
        if new_state not in valid_transitions:
            raise InvalidStateTransitionError(
                f"Cannot transition from {current_state.value} to {new_state.value}. "
                f"Valid transitions: {[s.value for s in valid_transitions]}"
            )
        
        # Update state
        state["state"] = new_state.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        if new_state == WorkflowState.RUNNING and not state["started_at"]:
            state["started_at"] = datetime.utcnow().isoformat()
        
        if new_state in [WorkflowState.COMPLETED, WorkflowState.FAILED, 
                         WorkflowState.CANCELLED, WorkflowState.TIMEOUT]:
            state["completed_at"] = datetime.utcnow().isoformat()
        
        if error:
            state["error"] = error
        
        await self._save_state(execution_id, state)
        await self._record_history(execution_id, new_state, reason or f"Transitioned to {new_state.value}")
        
        logger.info(f"Execution {execution_id}: {current_state.value} -> {new_state.value}")
        
        return state
    
    async def update_node_result(
        self,
        execution_id: str,
        node_id: str,
        result: Any,
        status: str = "success",
    ) -> Dict[str, Any]:
        """
        Update result for a specific node.
        
        Args:
            execution_id: Execution ID
            node_id: Node ID
            result: Node execution result
            status: Node status
            
        Returns:
            Updated state dict
        """
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
        
        state["node_results"][node_id] = {
            "result": result,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        state["current_node_id"] = node_id
        state["updated_at"] = datetime.utcnow().isoformat()
        
        await self._save_state(execution_id, state)
        
        return state
    
    async def create_checkpoint(
        self,
        execution_id: str,
        checkpoint_name: str,
    ) -> str:
        """
        Create a checkpoint for the current execution state.
        
        Args:
            execution_id: Execution ID
            checkpoint_name: Name for the checkpoint
            
        Returns:
            Checkpoint ID
        """
        import uuid
        
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
        
        checkpoint_id = str(uuid.uuid4())
        checkpoint = {
            "id": checkpoint_id,
            "name": checkpoint_name,
            "state_snapshot": state.copy(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        state["checkpoints"].append(checkpoint)
        await self._save_state(execution_id, state)
        
        logger.info(f"Created checkpoint {checkpoint_id} for execution {execution_id}")
        
        return checkpoint_id
    
    async def restore_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str,
    ) -> Dict[str, Any]:
        """
        Restore execution state from a checkpoint.
        
        Args:
            execution_id: Execution ID
            checkpoint_id: Checkpoint ID to restore
            
        Returns:
            Restored state dict
        """
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Find checkpoint
        checkpoint = next(
            (cp for cp in state["checkpoints"] if cp["id"] == checkpoint_id),
            None
        )
        
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # Restore state (preserve checkpoints and metadata)
        restored = checkpoint["state_snapshot"].copy()
        restored["checkpoints"] = state["checkpoints"]
        restored["metadata"]["restored_from"] = checkpoint_id
        restored["updated_at"] = datetime.utcnow().isoformat()
        
        await self._save_state(execution_id, restored)
        await self._record_history(
            execution_id,
            WorkflowState(restored["state"]),
            f"Restored from checkpoint: {checkpoint['name']}"
        )
        
        return restored
    
    async def get_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution state."""
        if self.redis:
            try:
                data = await self.redis.get(f"workflow:state:{execution_id}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed, using local state: {e}")
        
        return self._local_state.get(execution_id)
    
    async def get_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get state transition history."""
        if self.redis:
            try:
                data = await self.redis.lrange(f"workflow:history:{execution_id}", 0, -1)
                if data:
                    return [json.loads(item) for item in data]
            except Exception as e:
                logger.warning(f"Redis lrange failed: {e}")
        
        return self._state_history.get(execution_id, [])
    
    async def _save_state(self, execution_id: str, state: Dict[str, Any]):
        """Save state to storage."""
        self._local_state[execution_id] = state
        
        if self.redis:
            try:
                await self.redis.set(
                    f"workflow:state:{execution_id}",
                    json.dumps(state, default=str),
                    ex=86400 * 7  # 7 days TTL
                )
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
    
    async def _record_history(
        self,
        execution_id: str,
        state: WorkflowState,
        message: str,
    ):
        """Record state transition in history."""
        entry = {
            "state": state.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if execution_id not in self._state_history:
            self._state_history[execution_id] = []
        self._state_history[execution_id].append(entry)
        
        if self.redis:
            try:
                await self.redis.rpush(
                    f"workflow:history:{execution_id}",
                    json.dumps(entry)
                )
                await self.redis.expire(f"workflow:history:{execution_id}", 86400 * 7)
            except Exception as e:
                logger.warning(f"Redis rpush failed: {e}")
    
    async def cleanup_expired(self, max_age_days: int = 7) -> int:
        """
        Clean up expired execution states.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of cleaned up executions
        """
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned = 0
        
        for execution_id, state in list(self._local_state.items()):
            completed_at = state.get("completed_at")
            if completed_at:
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                if completed_dt < cutoff:
                    del self._local_state[execution_id]
                    self._state_history.pop(execution_id, None)
                    cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired execution states")
        
        return cleaned


# Global state manager instance
_state_manager: Optional[WorkflowStateManager] = None


def get_state_manager(redis_client=None) -> WorkflowStateManager:
    """Get or create global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = WorkflowStateManager(redis_client)
    return _state_manager
