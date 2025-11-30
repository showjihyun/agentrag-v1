"""
Enhanced Trigger Manager with improved reliability and performance.

Improvements over original TriggerManager:
- Retry logic with exponential backoff
- Rate limiting for webhooks
- Caching for trigger lookups
- Better error handling
- Async database operations
- Trigger metrics collection
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    """Supported trigger types."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    API = "api"
    CHAT = "chat"
    MANUAL = "manual"
    EVENT = "event"


class TriggerStatus(str, Enum):
    """Trigger execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class TriggerMetrics:
    """Metrics for trigger performance monitoring."""
    trigger_id: str
    trigger_type: TriggerType
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0
    avg_duration_ms: float = 0
    last_execution_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    def record_execution(self, success: bool, duration_ms: float, error: Optional[str] = None):
        """Record an execution."""
        self.total_executions += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_executions
        self.last_execution_at = datetime.utcnow()
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            self.last_error = error
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_executions == 0:
            return 100.0
        return (self.successful_executions / self.total_executions) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type.value,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": round(self.success_rate, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "last_error": self.last_error,
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt using exponential backoff."""
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)
        return min(delay, self.max_delay_seconds)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10


class TriggerRateLimiter:
    """
    Rate limiter for trigger executions.
    
    Uses sliding window algorithm for accurate rate limiting.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, trigger_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if trigger execution is allowed.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = datetime.utcnow()
        
        if trigger_id not in self._requests:
            self._requests[trigger_id] = []
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        self._requests[trigger_id] = [
            t for t in self._requests[trigger_id]
            if t > hour_ago
        ]
        
        # Count requests in windows
        requests_last_minute = sum(
            1 for t in self._requests[trigger_id]
            if t > minute_ago
        )
        requests_last_hour = len(self._requests[trigger_id])
        
        # Check limits
        if requests_last_minute >= self.config.requests_per_minute:
            return False, 60
        
        if requests_last_hour >= self.config.requests_per_hour:
            return False, 3600
        
        # Record request
        self._requests[trigger_id].append(now)
        
        return True, None
    
    def get_remaining(self, trigger_id: str) -> Dict[str, int]:
        """Get remaining requests for trigger."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        requests = self._requests.get(trigger_id, [])
        
        requests_last_minute = sum(1 for t in requests if t > minute_ago)
        requests_last_hour = sum(1 for t in requests if t > hour_ago)
        
        return {
            "minute": max(0, self.config.requests_per_minute - requests_last_minute),
            "hour": max(0, self.config.requests_per_hour - requests_last_hour),
        }


