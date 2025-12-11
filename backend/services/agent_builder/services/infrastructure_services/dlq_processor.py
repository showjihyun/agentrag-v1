"""
Dead Letter Queue Processor

Automated processing of failed workflow executions:
- Automatic retry with exponential backoff
- Smart retry decisions based on error type
- Alerting integration
- Batch processing
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from backend.services.agent_builder.dead_letter_queue import (
    DeadLetterQueue,
    DeadLetterEntry,
    DLQEntryStatus,
    get_dead_letter_queue,
)

logger = logging.getLogger(__name__)


class RetryDecision(str, Enum):
    """Decision for retry handling."""
    RETRY = "retry"
    SKIP = "skip"
    DISCARD = "discard"
    MANUAL = "manual"


@dataclass
class RetryPolicy:
    """Policy for retry decisions."""
    max_retries: int = 3
    base_delay_seconds: float = 60.0
    max_delay_seconds: float = 3600.0
    exponential_base: float = 2.0
    
    # Error type specific policies
    retryable_errors: List[str] = None
    non_retryable_errors: List[str] = None
    
    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                "TimeoutError",
                "ConnectionError",
                "HTTPError",
                "RateLimitError",
                "ServiceUnavailable",
                "TemporaryError",
            ]
        if self.non_retryable_errors is None:
            self.non_retryable_errors = [
                "ValidationError",
                "AuthenticationError",
                "PermissionError",
                "ConfigurationError",
                "InvalidInputError",
            ]
    
    def get_delay(self, retry_count: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.base_delay_seconds * (self.exponential_base ** retry_count)
        return min(delay, self.max_delay_seconds)
    
    def should_retry(self, error_type: str, retry_count: int) -> RetryDecision:
        """Determine if error should be retried."""
        if retry_count >= self.max_retries:
            return RetryDecision.MANUAL
        
        if error_type in self.non_retryable_errors:
            return RetryDecision.DISCARD
        
        if error_type in self.retryable_errors:
            return RetryDecision.RETRY
        
        # Unknown error - retry with caution
        if retry_count < 2:
            return RetryDecision.RETRY
        
        return RetryDecision.MANUAL


@dataclass
class ProcessingResult:
    """Result of DLQ entry processing."""
    entry_id: str
    decision: RetryDecision
    success: bool
    message: str
    retry_scheduled_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None


class DLQProcessor:
    """
    Processes Dead Letter Queue entries.
    
    Features:
    - Automatic retry with configurable policies
    - Smart error classification
    - Batch processing
    - Alert integration
    - Processing metrics
    """
    
    def __init__(
        self,
        dlq: DeadLetterQueue,
        retry_policy: Optional[RetryPolicy] = None,
        workflow_executor_factory: Optional[Callable] = None,
        alert_callback: Optional[Callable[[DeadLetterEntry, str], Awaitable[None]]] = None,
    ):
        self.dlq = dlq
        self.retry_policy = retry_policy or RetryPolicy()
        self.executor_factory = workflow_executor_factory
        self.alert_callback = alert_callback
        
        # Processing state
        self._processing = False
        self._processed_count = 0
        self._retry_count = 0
        self._discard_count = 0
        self._manual_count = 0
        
        # Scheduled retries
        self._retry_queue: List[tuple] = []  # (scheduled_time, entry_id)
    
    async def process_entry(
        self,
        entry: DeadLetterEntry,
        force_retry: bool = False,
    ) -> ProcessingResult:
        """
        Process a single DLQ entry.
        
        Args:
            entry: DLQ entry to process
            force_retry: Force retry regardless of policy
            
        Returns:
            Processing result
        """
        # Determine retry decision
        if force_retry:
            decision = RetryDecision.RETRY
        else:
            decision = self.retry_policy.should_retry(
                entry.error_type,
                entry.retry_count,
            )
        
        self._processed_count += 1
        
        if decision == RetryDecision.RETRY:
            return await self._handle_retry(entry)
        
        elif decision == RetryDecision.DISCARD:
            return await self._handle_discard(entry)
        
        elif decision == RetryDecision.MANUAL:
            return await self._handle_manual(entry)
        
        else:  # SKIP
            return ProcessingResult(
                entry_id=entry.id,
                decision=decision,
                success=True,
                message="Entry skipped",
            )
    
    async def _handle_retry(self, entry: DeadLetterEntry) -> ProcessingResult:
        """Handle retry decision."""
        # Mark as retrying
        await self.dlq.mark_retrying(entry.id)
        
        # Calculate delay
        delay = self.retry_policy.get_delay(entry.retry_count)
        scheduled_time = datetime.utcnow() + timedelta(seconds=delay)
        
        # If executor available, attempt immediate retry
        if self.executor_factory:
            try:
                result = await self._execute_retry(entry)
                
                if result.get("success"):
                    await self.dlq.resolve(entry.id, "Retry successful")
                    self._retry_count += 1
                    
                    return ProcessingResult(
                        entry_id=entry.id,
                        decision=RetryDecision.RETRY,
                        success=True,
                        message="Retry successful",
                        execution_result=result,
                    )
                else:
                    # Retry failed, schedule next attempt
                    self._retry_queue.append((scheduled_time, entry.id))
                    
                    return ProcessingResult(
                        entry_id=entry.id,
                        decision=RetryDecision.RETRY,
                        success=False,
                        message=f"Retry failed, next attempt at {scheduled_time}",
                        retry_scheduled_at=scheduled_time,
                    )
                    
            except Exception as e:
                logger.error(f"Retry execution failed: {e}")
                self._retry_queue.append((scheduled_time, entry.id))
                
                return ProcessingResult(
                    entry_id=entry.id,
                    decision=RetryDecision.RETRY,
                    success=False,
                    message=f"Retry error: {str(e)}",
                    retry_scheduled_at=scheduled_time,
                )
        else:
            # No executor, just schedule
            self._retry_queue.append((scheduled_time, entry.id))
            
            return ProcessingResult(
                entry_id=entry.id,
                decision=RetryDecision.RETRY,
                success=True,
                message=f"Retry scheduled for {scheduled_time}",
                retry_scheduled_at=scheduled_time,
            )
    
    async def _handle_discard(self, entry: DeadLetterEntry) -> ProcessingResult:
        """Handle discard decision."""
        await self.dlq.resolve(
            entry.id,
            f"Discarded: non-retryable error type '{entry.error_type}'",
            discard=True,
        )
        
        self._discard_count += 1
        
        # Send alert
        if self.alert_callback:
            await self.alert_callback(entry, "discarded")
        
        return ProcessingResult(
            entry_id=entry.id,
            decision=RetryDecision.DISCARD,
            success=True,
            message=f"Entry discarded: {entry.error_type}",
        )
    
    async def _handle_manual(self, entry: DeadLetterEntry) -> ProcessingResult:
        """Handle manual intervention decision."""
        self._manual_count += 1
        
        # Send alert for manual review
        if self.alert_callback:
            await self.alert_callback(entry, "manual_review_required")
        
        return ProcessingResult(
            entry_id=entry.id,
            decision=RetryDecision.MANUAL,
            success=True,
            message="Requires manual review",
        )
    
    async def _execute_retry(self, entry: DeadLetterEntry) -> Dict[str, Any]:
        """Execute retry for an entry."""
        if not self.executor_factory:
            raise RuntimeError("No executor factory configured")
        
        # Create executor
        executor = await self.executor_factory(entry.workflow_id)
        
        # Execute with original input
        result = await executor.execute(entry.input_data)
        
        return result
    
    async def process_pending(
        self,
        limit: int = 10,
        workflow_id: Optional[str] = None,
    ) -> List[ProcessingResult]:
        """
        Process pending DLQ entries.
        
        Args:
            limit: Maximum entries to process
            workflow_id: Optional filter by workflow
            
        Returns:
            List of processing results
        """
        entries = await self.dlq.list_entries(
            status=DLQEntryStatus.PENDING,
            workflow_id=workflow_id,
            limit=limit,
        )
        
        results = []
        for entry in entries:
            result = await self.process_entry(entry)
            results.append(result)
        
        return results
    
    async def process_scheduled_retries(self) -> List[ProcessingResult]:
        """Process scheduled retries that are due."""
        now = datetime.utcnow()
        results = []
        
        # Find due retries
        due_retries = [
            (scheduled, entry_id)
            for scheduled, entry_id in self._retry_queue
            if scheduled <= now
        ]
        
        # Remove from queue
        self._retry_queue = [
            (scheduled, entry_id)
            for scheduled, entry_id in self._retry_queue
            if scheduled > now
        ]
        
        # Process due retries
        for _, entry_id in due_retries:
            entry = await self.dlq.get_entry(entry_id)
            if entry and entry.status == DLQEntryStatus.RETRYING:
                result = await self.process_entry(entry, force_retry=True)
                results.append(result)
        
        return results
    
    async def start_background_processor(
        self,
        interval_seconds: int = 60,
        batch_size: int = 10,
    ):
        """
        Start background processing loop.
        
        Args:
            interval_seconds: Processing interval
            batch_size: Entries to process per batch
        """
        self._processing = True
        logger.info("Starting DLQ background processor")
        
        while self._processing:
            try:
                # Process pending entries
                await self.process_pending(limit=batch_size)
                
                # Process scheduled retries
                await self.process_scheduled_retries()
                
            except Exception as e:
                logger.error(f"DLQ processor error: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop_background_processor(self):
        """Stop background processing."""
        self._processing = False
        logger.info("Stopping DLQ background processor")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self._processed_count,
            "retry_count": self._retry_count,
            "discard_count": self._discard_count,
            "manual_count": self._manual_count,
            "pending_retries": len(self._retry_queue),
            "is_processing": self._processing,
        }
    
    async def get_retry_schedule(self) -> List[Dict[str, Any]]:
        """Get scheduled retries."""
        return [
            {
                "entry_id": entry_id,
                "scheduled_at": scheduled.isoformat(),
                "delay_seconds": (scheduled - datetime.utcnow()).total_seconds(),
            }
            for scheduled, entry_id in sorted(self._retry_queue)
        ]


class DLQAlertManager:
    """
    Manages alerts for DLQ events.
    
    Features:
    - Multiple alert channels (email, Slack, webhook)
    - Alert throttling
    - Alert aggregation
    """
    
    def __init__(
        self,
        email_service=None,
        slack_service=None,
        webhook_url: Optional[str] = None,
        throttle_minutes: int = 15,
    ):
        self.email_service = email_service
        self.slack_service = slack_service
        self.webhook_url = webhook_url
        self.throttle_minutes = throttle_minutes
        
        self._last_alerts: Dict[str, datetime] = {}
    
    async def send_alert(
        self,
        entry: DeadLetterEntry,
        alert_type: str,
    ):
        """
        Send alert for DLQ entry.
        
        Args:
            entry: DLQ entry
            alert_type: Type of alert (discarded, manual_review_required, etc.)
        """
        # Check throttle
        throttle_key = f"{entry.workflow_id}:{alert_type}"
        last_alert = self._last_alerts.get(throttle_key)
        
        if last_alert:
            elapsed = (datetime.utcnow() - last_alert).total_seconds() / 60
            if elapsed < self.throttle_minutes:
                logger.debug(f"Alert throttled for {throttle_key}")
                return
        
        self._last_alerts[throttle_key] = datetime.utcnow()
        
        # Build alert message
        message = self._build_alert_message(entry, alert_type)
        
        # Send to channels
        tasks = []
        
        if self.slack_service:
            tasks.append(self._send_slack_alert(message))
        
        if self.webhook_url:
            tasks.append(self._send_webhook_alert(entry, alert_type))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _build_alert_message(
        self,
        entry: DeadLetterEntry,
        alert_type: str,
    ) -> str:
        """Build alert message."""
        return (
            f"🚨 DLQ Alert: {alert_type}\n"
            f"Workflow: {entry.workflow_id}\n"
            f"Execution: {entry.execution_id}\n"
            f"Error: {entry.error_type}\n"
            f"Message: {entry.error_message[:200]}\n"
            f"Retries: {entry.retry_count}/{entry.max_retries}\n"
            f"Created: {entry.created_at.isoformat()}"
        )
    
    async def _send_slack_alert(self, message: str):
        """Send Slack alert."""
        try:
            if self.slack_service:
                await self.slack_service.send_message(message)
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")
    
    async def _send_webhook_alert(
        self,
        entry: DeadLetterEntry,
        alert_type: str,
    ):
        """Send webhook alert."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json={
                        "alert_type": alert_type,
                        "entry": entry.to_dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    timeout=10.0,
                )
        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")


# Global processor instance
_dlq_processor: Optional[DLQProcessor] = None


def get_dlq_processor(
    dlq: Optional[DeadLetterQueue] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> DLQProcessor:
    """Get or create DLQ processor."""
    global _dlq_processor
    if _dlq_processor is None:
        _dlq_processor = DLQProcessor(
            dlq=dlq or get_dead_letter_queue(),
            retry_policy=retry_policy,
        )
    return _dlq_processor
