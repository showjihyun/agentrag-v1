"""
Distributed Tracing for Agent Builder.

Provides detailed tracing and observability for agent executions.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import json
from enum import Enum

logger = logging.getLogger(__name__)


class SpanType(str, Enum):
    """Types of trace spans."""
    AGENT_EXECUTION = "agent_execution"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    WORKFLOW_EXECUTION = "workflow_execution"
    BLOCK_EXECUTION = "block_execution"
    DATABASE_QUERY = "database_query"
    CACHE_OPERATION = "cache_operation"


class SpanStatus(str, Enum):
    """Status of a span."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class Span:
    """
    Represents a single trace span.
    
    A span tracks a single operation with timing and metadata.
    """
    
    def __init__(
        self,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        name: str,
        span_type: SpanType,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize span.
        
        Args:
            trace_id: Trace ID
            span_id: Span ID
            parent_span_id: Parent span ID
            name: Span name
            span_type: Type of span
            attributes: Optional attributes
        """
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.span_type = span_type
        self.attributes = attributes or {}
        
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
        self.status = SpanStatus.OK
        self.error: Optional[str] = None
        self.events: List[Dict[str, Any]] = []
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value
    
    def set_status(self, status: SpanStatus, error: Optional[str] = None):
        """Set span status."""
        self.status = status
        if error:
            self.error = error
    
    def end(self):
        """End the span."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "span_type": self.span_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "error": self.error,
            "attributes": self.attributes,
            "events": self.events
        }


