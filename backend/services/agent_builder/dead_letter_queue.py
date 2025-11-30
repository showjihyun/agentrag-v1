"""
Dead Letter Queue (DLQ) for Failed Workflow Executions

Captures failed executions for later analysis and retry.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class DLQEntryStatus(str, Enum):
    """Status of DLQ entry."""
    PENDING = "pending"
    RETRYING = "retrying"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class DeadLetterEntry:
    """Represents a failed execution in the DLQ."""
    
    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        error_message: str,
        error_type: str,
        input_data: Dict[str, Any],
        execution_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid.uuid4())
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.error_message = error_message
        self.error_type = error_type
        self.input_data = input_data
        self.execution_context = execution_context or {}
        self.metadata = metadata or {}
        self.status = DLQEntryStatus.PENDING
        self.retry_count = 0
        self.max_retries = 3
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None
        self.resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "input_data": self.input_data,
            "execution_context": self.execution_context,
            "metadata": self.metadata,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeadLetterEntry":
        """Create from dictionary."""
        entry = cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            error_message=data["error_message"],
            error_type=data["error_type"],
            input_data=data["input_data"],
            execution_context=data.get("execution_context", {}),
            metadata=data.get("metadata", {}),
        )
        entry.id = data["id"]
        entry.status = DLQEntryStatus(data["status"])
        entry.retry_count = data.get("retry_count", 0)
        entry.max_retries = data.get("max_retries", 3)
        entry.created_at = datetime.fromisoformat(data["created_at"])
        entry.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("resolved_at"):
            entry.resolved_at = datetime.fromisoformat(data["resolved_at"])
        entry.resolution_notes = data.get("resolution_notes")
        return entry


class DeadLetterQueue:
    """
    Dead Letter Queue for failed workflow executions.
    
    Features:
    - Capture failed executions with full context
    - Automatic retry with backoff
    - Manual resolution workflow
    - Metrics and alerting integration
    """
    
    def __init__(self, redis_client=None, db_session=None):
        """
        Initialize DLQ.
        
        Args:
            redis_client: Optional Redis client for queue storage
            db_session: Optional DB session for persistence
        """
        self.redis = redis_client
        self.db = db_session
        self._local_queue: Dict[str, DeadLetterEntry] = {}
        self._queue_key = "dlq:workflow:entries"
    
    async def enqueue(
        self,
        execution_id: str,
        workflow_id: str,
        error: Exception,
        input_data: Dict[str, Any],
        execution_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeadLetterEntry:
        """
        Add failed execution to DLQ.
        
        Args:
            execution_id: Failed execution ID
            workflow_id: Workflow ID
            error: Exception that caused failure
            input_data: Original input data
            execution_context: Execution context at failure
            metadata: Additional metadata
            
        Returns:
            Created DLQ entry
        """
        entry = DeadLetterEntry(
            execution_id=execution_id,
            workflow_id=workflow_id,
            error_message=str(error),
            error_type=type(error).__name__,
            input_data=input_data,
            execution_context=execution_context,
            metadata=metadata,
        )
        
        await self._save_entry(entry)
        
        logger.warning(
            f"Added to DLQ: execution={execution_id}, "
            f"workflow={workflow_id}, error={type(error).__name__}"
        )
        
        return entry
    
    async def get_entry(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """Get DLQ entry by ID."""
        if self.redis:
            try:
                data = await self.redis.hget(self._queue_key, entry_id)
                if data:
                    return DeadLetterEntry.from_dict(json.loads(data))
            except Exception as e:
                logger.warning(f"Redis hget failed: {e}")
        
        return self._local_queue.get(entry_id)
    
    async def list_entries(
        self,
        status: Optional[DLQEntryStatus] = None,
        workflow_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DeadLetterEntry]:
        """
        List DLQ entries with filtering.
        
        Args:
            status: Filter by status
            workflow_id: Filter by workflow
            limit: Max entries to return
            offset: Pagination offset
            
        Returns:
            List of DLQ entries
        """
        entries = []
        
        if self.redis:
            try:
                all_data = await self.redis.hgetall(self._queue_key)
                for data in all_data.values():
                    entry = DeadLetterEntry.from_dict(json.loads(data))
                    entries.append(entry)
            except Exception as e:
                logger.warning(f"Redis hgetall failed: {e}")
                entries = list(self._local_queue.values())
        else:
            entries = list(self._local_queue.values())
        
        # Apply filters
        if status:
            entries = [e for e in entries if e.status == status]
        if workflow_id:
            entries = [e for e in entries if e.workflow_id == workflow_id]
        
        # Sort by created_at descending
        entries.sort(key=lambda e: e.created_at, reverse=True)
        
        # Apply pagination
        return entries[offset:offset + limit]
    
    async def mark_retrying(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """
        Mark entry as being retried.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Updated entry or None
        """
        entry = await self.get_entry(entry_id)
        if not entry:
            return None
        
        if entry.retry_count >= entry.max_retries:
            logger.warning(f"DLQ entry {entry_id} exceeded max retries")
            return None
        
        entry.status = DLQEntryStatus.RETRYING
        entry.retry_count += 1
        entry.updated_at = datetime.utcnow()
        
        await self._save_entry(entry)
        
        logger.info(f"DLQ entry {entry_id} marked for retry ({entry.retry_count}/{entry.max_retries})")
        
        return entry
    
    async def resolve(
        self,
        entry_id: str,
        notes: Optional[str] = None,
        discard: bool = False,
    ) -> Optional[DeadLetterEntry]:
        """
        Resolve a DLQ entry.
        
        Args:
            entry_id: Entry ID
            notes: Resolution notes
            discard: Whether to discard (vs resolve)
            
        Returns:
            Updated entry or None
        """
        entry = await self.get_entry(entry_id)
        if not entry:
            return None
        
        entry.status = DLQEntryStatus.DISCARDED if discard else DLQEntryStatus.RESOLVED
        entry.resolved_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        entry.resolution_notes = notes
        
        await self._save_entry(entry)
        
        logger.info(f"DLQ entry {entry_id} {'discarded' if discard else 'resolved'}")
        
        return entry
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get DLQ statistics.
        
        Returns:
            Statistics dict
        """
        entries = await self.list_entries(limit=10000)
        
        stats = {
            "total": len(entries),
            "by_status": {},
            "by_error_type": {},
            "by_workflow": {},
            "oldest_pending": None,
        }
        
        for entry in entries:
            # By status
            status = entry.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By error type
            error_type = entry.error_type
            stats["by_error_type"][error_type] = stats["by_error_type"].get(error_type, 0) + 1
            
            # By workflow
            workflow = entry.workflow_id
            stats["by_workflow"][workflow] = stats["by_workflow"].get(workflow, 0) + 1
            
            # Oldest pending
            if entry.status == DLQEntryStatus.PENDING:
                if not stats["oldest_pending"] or entry.created_at < datetime.fromisoformat(stats["oldest_pending"]):
                    stats["oldest_pending"] = entry.created_at.isoformat()
        
        return stats
    
    async def cleanup_resolved(self, older_than_days: int = 30) -> int:
        """
        Clean up old resolved entries.
        
        Args:
            older_than_days: Remove entries older than this
            
        Returns:
            Number of entries removed
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        removed = 0
        
        entries = await self.list_entries(limit=10000)
        
        for entry in entries:
            if entry.status in [DLQEntryStatus.RESOLVED, DLQEntryStatus.DISCARDED]:
                if entry.resolved_at and entry.resolved_at < cutoff:
                    await self._delete_entry(entry.id)
                    removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} resolved DLQ entries")
        
        return removed
    
    async def _save_entry(self, entry: DeadLetterEntry):
        """Save entry to storage."""
        self._local_queue[entry.id] = entry
        
        if self.redis:
            try:
                await self.redis.hset(
                    self._queue_key,
                    entry.id,
                    json.dumps(entry.to_dict(), default=str)
                )
            except Exception as e:
                logger.warning(f"Redis hset failed: {e}")
    
    async def _delete_entry(self, entry_id: str):
        """Delete entry from storage."""
        self._local_queue.pop(entry_id, None)
        
        if self.redis:
            try:
                await self.redis.hdel(self._queue_key, entry_id)
            except Exception as e:
                logger.warning(f"Redis hdel failed: {e}")


# Global DLQ instance
_dlq: Optional[DeadLetterQueue] = None


def get_dead_letter_queue(redis_client=None, db_session=None) -> DeadLetterQueue:
    """Get or create global DLQ."""
    global _dlq
    if _dlq is None:
        _dlq = DeadLetterQueue(redis_client, db_session)
    return _dlq