class TriggerCache:
    """
    In-memory cache for trigger configurations.
    
    Reduces database lookups for frequently accessed triggers.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        value, expires_at = self._cache[key]
        
        if datetime.utcnow() > expires_at:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        self._cache[key] = (value, expires_at)
    
    def delete(self, key: str):
        """Delete value from cache."""
        self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()


class EnhancedTriggerManager:
    """
    Enhanced trigger manager with reliability features.
    
    Features:
    - Retry with exponential backoff
    - Rate limiting per trigger
    - Caching for trigger lookups
    - Metrics collection
    - Dead letter queue for failed triggers
    """
    
    def __init__(
        self,
        db_session: Session,
        retry_config: Optional[RetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        cache_ttl: int = 300,
    ):
        self.db = db_session
        self.retry_config = retry_config or RetryConfig()
        self.rate_limiter = TriggerRateLimiter(rate_limit_config or RateLimitConfig())
        self.cache = TriggerCache(ttl_seconds=cache_ttl)
        self._metrics: Dict[str, TriggerMetrics] = {}
    
    async def execute_with_retry(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        trigger_data: Dict[str, Any],
        user_id: str,
        trigger_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute trigger with retry logic.
        
        Args:
            workflow_id: Workflow to execute
            trigger_type: Type of trigger
            trigger_data: Trigger payload
            user_id: User ID
            trigger_id: Optional trigger ID
        
        Returns:
            Execution result
        """
        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(
            trigger_id or workflow_id
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for trigger: {trigger_id or workflow_id}"
            )
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": retry_after,
            }
        
        # Execute with retry
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            start_time = datetime.utcnow()
            
            try:
                result = await self._execute_trigger(
                    workflow_id=workflow_id,
                    trigger_type=trigger_type,
                    trigger_data=trigger_data,
                    user_id=user_id,
                    trigger_id=trigger_id,
                )
                
                # Record success metrics
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self._record_metrics(
                    trigger_id=trigger_id or workflow_id,
                    trigger_type=trigger_type,
                    success=True,
                    duration_ms=duration_ms,
                )
                
                return result
                
            except Exception as e:
                last_error = str(e)
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.warning(
                    f"Trigger execution failed (attempt {attempt + 1}/"
                    f"{self.retry_config.max_retries + 1}): {e}"
                )
                
                # Record failure metrics
                self._record_metrics(
                    trigger_id=trigger_id or workflow_id,
                    trigger_type=trigger_type,
                    success=False,
                    duration_ms=duration_ms,
                    error=last_error,
                )
                
                # Check if we should retry
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.get_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Send to dead letter queue
                    await self._send_to_dlq(
                        workflow_id=workflow_id,
                        trigger_type=trigger_type,
                        trigger_data=trigger_data,
                        error=last_error,
                    )
        
        return {
            "success": False,
            "error": f"All retries exhausted: {last_error}",
            "retries": self.retry_config.max_retries,
        }
    
    async def _execute_trigger(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        trigger_data: Dict[str, Any],
        user_id: str,
        trigger_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute trigger (internal method)."""
        from backend.core.triggers.manager import TriggerManager
        
        # Use original TriggerManager for actual execution
        manager = TriggerManager(self.db)
        
        return await manager.execute_trigger(
            workflow_id=workflow_id,
            trigger_type=trigger_type.value,
            trigger_data=trigger_data,
            user_id=user_id,
            trigger_id=trigger_id,
        )
    
    async def _send_to_dlq(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        trigger_data: Dict[str, Any],
        error: str,
    ):
        """Send failed trigger to dead letter queue."""
        logger.error(
            f"Sending trigger to DLQ: workflow_id={workflow_id}, "
            f"type={trigger_type.value}, error={error}"
        )
        
        try:
            from backend.services.agent_builder.dead_letter_queue import DeadLetterQueue
            
            dlq = DeadLetterQueue(self.db)
            await dlq.add_message(
                message_type="trigger_execution",
                message_data={
                    "workflow_id": workflow_id,
                    "trigger_type": trigger_type.value,
                    "trigger_data": trigger_data,
                },
                error_message=error,
                source="trigger_manager",
            )
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def _record_metrics(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        """Record trigger execution metrics."""
        if trigger_id not in self._metrics:
            self._metrics[trigger_id] = TriggerMetrics(
                trigger_id=trigger_id,
                trigger_type=trigger_type,
            )
        
        self._metrics[trigger_id].record_execution(
            success=success,
            duration_ms=duration_ms,
            error=error,
        )
    
    def get_metrics(self, trigger_id: Optional[str] = None) -> Dict[str, Any]:
        """Get trigger metrics."""
        if trigger_id:
            metrics = self._metrics.get(trigger_id)
            return metrics.to_dict() if metrics else {}
        
        return {
            tid: m.to_dict()
            for tid, m in self._metrics.items()
        }
    
    def get_rate_limit_status(self, trigger_id: str) -> Dict[str, Any]:
        """Get rate limit status for trigger."""
        remaining = self.rate_limiter.get_remaining(trigger_id)
        return {
            "trigger_id": trigger_id,
            "remaining_requests": remaining,
            "limits": {
                "per_minute": self.rate_limiter.config.requests_per_minute,
                "per_hour": self.rate_limiter.config.requests_per_hour,
            }
        }
    
    async def get_trigger_cached(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
    ) -> Optional[Dict[str, Any]]:
        """Get trigger with caching."""
        cache_key = f"{trigger_type.value}:{trigger_id}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Load from database
        trigger_data = await self._load_trigger(trigger_id, trigger_type)
        
        if trigger_data:
            self.cache.set(cache_key, trigger_data)
        
        return trigger_data
    
    async def _load_trigger(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
    ) -> Optional[Dict[str, Any]]:
        """Load trigger from database."""
        from backend.db.models.agent_builder import WorkflowWebhook, WorkflowSchedule
        
        if trigger_type == TriggerType.WEBHOOK:
            webhook = self.db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            
            if webhook:
                return {
                    "id": str(webhook.id),
                    "workflow_id": str(webhook.workflow_id),
                    "type": "webhook",
                    "config": {
                        "webhook_path": webhook.webhook_path,
                        "http_method": webhook.http_method,
                    },
                    "is_active": webhook.is_active,
                }
        
        elif trigger_type == TriggerType.SCHEDULE:
            schedule = self.db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            
            if schedule:
                return {
                    "id": str(schedule.id),
                    "workflow_id": str(schedule.workflow_id),
                    "type": "schedule",
                    "config": {
                        "cron_expression": schedule.cron_expression,
                        "timezone": schedule.timezone,
                    },
                    "is_active": schedule.is_active,
                }
        
        return None
    
    def invalidate_cache(self, trigger_id: str, trigger_type: TriggerType):
        """Invalidate cached trigger."""
        cache_key = f"{trigger_type.value}:{trigger_id}"
        self.cache.delete(cache_key)


# ============================================================================
# Event Trigger Support
# ============================================================================

@dataclass
class EventTriggerConfig:
    """Configuration for event-based triggers."""
    event_type: str  # file_change, db_change, custom
    event_source: str  # Source of events
    filter_pattern: Optional[str] = None  # Pattern to filter events
    debounce_seconds: float = 1.0  # Debounce rapid events


class EventTrigger:
    """
    Event-based trigger for reacting to system events.
    
    Supports:
    - File system changes
    - Database changes
    - Custom events via event bus
    """
    
    def __init__(
        self,
        workflow_id: str,
        config: EventTriggerConfig,
        manager: EnhancedTriggerManager,
    ):
        self.workflow_id = workflow_id
        self.config = config
        self.manager = manager
        self._last_trigger_time: Optional[datetime] = None
    
    async def handle_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle incoming event.
        
        Returns True if workflow was triggered.
        """
        # Check debounce
        now = datetime.utcnow()
        if self._last_trigger_time:
            elapsed = (now - self._last_trigger_time).total_seconds()
            if elapsed < self.config.debounce_seconds:
                logger.debug(f"Event debounced for workflow {self.workflow_id}")
                return False
        
        # Check filter pattern
        if self.config.filter_pattern:
            if not self._matches_filter(event_data):
                return False
        
        # Trigger workflow
        self._last_trigger_time = now
        
        await self.manager.execute_with_retry(
            workflow_id=self.workflow_id,
            trigger_type=TriggerType.EVENT,
            trigger_data={
                "event_type": self.config.event_type,
                "event_source": self.config.event_source,
                "event_data": event_data,
            },
            user_id="system",
        )
        
        return True
    
    def _matches_filter(self, event_data: Dict[str, Any]) -> bool:
        """Check if event matches filter pattern."""
        import re
        
        if not self.config.filter_pattern:
            return True
        
        # Simple pattern matching on event data string representation
        event_str = str(event_data)
        return bool(re.search(self.config.filter_pattern, event_str))
