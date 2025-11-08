"""
LLM Request Batching for Cost Optimization

Reduces LLM costs by up to 50% through dynamic request batching.
"""

import asyncio
import logging
from typing import List, Callable, Optional, Any
from collections import deque
from datetime import datetime
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Batch request data."""
    
    prompt: str
    future: asyncio.Future
    callback: Optional[Callable] = None
    metadata: Optional[dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class LLMBatcher:
    """
    Dynamic request batching for LLM calls.
    
    Features:
    - Automatic batching
    - Adaptive batch size
    - Latency optimization
    - Cost reduction (up to 50%)
    """
    
    def __init__(
        self,
        max_batch_size: int = 10,
        max_wait_ms: int = 100,
        min_batch_size: int = 2
    ):
        """
        Initialize LLM Batcher.
        
        Args:
            max_batch_size: Maximum batch size
            max_wait_ms: Maximum wait time in milliseconds
            min_batch_size: Minimum batch size to trigger processing
        """
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.min_batch_size = min_batch_size
        
        self.queue: deque = deque()
        self.processing = False
        self._process_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "batches_processed": 0,
            "total_batched": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time_ms": 0.0
        }
    
    async def add_request(
        self,
        prompt: str,
        callback: Optional[Callable] = None,
        metadata: Optional[dict] = None
    ) -> Any:
        """
        Add request to batch queue.
        
        Args:
            prompt: Input prompt
            callback: Optional callback function
            metadata: Optional metadata
            
        Returns:
            LLM response
        """
        self.stats["total_requests"] += 1
        
        # Create future for response
        future = asyncio.Future()
        
        # Create request
        request = BatchRequest(
            prompt=prompt,
            future=future,
            callback=callback,
            metadata=metadata
        )
        
        # Add to queue
        self.queue.append(request)
        
        logger.debug(f"Request added to batch queue. Queue size: {len(self.queue)}")
        
        # Start processing if not already running
        if not self.processing:
            self._process_task = asyncio.create_task(self._process_batch())
        
        # Check if we should process immediately
        elif len(self.queue) >= self.max_batch_size:
            # Cancel current wait and process immediately
            if self._process_task and not self._process_task.done():
                self._process_task.cancel()
                self._process_task = asyncio.create_task(self._process_batch())
        
        # Wait for response
        return await future
    
    async def _process_batch(self):
        """Process batch of requests."""
        self.processing = True
        
        try:
            # Wait for batch to fill or timeout
            if len(self.queue) < self.min_batch_size:
                await asyncio.sleep(self.max_wait_ms / 1000)
            
            if not self.queue:
                return
            
            # Collect batch
            batch_requests: List[BatchRequest] = []
            
            while self.queue and len(batch_requests) < self.max_batch_size:
                batch_requests.append(self.queue.popleft())
            
            if not batch_requests:
                return
            
            # Calculate wait time
            wait_times = [
                (datetime.utcnow() - req.timestamp).total_seconds() * 1000
                for req in batch_requests
            ]
            avg_wait_time = sum(wait_times) / len(wait_times)
            
            # Update statistics
            self.stats["batches_processed"] += 1
            self.stats["total_batched"] += len(batch_requests)
            self.stats["avg_batch_size"] = (
                self.stats["total_batched"] / self.stats["batches_processed"]
            )
            self.stats["avg_wait_time_ms"] = (
                (self.stats["avg_wait_time_ms"] * (self.stats["batches_processed"] - 1) + avg_wait_time)
                / self.stats["batches_processed"]
            )
            
            logger.info(
                f"Processing batch of {len(batch_requests)} requests. "
                f"Avg wait: {avg_wait_time:.2f}ms"
            )
            
            # Extract prompts
            prompts = [req.prompt for req in batch_requests]
            
            # Process batch
            try:
                responses = await self._call_llm_batch(prompts)
                
                # Distribute responses
                for request, response in zip(batch_requests, responses):
                    # Set result
                    if not request.future.done():
                        request.future.set_result(response)
                    
                    # Call callback if provided
                    if request.callback:
                        try:
                            if asyncio.iscoroutinefunction(request.callback):
                                await request.callback(response)
                            else:
                                request.callback(response)
                        except Exception as e:
                            logger.error(f"Callback error: {e}", exc_info=True)
                
                logger.info(f"Batch processed successfully: {len(responses)} responses")
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}", exc_info=True)
                
                # Set exception for all requests
                for request in batch_requests:
                    if not request.future.done():
                        request.future.set_exception(e)
        
        except asyncio.CancelledError:
            logger.debug("Batch processing cancelled")
            # Re-add requests to queue
            for request in batch_requests:
                self.queue.appendleft(request)
        
        finally:
            self.processing = False
            
            # Continue processing if more requests
            if self.queue:
                self._process_task = asyncio.create_task(self._process_batch())
    
    async def _call_llm_batch(self, prompts: List[str]) -> List[str]:
        """
        Call LLM with batch of prompts.
        
        This is a placeholder - implement actual LLM batch API call.
        
        Args:
            prompts: List of prompts
            
        Returns:
            List of responses
        """
        # TODO: Implement actual batch LLM call
        # For now, simulate batch processing
        
        logger.debug(f"Calling LLM batch API with {len(prompts)} prompts")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        # Return mock responses
        return [f"Response for: {prompt[:50]}..." for prompt in prompts]
    
    def get_stats(self) -> dict:
        """Get batching statistics."""
        total_requests = self.stats["total_requests"]
        total_batched = self.stats["total_batched"]
        
        batching_rate = (total_batched / total_requests * 100) if total_requests > 0 else 0
        
        # Estimate cost savings
        # Assuming batch API is 50% cheaper per request
        estimated_savings = batching_rate * 0.5
        
        return {
            "total_requests": total_requests,
            "batches_processed": self.stats["batches_processed"],
            "total_batched": total_batched,
            "avg_batch_size": f"{self.stats['avg_batch_size']:.2f}",
            "avg_wait_time_ms": f"{self.stats['avg_wait_time_ms']:.2f}",
            "batching_rate": f"{batching_rate:.2f}%",
            "estimated_cost_savings": f"{estimated_savings:.2f}%"
        }
    
    async def flush(self):
        """Flush remaining requests in queue."""
        if self.queue:
            logger.info(f"Flushing {len(self.queue)} remaining requests")
            
            if self._process_task and not self._process_task.done():
                self._process_task.cancel()
            
            await self._process_batch()


class AdaptiveLLMBatcher(LLMBatcher):
    """
    Adaptive LLM Batcher with dynamic batch size adjustment.
    
    Automatically adjusts batch size based on:
    - Request rate
    - Latency requirements
    - System load
    """
    
    def __init__(
        self,
        initial_batch_size: int = 10,
        max_wait_ms: int = 100,
        target_latency_ms: int = 200
    ):
        """
        Initialize Adaptive LLM Batcher.
        
        Args:
            initial_batch_size: Initial batch size
            max_wait_ms: Maximum wait time
            target_latency_ms: Target latency
        """
        super().__init__(
            max_batch_size=initial_batch_size,
            max_wait_ms=max_wait_ms
        )
        
        self.target_latency_ms = target_latency_ms
        self.current_batch_size = initial_batch_size
        
        # Adaptation parameters
        self.min_batch_size = 2
        self.max_batch_size_limit = 50
        self.adjustment_interval = 10  # Adjust every N batches
    
    async def _process_batch(self):
        """Process batch with adaptive sizing."""
        await super()._process_batch()
        
        # Adjust batch size periodically
        if self.stats["batches_processed"] % self.adjustment_interval == 0:
            await self._adjust_batch_size()
    
    async def _adjust_batch_size(self):
        """Adjust batch size based on performance."""
        avg_wait = self.stats["avg_wait_time_ms"]
        
        if avg_wait > self.target_latency_ms:
            # Reduce batch size to improve latency
            new_size = max(
                self.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
            
            if new_size != self.current_batch_size:
                logger.info(
                    f"Reducing batch size: {self.current_batch_size} → {new_size} "
                    f"(avg wait: {avg_wait:.2f}ms)"
                )
                self.current_batch_size = new_size
                self.max_batch_size = new_size
        
        elif avg_wait < self.target_latency_ms * 0.5:
            # Increase batch size for better cost savings
            new_size = min(
                self.max_batch_size_limit,
                int(self.current_batch_size * 1.2)
            )
            
            if new_size != self.current_batch_size:
                logger.info(
                    f"Increasing batch size: {self.current_batch_size} → {new_size} "
                    f"(avg wait: {avg_wait:.2f}ms)"
                )
                self.current_batch_size = new_size
                self.max_batch_size = new_size


# Global batcher instance
_llm_batcher: Optional[LLMBatcher] = None


def get_llm_batcher() -> LLMBatcher:
    """Get global LLM batcher instance."""
    global _llm_batcher
    if _llm_batcher is None:
        raise RuntimeError("LLM batcher not initialized")
    return _llm_batcher


def initialize_llm_batcher(
    max_batch_size: int = 10,
    max_wait_ms: int = 100,
    adaptive: bool = True
) -> LLMBatcher:
    """
    Initialize global LLM batcher.
    
    Args:
        max_batch_size: Maximum batch size
        max_wait_ms: Maximum wait time
        adaptive: Use adaptive batching
        
    Returns:
        LLM batcher instance
    """
    global _llm_batcher
    if _llm_batcher is None:
        if adaptive:
            _llm_batcher = AdaptiveLLMBatcher(
                initial_batch_size=max_batch_size,
                max_wait_ms=max_wait_ms
            )
        else:
            _llm_batcher = LLMBatcher(
                max_batch_size=max_batch_size,
                max_wait_ms=max_wait_ms
            )
    return _llm_batcher


def cleanup_llm_batcher():
    """Cleanup global LLM batcher."""
    global _llm_batcher
    _llm_batcher = None
