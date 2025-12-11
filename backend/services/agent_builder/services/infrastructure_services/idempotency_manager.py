"""
Idempotency Manager

Ensures workflow executions are idempotent by tracking request IDs
and preventing duplicate executions.
"""

import logging
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class IdempotencyStatus(str, Enum):
    """Status of idempotent request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IdempotencyManager:
    """
    Manages idempotency for workflow executions.
    
    Features:
    - Request deduplication via idempotency keys
    - Cached response retrieval for duplicate requests
    - Automatic cleanup of old entries
    - Support for both Redis and in-memory storage
    """
    
    def __init__(self, redis_client=None, ttl_hours: int = 24):
        """
        Initialize idempotency manager.
        
        Args:
            redis_client: Optional Redis client
            ttl_hours: Time-to-live for idempotency records
        """
        self.redis = redis_client
        self.ttl_seconds = ttl_hours * 3600
        self._local_store: Dict[str, Dict[str, Any]] = {}
    
    def generate_key(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """
        Generate idempotency key from request parameters.
        
        Args:
            workflow_id: Workflow ID
            input_data: Input data
            user_id: Optional user ID
            
        Returns:
            Idempotency key
        """
        # Create deterministic hash of input
        key_data = {
            "workflow_id": workflow_id,
            "input_data": input_data,
            "user_id": user_id,
        }
        
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:32]
        
        return f"idempotency:{workflow_id}:{key_hash}"
    
    async def check_and_set(
        self,
        idempotency_key: str,
        execution_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if request is duplicate and set processing status.
        
        Args:
            idempotency_key: Idempotency key
            execution_id: New execution ID
            
        Returns:
            Existing record if duplicate, None if new request
        """
        # Check existing record
        existing = await self._get_record(idempotency_key)
        
        if existing:
            status = existing.get("status")
            
            # If completed or failed, return cached response
            if status in [IdempotencyStatus.COMPLETED.value, IdempotencyStatus.FAILED.value]:
                logger.info(f"Idempotent request found: {idempotency_key} -> {existing['execution_id']}")
                return existing
            
            # If still processing, return existing execution info
            if status == IdempotencyStatus.PROCESSING.value:
                # Check if processing is stale (> 5 minutes)
                created_at = datetime.fromisoformat(existing["created_at"])
                if datetime.utcnow() - created_at > timedelta(minutes=5):
                    logger.warning(f"Stale processing record found: {idempotency_key}")
                    # Allow retry for stale records
                else:
                    logger.info(f"Request already processing: {idempotency_key}")
                    return existing
        
        # Set new record
        record = {
            "idempotency_key": idempotency_key,
            "execution_id": execution_id,
            "status": IdempotencyStatus.PROCESSING.value,
            "created_at": datetime.utcnow().isoformat(),
            "response": None,
        }
        
        await self._set_record(idempotency_key, record)
        logger.debug(f"New idempotency record: {idempotency_key}")
        
        return None
    
    async def complete(
        self,
        idempotency_key: str,
        response: Dict[str, Any],
        success: bool = True,
    ):
        """
        Mark request as completed with response.
        
        Args:
            idempotency_key: Idempotency key
            response: Response to cache
            success: Whether execution succeeded
        """
        record = await self._get_record(idempotency_key)
        if not record:
            logger.warning(f"No record found for completion: {idempotency_key}")
            return
        
        record["status"] = (
            IdempotencyStatus.COMPLETED.value if success
            else IdempotencyStatus.FAILED.value
        )
        record["response"] = response
        record["completed_at"] = datetime.utcnow().isoformat()
        
        await self._set_record(idempotency_key, record)
        logger.debug(f"Idempotency record completed: {idempotency_key}")
    
    async def get_cached_response(
        self,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for idempotency key.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            Cached response or None
        """
        record = await self._get_record(idempotency_key)
        if record and record.get("status") == IdempotencyStatus.COMPLETED.value:
            return record.get("response")
        return None
    
    async def invalidate(self, idempotency_key: str):
        """
        Invalidate an idempotency record.
        
        Args:
            idempotency_key: Key to invalidate
        """
        if self.redis:
            try:
                await self.redis.delete(idempotency_key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        self._local_store.pop(idempotency_key, None)
        logger.debug(f"Idempotency record invalidated: {idempotency_key}")
    
    async def _get_record(self, key: str) -> Optional[Dict[str, Any]]:
        """Get record from storage."""
        if self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        return self._local_store.get(key)
    
    async def _set_record(self, key: str, record: Dict[str, Any]):
        """Set record in storage."""
        self._local_store[key] = record
        
        if self.redis:
            try:
                await self.redis.set(
                    key,
                    json.dumps(record, default=str),
                    ex=self.ttl_seconds
                )
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired local records.
        
        Returns:
            Number of records cleaned
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        cleaned = 0
        
        for key, record in list(self._local_store.items()):
            created_at = datetime.fromisoformat(record["created_at"])
            if created_at < cutoff:
                del self._local_store[key]
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned {cleaned} expired idempotency records")
        
        return cleaned


# Global idempotency manager
_idempotency_manager: Optional[IdempotencyManager] = None


def get_idempotency_manager(redis_client=None) -> IdempotencyManager:
    """Get or create global idempotency manager."""
    global _idempotency_manager
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyManager(redis_client)
    return _idempotency_manager
