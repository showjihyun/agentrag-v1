"""
Checkpoint Recovery System

Provides robust checkpoint and recovery mechanisms for workflow executions:
- Automatic checkpoint creation
- State restoration from checkpoints
- Partial execution recovery
- Checkpoint cleanup and management
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class CheckpointType(str, Enum):
    """Types of checkpoints."""
    AUTO = "auto"           # Automatic periodic checkpoint
    NODE = "node"           # After node completion
    MANUAL = "manual"       # User-triggered
    ERROR = "error"         # Before error handling
    PAUSE = "pause"         # On pause request


@dataclass
class Checkpoint:
    """Represents a workflow execution checkpoint."""
    id: str
    execution_id: str
    workflow_id: str
    checkpoint_type: CheckpointType
    name: str
    
    # State snapshot
    current_node_id: Optional[str]
    completed_nodes: List[str]
    node_results: Dict[str, Any]
    execution_data: Dict[str, Any]
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "checkpoint_type": self.checkpoint_type.value,
            "name": self.name,
            "current_node_id": self.current_node_id,
            "completed_nodes": self.completed_nodes,
            "node_results": self.node_results,
            "execution_data": self.execution_data,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            id=data["id"],
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            checkpoint_type=CheckpointType(data["checkpoint_type"]),
            name=data["name"],
            current_node_id=data.get("current_node_id"),
            completed_nodes=data.get("completed_nodes", []),
            node_results=data.get("node_results", {}),
            execution_data=data.get("execution_data", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RecoveryPlan:
    """Plan for recovering from a checkpoint."""
    checkpoint: Checkpoint
    nodes_to_skip: List[str]
    nodes_to_execute: List[str]
    initial_data: Dict[str, Any]
    recovery_strategy: str  # "resume", "retry_failed", "restart_from"


class CheckpointManager:
    """
    Manages checkpoints for workflow executions.
    
    Features:
    - Automatic checkpoint creation at configurable intervals
    - Multiple checkpoint types (auto, node, manual, error)
    - Efficient storage with Redis and file backup
    - Checkpoint cleanup policies
    """
    
    def __init__(
        self,
        redis_client=None,
        max_checkpoints_per_execution: int = 10,
        auto_checkpoint_interval: int = 5,  # Every N nodes
        checkpoint_ttl_hours: int = 24,
    ):
        self.redis = redis_client
        self.max_checkpoints = max_checkpoints_per_execution
        self.auto_interval = auto_checkpoint_interval
        self.checkpoint_ttl = timedelta(hours=checkpoint_ttl_hours)
        
        self._local_checkpoints: Dict[str, List[Checkpoint]] = {}
        self._node_counter: Dict[str, int] = {}
    
    async def create_checkpoint(
        self,
        execution_id: str,
        workflow_id: str,
        checkpoint_type: CheckpointType,
        name: str,
        current_node_id: Optional[str],
        completed_nodes: List[str],
        node_results: Dict[str, Any],
        execution_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """
        Create a new checkpoint.
        
        Args:
            execution_id: Execution ID
            workflow_id: Workflow ID
            checkpoint_type: Type of checkpoint
            name: Checkpoint name
            current_node_id: Current node being executed
            completed_nodes: List of completed node IDs
            node_results: Results from completed nodes
            execution_data: Current execution data/context
            metadata: Additional metadata
            
        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            workflow_id=workflow_id,
            checkpoint_type=checkpoint_type,
            name=name,
            current_node_id=current_node_id,
            completed_nodes=completed_nodes.copy(),
            node_results=node_results.copy(),
            execution_data=execution_data.copy(),
            metadata=metadata or {},
        )
        
        await self._save_checkpoint(checkpoint)
        await self._enforce_limits(execution_id)
        
        logger.info(
            f"Created checkpoint '{name}' for execution {execution_id} "
            f"(type={checkpoint_type.value}, nodes={len(completed_nodes)})"
        )
        
        return checkpoint
    
    async def should_auto_checkpoint(self, execution_id: str) -> bool:
        """Check if auto checkpoint should be created."""
        count = self._node_counter.get(execution_id, 0) + 1
        self._node_counter[execution_id] = count
        return count % self.auto_interval == 0
    
    async def get_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        # Check Redis
        if self.redis:
            try:
                data = await self.redis.get(f"checkpoint:{checkpoint_id}")
                if data:
                    return Checkpoint.from_dict(json.loads(data))
            except Exception as e:
                logger.warning(f"Redis get checkpoint failed: {e}")
        
        # Check local
        for checkpoints in self._local_checkpoints.values():
            for cp in checkpoints:
                if cp.id == checkpoint_id:
                    return cp
        
        return None
    
    async def get_latest_checkpoint(
        self,
        execution_id: str,
        checkpoint_type: Optional[CheckpointType] = None,
    ) -> Optional[Checkpoint]:
        """Get the latest checkpoint for an execution."""
        checkpoints = await self.list_checkpoints(execution_id)
        
        if checkpoint_type:
            checkpoints = [cp for cp in checkpoints if cp.checkpoint_type == checkpoint_type]
        
        if not checkpoints:
            return None
        
        return max(checkpoints, key=lambda cp: cp.created_at)
    
    async def list_checkpoints(
        self,
        execution_id: str,
    ) -> List[Checkpoint]:
        """List all checkpoints for an execution."""
        checkpoints = []
        
        # Check Redis
        if self.redis:
            try:
                keys = await self.redis.keys(f"checkpoint:*:{execution_id}")
                for key in keys:
                    data = await self.redis.get(key)
                    if data:
                        checkpoints.append(Checkpoint.from_dict(json.loads(data)))
            except Exception as e:
                logger.warning(f"Redis list checkpoints failed: {e}")
        
        # Add local checkpoints
        local = self._local_checkpoints.get(execution_id, [])
        checkpoint_ids = {cp.id for cp in checkpoints}
        for cp in local:
            if cp.id not in checkpoint_ids:
                checkpoints.append(cp)
        
        return sorted(checkpoints, key=lambda cp: cp.created_at)
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        # Delete from Redis
        if self.redis:
            try:
                await self.redis.delete(f"checkpoint:{checkpoint_id}")
            except Exception as e:
                logger.warning(f"Redis delete checkpoint failed: {e}")
        
        # Delete from local
        for execution_id, checkpoints in self._local_checkpoints.items():
            self._local_checkpoints[execution_id] = [
                cp for cp in checkpoints if cp.id != checkpoint_id
            ]
        
        return True
    
    async def cleanup_expired(self) -> int:
        """Clean up expired checkpoints."""
        cutoff = datetime.utcnow() - self.checkpoint_ttl
        deleted = 0
        
        for execution_id, checkpoints in list(self._local_checkpoints.items()):
            expired = [cp for cp in checkpoints if cp.created_at < cutoff]
            for cp in expired:
                await self.delete_checkpoint(cp.id)
                deleted += 1
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired checkpoints")
        
        return deleted
    
    async def _save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to storage."""
        execution_id = checkpoint.execution_id
        
        # Save to local
        if execution_id not in self._local_checkpoints:
            self._local_checkpoints[execution_id] = []
        self._local_checkpoints[execution_id].append(checkpoint)
        
        # Save to Redis
        if self.redis:
            try:
                key = f"checkpoint:{checkpoint.id}:{execution_id}"
                await self.redis.set(
                    key,
                    json.dumps(checkpoint.to_dict(), default=str),
                    ex=int(self.checkpoint_ttl.total_seconds()),
                )
            except Exception as e:
                logger.warning(f"Redis save checkpoint failed: {e}")
    
    async def _enforce_limits(self, execution_id: str):
        """Enforce checkpoint limits per execution."""
        checkpoints = await self.list_checkpoints(execution_id)
        
        if len(checkpoints) > self.max_checkpoints:
            # Keep manual and error checkpoints, remove oldest auto checkpoints
            auto_checkpoints = [
                cp for cp in checkpoints
                if cp.checkpoint_type == CheckpointType.AUTO
            ]
            
            # Sort by age and remove oldest
            auto_checkpoints.sort(key=lambda cp: cp.created_at)
            to_remove = len(checkpoints) - self.max_checkpoints
            
            for cp in auto_checkpoints[:to_remove]:
                await self.delete_checkpoint(cp.id)


class RecoveryManager:
    """
    Manages recovery from checkpoints.
    
    Features:
    - Multiple recovery strategies
    - Automatic recovery plan generation
    - Partial execution support
    - Recovery validation
    """
    
    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        state_manager=None,
    ):
        self.checkpoint_manager = checkpoint_manager
        self.state_manager = state_manager
    
    async def create_recovery_plan(
        self,
        execution_id: str,
        workflow_nodes: List[Dict],
        checkpoint_id: Optional[str] = None,
        strategy: str = "resume",
    ) -> Optional[RecoveryPlan]:
        """
        Create a recovery plan from a checkpoint.
        
        Args:
            execution_id: Execution ID
            workflow_nodes: List of workflow node definitions
            checkpoint_id: Specific checkpoint to recover from (or latest)
            strategy: Recovery strategy ("resume", "retry_failed", "restart_from")
            
        Returns:
            Recovery plan or None if no checkpoint available
        """
        # Get checkpoint
        if checkpoint_id:
            checkpoint = await self.checkpoint_manager.get_checkpoint(checkpoint_id)
        else:
            checkpoint = await self.checkpoint_manager.get_latest_checkpoint(execution_id)
        
        if not checkpoint:
            logger.warning(f"No checkpoint found for execution {execution_id}")
            return None
        
        # Build node ID set
        all_node_ids = {node["id"] for node in workflow_nodes}
        completed_nodes = set(checkpoint.completed_nodes)
        
        # Determine nodes to execute based on strategy
        if strategy == "resume":
            # Continue from where we left off
            nodes_to_skip = list(completed_nodes)
            nodes_to_execute = list(all_node_ids - completed_nodes)
        
        elif strategy == "retry_failed":
            # Retry the failed node and continue
            failed_node = checkpoint.current_node_id
            nodes_to_skip = [n for n in completed_nodes if n != failed_node]
            nodes_to_execute = list(all_node_ids - set(nodes_to_skip))
        
        elif strategy == "restart_from":
            # Restart from the checkpoint node
            restart_node = checkpoint.current_node_id
            # Find all nodes that depend on restart_node
            nodes_to_skip = self._get_nodes_before(restart_node, workflow_nodes)
            nodes_to_execute = list(all_node_ids - set(nodes_to_skip))
        
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")
        
        # Build initial data from checkpoint
        initial_data = checkpoint.execution_data.copy()
        for node_id, result in checkpoint.node_results.items():
            if node_id in nodes_to_skip:
                if isinstance(result, dict) and "result" in result:
                    initial_data.update(result["result"] if isinstance(result["result"], dict) else {})
        
        return RecoveryPlan(
            checkpoint=checkpoint,
            nodes_to_skip=nodes_to_skip,
            nodes_to_execute=nodes_to_execute,
            initial_data=initial_data,
            recovery_strategy=strategy,
        )
    
    async def execute_recovery(
        self,
        recovery_plan: RecoveryPlan,
        executor,
    ) -> Dict[str, Any]:
        """
        Execute a recovery plan.
        
        Args:
            recovery_plan: Recovery plan to execute
            executor: Workflow executor instance
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing recovery for {recovery_plan.checkpoint.execution_id} "
            f"(strategy={recovery_plan.recovery_strategy}, "
            f"skip={len(recovery_plan.nodes_to_skip)}, "
            f"execute={len(recovery_plan.nodes_to_execute)})"
        )
        
        # Update state manager if available
        if self.state_manager:
            await self.state_manager.transition_state(
                recovery_plan.checkpoint.execution_id,
                "running",
                f"Recovered from checkpoint: {recovery_plan.checkpoint.name}",
            )
        
        # Execute with recovery context
        result = await executor.execute_with_recovery(
            input_data=recovery_plan.initial_data,
            skip_nodes=set(recovery_plan.nodes_to_skip),
            node_results=recovery_plan.checkpoint.node_results,
        )
        
        return result
    
    def _get_nodes_before(
        self,
        node_id: str,
        workflow_nodes: List[Dict],
    ) -> List[str]:
        """Get all nodes that come before a given node in the workflow."""
        # This is a simplified implementation
        # A full implementation would use the edge graph
        nodes_before = []
        found = False
        
        for node in workflow_nodes:
            if node["id"] == node_id:
                found = True
                break
            nodes_before.append(node["id"])
        
        return nodes_before if found else []
    
    async def validate_recovery(
        self,
        recovery_plan: RecoveryPlan,
        workflow_nodes: List[Dict],
    ) -> Dict[str, Any]:
        """
        Validate a recovery plan.
        
        Args:
            recovery_plan: Recovery plan to validate
            workflow_nodes: Current workflow nodes
            
        Returns:
            Validation result with any issues
        """
        issues = []
        
        # Check if checkpoint is still valid
        checkpoint = recovery_plan.checkpoint
        current_node_ids = {node["id"] for node in workflow_nodes}
        
        # Check for missing nodes
        for node_id in checkpoint.completed_nodes:
            if node_id not in current_node_ids:
                issues.append(f"Completed node '{node_id}' no longer exists in workflow")
        
        # Check for new required nodes
        for node_id in recovery_plan.nodes_to_execute:
            if node_id not in current_node_ids:
                issues.append(f"Node to execute '{node_id}' not found in workflow")
        
        # Check checkpoint age
        age = datetime.utcnow() - checkpoint.created_at
        if age > timedelta(hours=24):
            issues.append(f"Checkpoint is {age.total_seconds() / 3600:.1f} hours old")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "checkpoint_age_hours": age.total_seconds() / 3600,
            "nodes_to_skip": len(recovery_plan.nodes_to_skip),
            "nodes_to_execute": len(recovery_plan.nodes_to_execute),
        }


# Global instances
_checkpoint_manager: Optional[CheckpointManager] = None
_recovery_manager: Optional[RecoveryManager] = None


def get_checkpoint_manager(redis_client=None) -> CheckpointManager:
    """Get or create checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(redis_client)
    return _checkpoint_manager


def get_recovery_manager(
    checkpoint_manager: Optional[CheckpointManager] = None,
    state_manager=None,
) -> RecoveryManager:
    """Get or create recovery manager."""
    global _recovery_manager
    if _recovery_manager is None:
        cp_manager = checkpoint_manager or get_checkpoint_manager()
        _recovery_manager = RecoveryManager(cp_manager, state_manager)
    return _recovery_manager
