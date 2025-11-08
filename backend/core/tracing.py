"""
OpenTelemetry Distributed Tracing

Provides distributed tracing for monitoring and debugging.
"""

import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


logger = logging.getLogger(__name__)


class TracingManager:
    """
    Tracing Manager for OpenTelemetry.
    
    Provides distributed tracing across services.
    """
    
    def __init__(
        self,
        service_name: str = "agent-builder",
        service_version: str = "1.0.0",
        environment: str = "development",
        otlp_endpoint: Optional[str] = None,
        enable_console: bool = False
    ):
        """
        Initialize Tracing Manager.
        
        Args:
            service_name: Service name
            service_version: Service version
            environment: Environment (development, staging, production)
            otlp_endpoint: OTLP collector endpoint (e.g., "localhost:4317")
            enable_console: Enable console exporter for debugging
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint
        self.enable_console = enable_console
        
        self.tracer: Optional[trace.Tracer] = None
        self.propagator = TraceContextTextMapPropagator()
        
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing."""
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add exporters
        if self.otlp_endpoint:
            # OTLP exporter (for Jaeger, Zipkin, etc.)
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True  # Use TLS in production
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP exporter configured: {self.otlp_endpoint}")
        
        if self.enable_console:
            # Console exporter (for debugging)
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Console exporter enabled")
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(
            instrumenting_module_name=self.service_name,
            instrumenting_library_version=self.service_version
        )
        
        logger.info(
            f"Tracing initialized: {self.service_name} v{self.service_version}"
        )
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ):
        """
        Start a new span.
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            
        Returns:
            Span context manager
        """
        span = self.tracer.start_span(name, kind=kind)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    @contextmanager
    def trace(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ):
        """
        Context manager for tracing.
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind
            
        Yields:
            Span
        """
        with self.tracer.start_as_current_span(name, kind=kind) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def trace_function(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator for tracing functions.
        
        Args:
            name: Span name (defaults to function name)
            attributes: Span attributes
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable):
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.trace(span_name, attributes) as span:
                    # Add function arguments as attributes
                    if args:
                        span.set_attribute("args", str(args))
                    if kwargs:
                        span.set_attribute("kwargs", str(kwargs))
                    
                    result = await func(*args, **kwargs)
                    return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.trace(span_name, attributes) as span:
                    # Add function arguments as attributes
                    if args:
                        span.set_attribute("args", str(args))
                    if kwargs:
                        span.set_attribute("kwargs", str(kwargs))
                    
                    result = func(*args, **kwargs)
                    return result
            
            # Return appropriate wrapper
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def inject_context(self, carrier: Dict[str, str]):
        """
        Inject trace context into carrier (for propagation).
        
        Args:
            carrier: Carrier dictionary (e.g., HTTP headers)
        """
        self.propagator.inject(carrier)
    
    def extract_context(self, carrier: Dict[str, str]):
        """
        Extract trace context from carrier.
        
        Args:
            carrier: Carrier dictionary (e.g., HTTP headers)
            
        Returns:
            Trace context
        """
        return self.propagator.extract(carrier)
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Add an event to the current span.
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """
        Set an attribute on the current span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """
        Record an exception in the current span.
        
        Args:
            exception: Exception to record
        """
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def get_tracing_manager() -> TracingManager:
    """Get global tracing manager instance."""
    global _tracing_manager
    if _tracing_manager is None:
        raise RuntimeError("Tracing manager not initialized")
    return _tracing_manager


def initialize_tracing(
    service_name: str = "agent-builder",
    service_version: str = "1.0.0",
    environment: str = "development",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = False
) -> TracingManager:
    """
    Initialize global tracing manager.
    
    Args:
        service_name: Service name
        service_version: Service version
        environment: Environment
        otlp_endpoint: OTLP collector endpoint
        enable_console: Enable console exporter
        
    Returns:
        Tracing manager instance
    """
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager(
            service_name=service_name,
            service_version=service_version,
            environment=environment,
            otlp_endpoint=otlp_endpoint,
            enable_console=enable_console
        )
    return _tracing_manager


def cleanup_tracing():
    """Cleanup global tracing manager."""
    global _tracing_manager
    _tracing_manager = None


# Convenience functions
def trace(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Context manager for tracing.
    
    Args:
        name: Span name
        attributes: Span attributes
        kind: Span kind
        
    Returns:
        Span context manager
    """
    manager = get_tracing_manager()
    return manager.trace(name, attributes, kind)


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator for tracing functions.
    
    Args:
        name: Span name
        attributes: Span attributes
        
    Returns:
        Function decorator
    """
    manager = get_tracing_manager()
    return manager.trace_function(name, attributes)
