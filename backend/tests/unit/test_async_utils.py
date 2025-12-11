# Tests for Async Utilities

import pytest
import asyncio
from backend.core.async_utils import (
    ConcurrencyLimiter,
    gather_with_concurrency,
    run_with_timeout,
    AsyncBatchProcessor,
    AsyncCircuitBreaker
)


class TestConcurrencyLimiter:
    """Test ConcurrencyLimiter class."""
    
    @pytest.mark.asyncio
    async def test_limiter_basic(self):
        """Test basic limiter functionality."""
        limiter = ConcurrencyLimiter(max_concurrent=2)
        
        async def task():
            async with limiter.acquire():
                await asyncio.sleep(0.1)
                return "done"
        
        results = await asyncio.gather(*[task() for _ in range(5)])
        
        assert len(results) == 5
        assert all(r == "done" for r in results)
    
    @pytest.mark.asyncio
    async def test_limiter_stats(self):
        """Test limiter statistics."""
        limiter = ConcurrencyLimiter(max_concurrent=2)
        
        async def task():
            async with limiter.acquire():
                await asyncio.sleep(0.01)
        
        await asyncio.gather(*[task() for _ in range(5)])
        
        stats = limiter.get_stats()
        assert stats["total_count"] == 5
        assert stats["active_count"] == 0
        assert stats["success_rate"] == 100.0
    
    @pytest.mark.asyncio
    async def test_limiter_with_errors(self):
        """Test limiter with errors."""
        limiter = ConcurrencyLimiter(max_concurrent=2)
        
        async def task(should_fail: bool):
            async with limiter.acquire():
                if should_fail:
                    raise ValueError("Task failed")
                return "done"
        
        results = await asyncio.gather(
            *[task(i % 2 == 0) for i in range(4)],
            return_exceptions=True
        )
        
        assert len(results) == 4
        assert sum(1 for r in results if isinstance(r, ValueError)) == 2
        
        stats = limiter.get_stats()
        assert stats["failed_count"] == 2


class TestGatherWithConcurrency:
    """Test gather_with_concurrency function."""
    
    @pytest.mark.asyncio
    async def test_gather_basic(self):
        """Test basic gather with concurrency."""
        async def task(n: int):
            await asyncio.sleep(0.01)
            return n * 2
        
        results = await gather_with_concurrency(
            3,
            *[task(i) for i in range(10)]
        )
        
        assert len(results) == 10
        assert results == [i * 2 for i in range(10)]
    
    @pytest.mark.asyncio
    async def test_gather_with_exceptions(self):
        """Test gather with exceptions."""
        async def task(n: int):
            if n == 5:
                raise ValueError("Error at 5")
            return n
        
        results = await gather_with_concurrency(
            3,
            *[task(i) for i in range(10)],
            return_exceptions=True
        )
        
        assert len(results) == 10
        assert isinstance(results[5], ValueError)


class TestRunWithTimeout:
    """Test run_with_timeout function."""
    
    @pytest.mark.asyncio
    async def test_timeout_success(self):
        """Test successful operation within timeout."""
        async def fast_task():
            await asyncio.sleep(0.01)
            return "done"
        
        result = await run_with_timeout(fast_task(), timeout=1.0)
        assert result == "done"
    
    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Test operation exceeding timeout."""
        async def slow_task():
            await asyncio.sleep(2.0)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await run_with_timeout(slow_task(), timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_timeout_with_default(self):
        """Test timeout with default value."""
        async def slow_task():
            await asyncio.sleep(2.0)
            return "done"
        
        result = await run_with_timeout(
            slow_task(),
            timeout=0.1,
            default="timeout"
        )
        assert result == "timeout"


class TestAsyncBatchProcessor:
    """Test AsyncBatchProcessor class."""
    
    @pytest.mark.asyncio
    async def test_process_batch(self):
        """Test processing a single batch."""
        processor = AsyncBatchProcessor(batch_size=5, max_concurrent=2)
        
        async def process_item(item: int):
            await asyncio.sleep(0.01)
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)
        
        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_process_all(self):
        """Test processing all items in batches."""
        processor = AsyncBatchProcessor(batch_size=3, max_concurrent=2)
        
        async def process_item(item: int):
            await asyncio.sleep(0.01)
            return item * 2
        
        items = list(range(10))
        results = await processor.process_all(items, process_item)
        
        assert len(results) == 10
        assert results == [i * 2 for i in range(10)]
    
    @pytest.mark.asyncio
    async def test_process_with_errors(self):
        """Test processing with some errors."""
        processor = AsyncBatchProcessor(batch_size=5, max_concurrent=2)
        
        async def process_item(item: int):
            if item == 5:
                raise ValueError("Error at 5")
            return item * 2
        
        items = list(range(10))
        results = await processor.process_all(items, process_item)
        
        # Should have None for failed item
        assert results[5] is None
        assert processor.failed_count == 1
    
    @pytest.mark.asyncio
    async def test_processor_stats(self):
        """Test processor statistics."""
        processor = AsyncBatchProcessor(batch_size=5, max_concurrent=2)
        
        async def process_item(item: int):
            return item * 2
        
        items = list(range(10))
        await processor.process_all(items, process_item)
        
        stats = processor.get_stats()
        assert stats["processed_count"] == 10
        assert stats["failed_count"] == 0
        assert stats["success_rate"] == 100.0


class TestAsyncCircuitBreaker:
    """Test AsyncCircuitBreaker class."""
    
    @pytest.mark.asyncio
    async def test_circuit_closed(self):
        """Test circuit breaker in closed state."""
        breaker = AsyncCircuitBreaker(failure_threshold=3)
        
        async def successful_task():
            return "success"
        
        result = await breaker.call(successful_task())
        assert result == "success"
        assert breaker.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test circuit breaker opens after threshold."""
        breaker = AsyncCircuitBreaker(failure_threshold=3)
        
        async def failing_task():
            raise ValueError("Task failed")
        
        # Fail 3 times to open circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_task())
        
        assert breaker.state == "OPEN"
        assert breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        breaker = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=10.0)
        
        async def failing_task():
            raise ValueError("Task failed")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_task())
        
        assert breaker.state == "OPEN"
        
        # Should reject new calls
        async def any_task():
            return "success"
        
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(any_task())
    
    @pytest.mark.asyncio
    async def test_circuit_recovery(self):
        """Test circuit breaker recovery."""
        breaker = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_task():
            raise ValueError("Task failed")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_task())
        
        assert breaker.state == "OPEN"
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should enter HALF_OPEN and allow one call
        async def successful_task():
            return "success"
        
        result = await breaker.call(successful_task())
        assert result == "success"
        assert breaker.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_state(self):
        """Test getting circuit breaker state."""
        breaker = AsyncCircuitBreaker(failure_threshold=3)
        
        state = breaker.get_state()
        assert state["state"] == "CLOSED"
        assert state["failure_count"] == 0
        assert state["failure_threshold"] == 3
