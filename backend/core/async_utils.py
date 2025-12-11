# Async utilities for concurrency control and resource management

import asyncio
from typing import List, TypeVar, Callable, Any, Optional
from contextlib import asynccontextmanager
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ConcurrencyLimiter:
    """
    Limits the number of concurrent async operations.
    
    Features:
    - Semaphore-based concurrency control
    - Backpressure handling
    - Resource protection
    """
    
    def __init__(self, max_concurrent: int = 10):
        """
        Initialize concurrency limiter.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self.total_count = 0
        self.failed_count = 0
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire semaphore for concurrent operation."""
        async with self.semaphore:
            self.active_count += 1
            self.total_count += 1
            try:
                yield
            except Exception as e:
                self.failed_count += 1
                raise
            finally:
                self.active_count -= 1
    
    async def run(self, coro):
        """Run coroutine with concurrency limit."""
        async with self.acquire():
            return await coro
    
    def get_stats(self) -> dict:
        """Get limiter statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "active_count": self.active_count,
            "total_count": self.total_count,
            "failed_count": self.failed_count,
            "success_rate": (
                (self.total_count - self.failed_count) / self.total_count * 100
                if self.total_count > 0 else 0
            )
        }


async def gather_with_concurrency(
    n: int,
    *tasks,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Run multiple async tasks with concurrency limit.
    
    Args:
        n: Maximum number of concurrent tasks
        *tasks: Coroutines to run
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results
        
    Example:
        results = await gather_with_concurrency(
            5,
            fetch_data(1),
            fetch_data(2),
            fetch_data(3),
            # ... more tasks
        )
    """
    limiter = ConcurrencyLimiter(max_concurrent=n)
    
    async def limited_task(task):
        """Wrap task with concurrency limit."""
        try:
            return await limiter.run(task)
        except Exception as e:
            if return_exceptions:
                return e
            raise
    
    try:
        results = await asyncio.gather(
            *[limited_task(task) for task in tasks],
            return_exceptions=return_exceptions
        )
        
        stats = limiter.get_stats()
        logger.info(
            "Concurrent tasks completed",
            extra={
                "total_tasks": len(tasks),
                "max_concurrent": n,
                "success_rate": stats["success_rate"]
            }
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Concurrent tasks failed: {e}", exc_info=True)
        raise


async def run_with_timeout(
    coro,
    timeout: float,
    default: Optional[Any] = None
) -> Any:
    """
    Run coroutine with timeout.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        default: Default value if timeout occurs
        
    Returns:
        Result or default value
        
    Example:
        result = await run_with_timeout(
            slow_operation(),
            timeout=5.0,
            default=None
        )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        if default is not None:
            return default
        raise


class AsyncBatchProcessor:
    """
    Process items in batches with concurrency control.
    
    Features:
    - Batch processing
    - Concurrency control
    - Error handling
    - Progress tracking
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_concurrent: int = 5
    ):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_concurrent: Maximum concurrent batches
        """
        self.batch_size = batch_size
        self.limiter = ConcurrencyLimiter(max_concurrent=max_concurrent)
        self.processed_count = 0
        self.failed_count = 0
    
    async def process_batch(
        self,
        items: List[Any],
        processor: Callable[[Any], Any]
    ) -> List[Any]:
        """
        Process a batch of items.
        
        Args:
            items: Items to process
            processor: Async function to process each item
            
        Returns:
            List of results
        """
        async with self.limiter.acquire():
            results = []
            for item in items:
                try:
                    result = await processor(item)
                    results.append(result)
                    self.processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process item: {e}", exc_info=True)
                    self.failed_count += 1
                    results.append(None)
            
            return results
    
    async def process_all(
        self,
        items: List[Any],
        processor: Callable[[Any], Any]
    ) -> List[Any]:
        """
        Process all items in batches.
        
        Args:
            items: All items to process
            processor: Async function to process each item
            
        Returns:
            List of all results
        """
        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        logger.info(
            f"Processing {len(items)} items in {len(batches)} batches",
            extra={
                "total_items": len(items),
                "batch_count": len(batches),
                "batch_size": self.batch_size
            }
        )
        
        # Process batches concurrently
        batch_results = await asyncio.gather(
            *[self.process_batch(batch, processor) for batch in batches],
            return_exceptions=True
        )
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                logger.error(f"Batch failed: {batch_result}")
                continue
            results.extend(batch_result)
        
        logger.info(
            "Batch processing completed",
            extra={
                "total_items": len(items),
                "processed": self.processed_count,
                "failed": self.failed_count,
                "success_rate": (
                    self.processed_count / len(items) * 100
                    if len(items) > 0 else 0
                )
            }
        )
        
        return results
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "batch_size": self.batch_size,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "success_rate": (
                self.processed_count / (self.processed_count + self.failed_count) * 100
                if (self.processed_count + self.failed_count) > 0 else 0
            )
        }


class AsyncCircuitBreaker:
    """
    Circuit breaker for async operations.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before trying again
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    async def call(self, coro):
        """
        Call coroutine with circuit breaker protection.
        
        Args:
            coro: Coroutine to call
            
        Returns:
            Result of coroutine
            
        Raises:
            Exception: If circuit is open or call fails
        """
        if self.state == "OPEN":
            # Check if recovery timeout passed
            if self.last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await coro
            
            # Success - reset if in HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker recovered, entering CLOSED state")
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(
                    f"Circuit breaker opened after {self.failure_count} failures",
                    exc_info=True
                )
            
            raise
    
    def get_state(self) -> dict:
        """Get circuit breaker state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold
        }
