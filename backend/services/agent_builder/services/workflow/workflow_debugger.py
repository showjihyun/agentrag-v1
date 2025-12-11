"""
Workflow Debugger Service

Provides debugging capabilities for workflow execution including:
- Breakpoint management
- Step-by-step execution
- Execution state tracking
- Performance profiling
- Time-travel debugging
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import tracemalloc
import psutil
from collections import defaultdict


class ExecutionStatus(str, Enum):
    """Execution status enum"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class Breakpoint:
    """Breakpoint configuration"""
    node_id: str
    enabled: bool = True
    condition: Optional[str] = None
    hit_count: int = 0


@dataclass
class ExecutionState:
    """Execution state snapshot"""
    node_id: str
    timestamp: datetime
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


@dataclass
class NodeMetrics:
    """Performance metrics for a node"""
    node_id: str
    node_name: str
    executions: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    success_count: int = 0
    error_count: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    total_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    total_cpu_percent: float = 0.0
    avg_cpu_percent: float = 0.0


class WorkflowDebugger:
    """
    Workflow debugger for advanced debugging capabilities
    
    Features:
    - Breakpoint management
    - Step-by-step execution
    - Execution history tracking
    - Performance profiling
    - Time-travel debugging
    """
    
    def __init__(self):
        self.is_debugging: bool = False
        self.is_paused: bool = False
        self.current_node_id: Optional[str] = None
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.execution_history: List[ExecutionState] = []
        self.time_travel_index: Optional[int] = None
        self.pause_event: Optional[asyncio.Event] = None
        self.step_mode: bool = False
        
        # Performance tracking
        self.node_metrics: Dict[str, NodeMetrics] = {}
        self.process = psutil.Process()
        
    def start_debugging(self) -> None:
        """Start debugging session"""
        self.is_debugging = True
        self.is_paused = False
        self.execution_history = []
        self.time_travel_index = None
        self.node_metrics = {}
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused
        
    def stop_debugging(self) -> None:
        """Stop debugging session"""
        self.is_debugging = False
        self.is_paused = False
        self.current_node_id = None
        if self.pause_event:
            self.pause_event.set()  # Release any waiting coroutines
            
    def add_breakpoint(
        self,
        node_id: str,
        condition: Optional[str] = None
    ) -> Breakpoint:
        """Add a breakpoint"""
        breakpoint = Breakpoint(
            node_id=node_id,
            enabled=True,
            condition=condition
        )
        self.breakpoints[node_id] = breakpoint
        return breakpoint
        
    def remove_breakpoint(self, node_id: str) -> bool:
        """Remove a breakpoint"""
        if node_id in self.breakpoints:
            del self.breakpoints[node_id]
            return True
        return False
        
    def toggle_breakpoint(self, node_id: str) -> bool:
        """Toggle breakpoint enabled state"""
        if node_id in self.breakpoints:
            self.breakpoints[node_id].enabled = not self.breakpoints[node_id].enabled
            return self.breakpoints[node_id].enabled
        else:
            # Create new breakpoint if doesn't exist
            self.add_breakpoint(node_id)
            return True
            
    def should_pause_at_node(
        self,
        node_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if should pause at node"""
        if not self.is_debugging:
            return False
            
        # Always pause in step mode
        if self.step_mode:
            return True
            
        # Check breakpoint
        breakpoint = self.breakpoints.get(node_id)
        if not breakpoint or not breakpoint.enabled:
            return False
            
        # Increment hit count
        breakpoint.hit_count += 1
        
        # Evaluate condition if present
        if breakpoint.condition and context:
            try:
                # Simple condition evaluation (in production, use safe evaluator)
                return eval(breakpoint.condition, {"context": context})
            except Exception:
                # Pause on condition error
                return True
                
        return True
        
    async def pause_execution(self) -> None:
        """Pause execution and wait for resume"""
        if not self.pause_event:
            return
            
        self.is_paused = True
        self.pause_event.clear()
        await self.pause_event.wait()
        self.is_paused = False
        
    def continue_execution(self) -> None:
        """Continue execution from pause"""
        self.step_mode = False
        if self.pause_event:
            self.pause_event.set()
            
    def step_over(self) -> None:
        """Step over (execute current node and pause at next)"""
        self.step_mode = True
        if self.pause_event:
            self.pause_event.set()
            
    def step_into(self) -> None:
        """Step into (if node has sub-workflow, step into it)"""
        self.step_mode = True
        if self.pause_event:
            self.pause_event.set()
            
    def record_execution(self, state: ExecutionState) -> None:
        """Record execution state"""
        self.execution_history.append(state)
        self.current_node_id = state.node_id
        
        # Update metrics
        self._update_metrics(state)
        
    def _update_metrics(self, state: ExecutionState) -> None:
        """Update node performance metrics"""
        node_id = state.node_id
        
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = NodeMetrics(
                node_id=node_id,
                node_name=node_id  # Will be updated with actual name
            )
            
        metrics = self.node_metrics[node_id]
        metrics.executions += 1
        
        if state.duration_ms:
            metrics.total_duration_ms += state.duration_ms
            metrics.avg_duration_ms = metrics.total_duration_ms / metrics.executions
            
        if state.memory_mb:
            metrics.total_memory_mb += state.memory_mb
            metrics.avg_memory_mb = metrics.total_memory_mb / metrics.executions
            
        if state.cpu_percent:
            metrics.total_cpu_percent += state.cpu_percent
            metrics.avg_cpu_percent = metrics.total_cpu_percent / metrics.executions
            
        if state.status == ExecutionStatus.SUCCESS:
            metrics.success_count += 1
        elif state.status == ExecutionStatus.ERROR:
            metrics.error_count += 1
            
        metrics.success_rate = (metrics.success_count / metrics.executions) * 100
        metrics.error_rate = (metrics.error_count / metrics.executions) * 100
        
    async def execute_node_with_debug(
        self,
        node_id: str,
        node_name: str,
        execute_fn: Callable,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute node with debugging support
        
        Args:
            node_id: Node identifier
            node_name: Node display name
            execute_fn: Async function to execute
            input_data: Input data for the node
            
        Returns:
            Execution result
        """
        start_time = time.time()
        tracemalloc.start()
        
        # Record start
        self.record_execution(ExecutionState(
            node_id=node_id,
            timestamp=datetime.now(),
            status=ExecutionStatus.RUNNING,
            input_data=input_data
        ))
        
        # Check if should pause
        if self.should_pause_at_node(node_id, input_data):
            await self.pause_execution()
            
        try:
            # Execute node
            result = await execute_fn()
            
            # Measure performance
            duration_ms = (time.time() - start_time) * 1000
            current, peak = tracemalloc.get_traced_memory()
            memory_mb = current / (1024 * 1024)
            cpu_percent = self.process.cpu_percent()
            
            tracemalloc.stop()
            
            # Record success
            self.record_execution(ExecutionState(
                node_id=node_id,
                timestamp=datetime.now(),
                status=ExecutionStatus.SUCCESS,
                input_data=input_data,
                output_data=result,
                duration_ms=duration_ms,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent
            ))
            
            # Update node name in metrics
            if node_id in self.node_metrics:
                self.node_metrics[node_id].node_name = node_name
            
            return result
            
        except Exception as e:
            # Measure performance even on error
            duration_ms = (time.time() - start_time) * 1000
            try:
                current, peak = tracemalloc.get_traced_memory()
                memory_mb = current / (1024 * 1024)
            except:
                memory_mb = None
            cpu_percent = self.process.cpu_percent()
            
            tracemalloc.stop()
            
            # Record error
            self.record_execution(ExecutionState(
                node_id=node_id,
                timestamp=datetime.now(),
                status=ExecutionStatus.ERROR,
                input_data=input_data,
                error=str(e),
                duration_ms=duration_ms,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent
            ))
            
            # Update node name in metrics
            if node_id in self.node_metrics:
                self.node_metrics[node_id].node_name = node_name
            
            raise
            
    def time_travel(self, timestamp: datetime) -> Optional[ExecutionState]:
        """Time travel to specific execution state"""
        for i, state in enumerate(self.execution_history):
            if state.timestamp == timestamp:
                self.time_travel_index = i
                return state
        return None
        
    def get_current_state(self) -> Optional[ExecutionState]:
        """Get current execution state (considering time travel)"""
        if not self.execution_history:
            return None
            
        if self.time_travel_index is not None:
            return self.execution_history[self.time_travel_index]
            
        return self.execution_history[-1]
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        if not self.execution_history:
            return {
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "success_rate": 0,
                "error_rate": 0,
                "node_metrics": {}
            }
            
        total_duration = sum(
            s.duration_ms for s in self.execution_history if s.duration_ms
        )
        success_count = sum(
            1 for s in self.execution_history if s.status == ExecutionStatus.SUCCESS
        )
        error_count = sum(
            1 for s in self.execution_history if s.status == ExecutionStatus.ERROR
        )
        
        return {
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(self.execution_history),
            "success_rate": (success_count / len(self.execution_history)) * 100,
            "error_rate": (error_count / len(self.execution_history)) * 100,
            "node_metrics": {
                node_id: {
                    "node_id": metrics.node_id,
                    "node_name": metrics.node_name,
                    "executions": metrics.executions,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "avg_memory_mb": metrics.avg_memory_mb,
                    "avg_cpu_percent": metrics.avg_cpu_percent,
                }
                for node_id, metrics in self.node_metrics.items()
            }
        }
        
    def identify_bottlenecks(self, threshold_percent: float = 20.0) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks
        
        Args:
            threshold_percent: Percentage of total time to consider as bottleneck
            
        Returns:
            List of bottleneck nodes
        """
        metrics = self.get_performance_metrics()
        total_duration = metrics["total_duration_ms"]
        
        if total_duration == 0:
            return []
            
        bottlenecks = []
        for node_id, node_metrics in metrics["node_metrics"].items():
            node_total = node_metrics["avg_duration_ms"] * node_metrics["executions"]
            percentage = (node_total / total_duration) * 100
            
            if percentage >= threshold_percent:
                bottlenecks.append({
                    "node_id": node_id,
                    "node_name": node_metrics["node_name"],
                    "percentage": percentage,
                    "avg_duration_ms": node_metrics["avg_duration_ms"],
                    "executions": node_metrics["executions"],
                })
                
        return sorted(bottlenecks, key=lambda x: x["percentage"], reverse=True)
        
    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """Get optimization recommendations based on metrics"""
        recommendations = []
        metrics = self.get_performance_metrics()
        
        # Check for bottlenecks
        bottlenecks = self.identify_bottlenecks()
        if bottlenecks:
            recommendations.append({
                "type": "bottleneck",
                "severity": "high",
                "title": "Optimize Bottleneck Nodes",
                "description": f"{', '.join(b['node_name'] for b in bottlenecks)} are taking significant time. "
                              f"Consider optimizing their logic or running them in parallel."
            })
            
        # Check error rate
        if metrics["error_rate"] > 10:
            recommendations.append({
                "type": "error_rate",
                "severity": "high",
                "title": "High Error Rate Detected",
                "description": f"Error rate is {metrics['error_rate']:.1f}%. "
                              f"Review error-prone nodes and add proper error handling."
            })
            
        # Check for frequent executions (caching opportunity)
        for node_id, node_metrics in metrics["node_metrics"].items():
            if node_metrics["executions"] > 100:
                recommendations.append({
                    "type": "caching",
                    "severity": "medium",
                    "title": "Consider Caching",
                    "description": f"{node_metrics['node_name']} is executed frequently. "
                                  f"Implement caching for repeated operations to improve performance."
                })
                break  # Only suggest once
                
        return recommendations
        
    def export_debug_session(self) -> Dict[str, Any]:
        """Export complete debug session data"""
        return {
            "is_debugging": self.is_debugging,
            "is_paused": self.is_paused,
            "current_node_id": self.current_node_id,
            "breakpoints": [
                {
                    "node_id": bp.node_id,
                    "enabled": bp.enabled,
                    "condition": bp.condition,
                    "hit_count": bp.hit_count,
                }
                for bp in self.breakpoints.values()
            ],
            "execution_history": [
                {
                    "node_id": state.node_id,
                    "timestamp": state.timestamp.isoformat(),
                    "status": state.status.value,
                    "input_data": state.input_data,
                    "output_data": state.output_data,
                    "error": state.error,
                    "duration_ms": state.duration_ms,
                    "memory_mb": state.memory_mb,
                    "cpu_percent": state.cpu_percent,
                }
                for state in self.execution_history
            ],
            "performance_metrics": self.get_performance_metrics(),
            "bottlenecks": self.identify_bottlenecks(),
            "recommendations": self.get_optimization_recommendations(),
        }