class AgentTracer:
    """
    Distributed tracing system for agents.
    
    Features:
    - Span-based tracing
    - Performance profiling
    - Dependency mapping
    - Error tracking
    """
    
    def __init__(self):
        """Initialize tracer."""
        self.traces: Dict[str, List[Span]] = {}
        self.active_spans: Dict[str, Span] = {}
        
        logger.info("AgentTracer initialized")
    
    def start_trace(self, trace_id: str, name: str) -> str:
        """
        Start a new trace.
        
        Args:
            trace_id: Trace ID
            name: Trace name
            
        Returns:
            Trace ID
        """
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        
        logger.info(f"Started trace: {trace_id} - {name}")
        return trace_id
    
    def start_span(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        span_type: SpanType,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """
        Start a new span.
        
        Args:
            trace_id: Trace ID
            span_id: Span ID
            name: Span name
            span_type: Type of span
            parent_span_id: Parent span ID
            attributes: Optional attributes
            
        Returns:
            Span object
        """
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            span_type=span_type,
            attributes=attributes
        )
        
        self.active_spans[span_id] = span
        
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        
        logger.debug(f"Started span: {span_id} - {name}")
        return span
    
    def end_span(self, span_id: str):
        """
        End a span.
        
        Args:
            span_id: Span ID
        """
        if span_id in self.active_spans:
            span = self.active_spans[span_id]
            span.end()
            
            # Add to trace
            if span.trace_id in self.traces:
                self.traces[span.trace_id].append(span)
            
            # Remove from active
            del self.active_spans[span_id]
            
            logger.debug(f"Ended span: {span_id} - {span.duration_ms:.2f}ms")
    
    @asynccontextmanager
    async def trace_span(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        span_type: SpanType,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing a span.
        
        Usage:
            async with tracer.trace_span(trace_id, span_id, "operation", SpanType.LLM_CALL):
                # Your code here
                pass
        """
        span = self.start_span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            span_type=span_type,
            parent_span_id=parent_span_id,
            attributes=attributes
        )
        
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            raise
        finally:
            self.end_span(span_id)
    
    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get all spans for a trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            List of span dictionaries
        """
        spans = self.traces.get(trace_id, [])
        return [span.to_dict() for span in spans]
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """
        Get summary of a trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace summary
        """
        spans = self.traces.get(trace_id, [])
        
        if not spans:
            return {"trace_id": trace_id, "no_data": True}
        
        total_duration = sum(s.duration_ms for s in spans if s.duration_ms)
        
        # Group by span type
        by_type = {}
        for span in spans:
            span_type = span.span_type.value
            if span_type not in by_type:
                by_type[span_type] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "errors": 0
                }
            
            by_type[span_type]["count"] += 1
            by_type[span_type]["total_duration_ms"] += span.duration_ms or 0
            if span.status == SpanStatus.ERROR:
                by_type[span_type]["errors"] += 1
        
        # Find critical path (longest chain)
        critical_path = self._find_critical_path(spans)
        
        return {
            "trace_id": trace_id,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "by_type": by_type,
            "critical_path_ms": sum(s.duration_ms for s in critical_path if s.duration_ms),
            "error_count": sum(1 for s in spans if s.status == SpanStatus.ERROR)
        }
    
    def _find_critical_path(self, spans: List[Span]) -> List[Span]:
        """Find the critical path (longest chain) in the trace."""
        # Build dependency graph
        children = {}
        for span in spans:
            if span.parent_span_id:
                if span.parent_span_id not in children:
                    children[span.parent_span_id] = []
                children[span.parent_span_id].append(span)
        
        # Find root spans (no parent)
        roots = [s for s in spans if not s.parent_span_id]
        
        if not roots:
            return []
        
        # DFS to find longest path
        def find_longest_path(span: Span) -> List[Span]:
            if span.span_id not in children:
                return [span]
            
            longest = []
            for child in children[span.span_id]:
                path = find_longest_path(child)
                if sum(s.duration_ms or 0 for s in path) > sum(s.duration_ms or 0 for s in longest):
                    longest = path
            
            return [span] + longest
        
        # Find longest path from all roots
        longest_path = []
        for root in roots:
            path = find_longest_path(root)
            if sum(s.duration_ms or 0 for s in path) > sum(s.duration_ms or 0 for s in longest_path):
                longest_path = path
        
        return longest_path
    
    def export_trace(self, trace_id: str, format: str = "json") -> str:
        """
        Export trace in specified format.
        
        Args:
            trace_id: Trace ID
            format: Export format (json, jaeger, zipkin)
            
        Returns:
            Exported trace data
        """
        spans = self.get_trace(trace_id)
        
        if format == "json":
            return json.dumps({
                "trace_id": trace_id,
                "spans": spans
            }, indent=2)
        elif format == "jaeger":
            # Convert to Jaeger format
            return self._export_jaeger(trace_id, spans)
        elif format == "zipkin":
            # Convert to Zipkin format
            return self._export_zipkin(trace_id, spans)
        else:
            raise ValueError(f"Unknown export format: {format}")
    
    def _export_jaeger(self, trace_id: str, spans: List[Dict[str, Any]]) -> str:
        """Export in Jaeger format."""
        # Simplified Jaeger format
        jaeger_spans = []
        for span in spans:
            jaeger_spans.append({
                "traceID": trace_id,
                "spanID": span["span_id"],
                "operationName": span["name"],
                "references": [
                    {
                        "refType": "CHILD_OF",
                        "traceID": trace_id,
                        "spanID": span["parent_span_id"]
                    }
                ] if span["parent_span_id"] else [],
                "startTime": int(span["start_time"] * 1000000),  # microseconds
                "duration": int(span["duration_ms"] * 1000),  # microseconds
                "tags": span["attributes"],
                "logs": [
                    {
                        "timestamp": int(event["timestamp"] * 1000000),
                        "fields": event["attributes"]
                    }
                    for event in span["events"]
                ]
            })
        
        return json.dumps({
            "data": [{
                "traceID": trace_id,
                "spans": jaeger_spans
            }]
        }, indent=2)
    
    def _export_zipkin(self, trace_id: str, spans: List[Dict[str, Any]]) -> str:
        """Export in Zipkin format."""
        # Simplified Zipkin format
        zipkin_spans = []
        for span in spans:
            zipkin_spans.append({
                "traceId": trace_id,
                "id": span["span_id"],
                "parentId": span["parent_span_id"],
                "name": span["name"],
                "timestamp": int(span["start_time"] * 1000000),
                "duration": int(span["duration_ms"] * 1000),
                "tags": span["attributes"]
            })
        
        return json.dumps(zipkin_spans, indent=2)


# Global tracer instance
_tracer = AgentTracer()


def get_tracer() -> AgentTracer:
    """Get global tracer instance."""
    return _tracer
