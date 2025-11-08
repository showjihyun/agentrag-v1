"""
Unit tests for Saga Pattern
"""

import pytest
from unittest.mock import AsyncMock

from backend.core.saga import SagaOrchestrator, SagaBuilder, SagaState


@pytest.mark.asyncio
async def test_saga_successful_execution():
    """Test successful saga execution."""
    saga = SagaOrchestrator("test_saga")
    
    # Mock actions
    action1 = AsyncMock(return_value={"step1": "done"})
    compensate1 = AsyncMock()
    
    action2 = AsyncMock(return_value={"step2": "done"})
    compensate2 = AsyncMock()
    
    saga.add_step("step1", action1, compensate1)
    saga.add_step("step2", action2, compensate2)
    
    # Execute
    result = await saga.execute({"initial": "data"})
    
    # Verify
    assert result["initial"] == "data"
    assert result["step1"] == "done"
    assert result["step2"] == "done"
    assert saga.execution.state == SagaState.COMPLETED
    assert action1.called
    assert action2.called
    assert not compensate1.called
    assert not compensate2.called


@pytest.mark.asyncio
async def test_saga_compensation_on_failure():
    """Test saga compensation when step fails."""
    saga = SagaOrchestrator("test_saga")
    
    # Mock actions
    action1 = AsyncMock(return_value={"step1": "done"})
    compensate1 = AsyncMock()
    
    action2 = AsyncMock(side_effect=Exception("Step 2 failed"))
    compensate2 = AsyncMock()
    
    saga.add_step("step1", action1, compensate1)
    saga.add_step("step2", action2, compensate2)
    
    # Execute and expect failure
    with pytest.raises(Exception, match="Step 2 failed"):
        await saga.execute()
    
    # Verify compensation
    assert saga.execution.state == SagaState.COMPENSATED
    assert compensate1.called  # Step 1 should be compensated
    assert not compensate2.called  # Step 2 never completed


@pytest.mark.asyncio
async def test_saga_retry_on_failure():
    """Test saga retry logic."""
    saga = SagaOrchestrator("test_saga")
    
    # Mock action that fails twice then succeeds
    call_count = 0
    
    async def flaky_action(context):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return {"step1": "done"}
    
    compensate = AsyncMock()
    
    saga.add_step("step1", flaky_action, compensate, max_retries=3)
    
    # Execute
    result = await saga.execute()
    
    # Verify
    assert call_count == 3
    assert result["step1"] == "done"
    assert saga.execution.state == SagaState.COMPLETED
    assert not compensate.called


@pytest.mark.asyncio
async def test_saga_builder():
    """Test saga builder pattern."""
    action1 = AsyncMock(return_value={"step1": "done"})
    compensate1 = AsyncMock()
    
    action2 = AsyncMock(return_value={"step2": "done"})
    compensate2 = AsyncMock()
    
    saga = (
        SagaBuilder("test_saga")
        .step("step1", action1, compensate1)
        .step("step2", action2, compensate2)
        .build()
    )
    
    result = await saga.execute()
    
    assert result["step1"] == "done"
    assert result["step2"] == "done"
    assert saga.execution.state == SagaState.COMPLETED


@pytest.mark.asyncio
async def test_saga_execution_status():
    """Test getting saga execution status."""
    saga = SagaOrchestrator("test_saga")
    
    action = AsyncMock(return_value={"step1": "done"})
    compensate = AsyncMock()
    
    saga.add_step("step1", action, compensate)
    
    # Before execution
    assert saga.get_execution_status() is None
    
    # After execution
    await saga.execute()
    
    status = saga.get_execution_status()
    assert status is not None
    assert status["state"] == SagaState.COMPLETED.value
    assert status["completed_steps"] == ["step1"]
    assert status["total_steps"] == 1
