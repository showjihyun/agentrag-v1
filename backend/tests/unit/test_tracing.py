"""
Unit tests for OpenTelemetry Tracing

NOTE: These tests require opentelemetry package to be installed.
"""

import pytest
from unittest.mock import Mock, patch

# Skip tests if opentelemetry is not installed
pytest.importorskip("opentelemetry")

from backend.core.tracing import TracingManager, initialize_tracing


@pytest.fixture
def tracing_manager():
    """Create tracing manager instance."""
    return TracingManager(
        service_name="test-service",
        service_version="1.0.0",
        environment="test",
        enable_console=False
    )


def test_tracing_manager_initialization(tracing_manager):
    """Test tracing manager initialization."""
    assert tracing_manager.service_name == "test-service"
    assert tracing_manager.service_version == "1.0.0"
    assert tracing_manager.environment == "test"
    assert tracing_manager.tracer is not None


def test_start_span(tracing_manager):
    """Test starting a span."""
    span = tracing_manager.start_span(
        "test_operation",
        attributes={"key": "value"}
    )
    
    assert span is not None
    span.end()


def test_trace_context_manager(tracing_manager):
    """Test trace context manager."""
    with tracing_manager.trace("test_operation") as span:
        assert span is not None
        tracing_manager.set_attribute("test_key", "test_value")


def test_trace_function_decorator(tracing_manager):
    """Test trace function decorator."""
    
    @tracing_manager.trace_function("test_function")
    def test_func(x, y):
        return x + y
    
    result = test_func(1, 2)
    assert result == 3


@pytest.mark.asyncio
async def test_trace_async_function(tracing_manager):
    """Test tracing async function."""
    
    @tracing_manager.trace_function("async_test")
    async def async_func(x):
        return x * 2
    
    result = await async_func(5)
    assert result == 10


def test_add_event(tracing_manager):
    """Test adding event to span."""
    with tracing_manager.trace("test_operation"):
        tracing_manager.add_event(
            "test_event",
            attributes={"event_key": "event_value"}
        )


def test_record_exception(tracing_manager):
    """Test recording exception."""
    with pytest.raises(ValueError):
        with tracing_manager.trace("test_operation"):
            tracing_manager.record_exception(ValueError("Test error"))
            raise ValueError("Test error")


def test_initialize_tracing():
    """Test global tracing initialization."""
    manager = initialize_tracing(
        service_name="global-test",
        service_version="2.0.0"
    )
    
    assert manager is not None
    assert manager.service_name == "global-test"
