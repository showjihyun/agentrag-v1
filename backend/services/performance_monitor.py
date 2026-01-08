"""Performance monitoring service for chatflow operations."""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import asyncio
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    operation: str
    duration_ms: float
    memory_type: str
    session_id: str
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """Monitor and analyze chatflow performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_stats = defaultdict(list)
        self.memory_type_stats = defaultdict(list)
        self.error_counts = defaultdict(int)
        
        # Performance thresholds (ms)
        self.thresholds = {
            'chat_response': 5000,  # 5s for chat response
            'memory_retrieval': 1000,  # 1s for memory operations
            'context_analysis': 500,  # 500ms for context analysis
            'embedding_generation': 2000,  # 2s for embeddings
            'vector_search': 1500,  # 1.5s for vector search
        }
        
        # Real-time monitoring
        self._monitoring_active = False
        self._alert_callbacks = []
    
    def record_metric(
        self,
        operation: str,
        duration_ms: float,
        memory_type: str,
        session_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation=operation,
            duration_ms=duration_ms,
            memory_type=memory_type,
            session_id=session_id,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        self.operation_stats[operation].append(duration_ms)
        self.memory_type_stats[memory_type].append(duration_ms)
        
        if not success:
            self.error_counts[operation] += 1
        
        # Check for performance alerts
        self._check_performance_alerts(metric)
    
    def get_performance_summary(
        self,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance summary for the specified time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'time_window_minutes': time_window_minutes,
                'total_operations': 0,
                'summary': 'No operations in time window'
            }
        
        # Overall statistics
        total_ops = len(recent_metrics)
        successful_ops = sum(1 for m in recent_metrics if m.success)
        success_rate = (successful_ops / total_ops) * 100 if total_ops > 0 else 0
        
        # Duration statistics
        durations = [m.duration_ms for m in recent_metrics]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        # Operation breakdown
        operation_breakdown = defaultdict(lambda: {'count': 0, 'avg_duration': 0, 'success_rate': 0})
        for metric in recent_metrics:
            op_stats = operation_breakdown[metric.operation]
            op_stats['count'] += 1
            op_stats['total_duration'] = op_stats.get('total_duration', 0) + metric.duration_ms
            op_stats['successful'] = op_stats.get('successful', 0) + (1 if metric.success else 0)
        
        # Calculate averages and success rates
        for op, stats in operation_breakdown.items():
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['success_rate'] = (stats['successful'] / stats['count']) * 100
            del stats['total_duration']  # Remove intermediate calculation
            del stats['successful']  # Remove intermediate calculation
        
        # Memory type breakdown
        memory_breakdown = defaultdict(lambda: {'count': 0, 'avg_duration': 0})
        for metric in recent_metrics:
            mem_stats = memory_breakdown[metric.memory_type]
            mem_stats['count'] += 1
            mem_stats['total_duration'] = mem_stats.get('total_duration', 0) + metric.duration_ms
        
        for mem_type, stats in memory_breakdown.items():
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            del stats['total_duration']
        
        # Performance alerts
        alerts = self._generate_performance_alerts(recent_metrics)
        
        return {
            'time_window_minutes': time_window_minutes,
            'total_operations': total_ops,
            'success_rate': round(success_rate, 2),
            'duration_stats': {
                'avg_ms': round(avg_duration, 2),
                'min_ms': round(min_duration, 2),
                'max_ms': round(max_duration, 2)
            },
            'operation_breakdown': dict(operation_breakdown),
            'memory_type_breakdown': dict(memory_breakdown),
            'alerts': alerts,
            'recommendations': self._generate_recommendations(recent_metrics)
        }
    
    def get_memory_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance across different memory types."""
        memory_comparison = {}
        
        for memory_type, durations in self.memory_type_stats.items():
            if durations:
                memory_comparison[memory_type] = {
                    'avg_duration_ms': round(sum(durations) / len(durations), 2),
                    'min_duration_ms': round(min(durations), 2),
                    'max_duration_ms': round(max(durations), 2),
                    'operation_count': len(durations),
                    'p95_duration_ms': round(self._calculate_percentile(durations, 95), 2),
                    'p99_duration_ms': round(self._calculate_percentile(durations, 99), 2)
                }
        
        # Rank by performance
        if memory_comparison:
            sorted_by_performance = sorted(
                memory_comparison.items(),
                key=lambda x: x[1]['avg_duration_ms']
            )
            
            return {
                'comparison': memory_comparison,
                'ranking': {
                    'fastest': sorted_by_performance[0][0] if sorted_by_performance else None,
                    'slowest': sorted_by_performance[-1][0] if sorted_by_performance else None,
                    'recommended': self._recommend_memory_type(memory_comparison)
                }
            }
        
        return {'comparison': {}, 'ranking': {}}
    
    def get_session_performance(self, session_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific session."""
        session_metrics = [m for m in self.metrics if m.session_id == session_id]
        
        if not session_metrics:
            return {'session_id': session_id, 'metrics': 'No metrics found'}
        
        # Session statistics
        total_ops = len(session_metrics)
        successful_ops = sum(1 for m in session_metrics if m.success)
        durations = [m.duration_ms for m in session_metrics]
        
        # Operation timeline
        timeline = [
            {
                'timestamp': m.timestamp.isoformat(),
                'operation': m.operation,
                'duration_ms': m.duration_ms,
                'success': m.success,
                'memory_type': m.memory_type
            }
            for m in sorted(session_metrics, key=lambda x: x.timestamp)
        ]
        
        return {
            'session_id': session_id,
            'total_operations': total_ops,
            'success_rate': (successful_ops / total_ops) * 100 if total_ops > 0 else 0,
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
            'total_duration_ms': sum(durations),
            'timeline': timeline,
            'memory_types_used': list(set(m.memory_type for m in session_metrics))
        }
    
    def start_monitoring(self, alert_threshold_ms: float = 5000) -> None:
        """Start real-time performance monitoring."""
        self._monitoring_active = True
        self._alert_threshold = alert_threshold_ms
        logger.info(f"Performance monitoring started with {alert_threshold_ms}ms threshold")
    
    def stop_monitoring(self) -> None:
        """Stop real-time performance monitoring."""
        self._monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    def add_alert_callback(self, callback) -> None:
        """Add callback for performance alerts."""
        self._alert_callbacks.append(callback)
    
    def export_metrics(
        self,
        format: str = 'json',
        time_window_hours: int = 24
    ) -> str:
        """Export metrics data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_metrics = [
            asdict(m) for m in self.metrics 
            if m.timestamp >= cutoff_time
        ]
        
        # Convert datetime objects to ISO strings
        for metric in recent_metrics:
            metric['timestamp'] = metric['timestamp'].isoformat()
        
        if format == 'json':
            return json.dumps({
                'export_timestamp': datetime.utcnow().isoformat(),
                'time_window_hours': time_window_hours,
                'metrics_count': len(recent_metrics),
                'metrics': recent_metrics
            }, indent=2)
        
        # Add other formats as needed (CSV, etc.)
        return json.dumps(recent_metrics, indent=2)
    
    def _check_performance_alerts(self, metric: PerformanceMetric) -> None:
        """Check if metric triggers any performance alerts."""
        if not self._monitoring_active:
            return
        
        threshold = self.thresholds.get(metric.operation, self._alert_threshold)
        
        if metric.duration_ms > threshold:
            alert = {
                'type': 'performance_threshold_exceeded',
                'operation': metric.operation,
                'duration_ms': metric.duration_ms,
                'threshold_ms': threshold,
                'session_id': metric.session_id,
                'memory_type': metric.memory_type,
                'timestamp': metric.timestamp.isoformat()
            }
            
            # Trigger alert callbacks
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
    
    def _generate_performance_alerts(self, metrics: List[PerformanceMetric]) -> List[Dict[str, Any]]:
        """Generate performance alerts based on metrics."""
        alerts = []
        
        # Check for high error rates
        error_rate = (len([m for m in metrics if not m.success]) / len(metrics)) * 100 if metrics else 0
        if error_rate > 10:  # 10% error rate threshold
            alerts.append({
                'type': 'high_error_rate',
                'error_rate': round(error_rate, 2),
                'threshold': 10,
                'severity': 'high' if error_rate > 25 else 'medium'
            })
        
        # Check for slow operations
        slow_operations = [m for m in metrics if m.duration_ms > self.thresholds.get(m.operation, 5000)]
        if len(slow_operations) > len(metrics) * 0.1:  # More than 10% slow operations
            alerts.append({
                'type': 'high_latency',
                'slow_operations_count': len(slow_operations),
                'total_operations': len(metrics),
                'percentage': round((len(slow_operations) / len(metrics)) * 100, 2),
                'severity': 'medium'
            })
        
        return alerts
    
    def _generate_recommendations(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        # Analyze memory type performance
        memory_performance = defaultdict(list)
        for metric in metrics:
            memory_performance[metric.memory_type].append(metric.duration_ms)
        
        if len(memory_performance) > 1:
            # Find fastest memory type
            avg_durations = {
                mem_type: sum(durations) / len(durations)
                for mem_type, durations in memory_performance.items()
            }
            fastest = min(avg_durations, key=avg_durations.get)
            slowest = max(avg_durations, key=avg_durations.get)
            
            if avg_durations[slowest] > avg_durations[fastest] * 1.5:
                recommendations.append(
                    f"Consider using {fastest} memory type instead of {slowest} "
                    f"for better performance ({avg_durations[fastest]:.0f}ms vs {avg_durations[slowest]:.0f}ms avg)"
                )
        
        # Check for frequent errors
        error_operations = defaultdict(int)
        for metric in metrics:
            if not metric.success:
                error_operations[metric.operation] += 1
        
        for operation, error_count in error_operations.items():
            if error_count > 5:
                recommendations.append(
                    f"High error rate detected for {operation} ({error_count} errors). "
                    "Consider investigating root cause."
                )
        
        return recommendations
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def _recommend_memory_type(self, comparison: Dict[str, Any]) -> str:
        """Recommend best memory type based on performance data."""
        if not comparison:
            return 'buffer'  # Default recommendation
        
        # Score each memory type based on multiple factors
        scores = {}
        for mem_type, stats in comparison.items():
            # Lower duration is better
            duration_score = 1000 / (stats['avg_duration_ms'] + 1)
            
            # More operations indicate reliability
            operation_score = min(stats['operation_count'] / 100, 1.0)
            
            # Combined score
            scores[mem_type] = duration_score * 0.7 + operation_score * 0.3
        
        return max(scores, key=scores.get) if scores else 'buffer'

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

# Context manager for performance tracking
class PerformanceTracker:
    """Context manager for tracking operation performance."""
    
    def __init__(
        self,
        operation: str,
        memory_type: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.memory_type = memory_type
        self.session_id = session_id
        self.metadata = metadata or {}
        self.start_time = None
        self.monitor = get_performance_monitor()
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            success = exc_type is None
            error_message = str(exc_val) if exc_val else None
            
            self.monitor.record_metric(
                operation=self.operation,
                duration_ms=duration_ms,
                memory_type=self.memory_type,
                session_id=self.session_id,
                success=success,
                error_message=error_message,
                metadata=self.metadata
            )