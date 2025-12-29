"""
Adaptive Parallel Agent Execution System.

Enables concurrent execution of independent agent actions with dynamic scaling
and intelligent resource management for optimal performance.
"""

import logging
import asyncio
import psutil
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource metrics for adaptive scaling."""
    cpu_usage: float
    memory_usage: float
    active_connections: int
    timestamp: datetime


@dataclass
class ExecutionPrediction:
    """Prediction for execution resource requirements."""
    estimated_duration: float
    estimated_memory_mb: float
    recommended_concurrency: int
    confidence_score: float


class SystemLoadMonitor:
    """Monitors system resources for adaptive scaling decisions."""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 100
    
    async def get_current_metrics(self) -> SystemMetrics:
        """Get current system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Estimate active connections (simplified)
        active_connections = len(psutil.net_connections())
        
        metrics = SystemMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            active_connections=active_connections,
            timestamp=datetime.now()
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
            
        return metrics
    
    def get_average_load(self, minutes: int = 5) -> Optional[SystemMetrics]:
        """Get average system load over the last N minutes."""
        if not self.metrics_history:
            return None
            
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
            
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_connections = sum(m.active_connections for m in recent_metrics) / len(recent_metrics)
        
        return SystemMetrics(
            cpu_usage=avg_cpu,
            memory_usage=avg_memory,
            active_connections=int(avg_connections),
            timestamp=datetime.now()
        )


class AdaptiveParallelExecutor:
    """
    Advanced executor for running multiple agents in parallel with adaptive scaling.

    Features:
    - Dynamic concurrency adjustment based on system load
    - Execution prediction and resource planning
    - Intelligent result fusion
    - Advanced error handling and recovery
    - Performance optimization suggestions
    """

    def __init__(self, 
                 base_concurrent: int = 3,
                 max_concurrent: int = 10,
                 auto_scale: bool = True,
                 enable_prediction: bool = True):
        """
        Initialize AdaptiveParallelExecutor.

        Args:
            base_concurrent: Base number of concurrent executions
            max_concurrent: Maximum allowed concurrent executions
            auto_scale: Enable automatic scaling based on system load
            enable_prediction: Enable execution prediction
        """
        self.base_concurrent = base_concurrent
        self.max_concurrent = max_concurrent
        self.auto_scale = auto_scale
        self.enable_prediction = enable_prediction
        
        # System monitoring
        self.load_monitor = SystemLoadMonitor()
        
        # Execution statistics
        self.execution_stats = {
            "total_parallel_executions": 0,
            "total_time_saved": 0.0,
            "average_speedup": 0.0,
            "adaptive_scaling_events": 0,
            "prediction_accuracy": 0.0,
            "resource_efficiency": 0.0,
        }
        
        # Execution history for prediction
        self.execution_history: List[Dict[str, Any]] = []
        self.max_history = 1000

        logger.info(
            f"AdaptiveParallelExecutor initialized "
            f"(base={base_concurrent}, max={max_concurrent}, "
            f"auto_scale={auto_scale}, prediction={enable_prediction})"
        )

    async def get_optimal_concurrency(self, 
                                 action_count: int,
                                 predicted_load: Optional[ExecutionPrediction] = None) -> int:
        """
        Calculate optimal concurrency based on system load and predictions.
        
        Args:
            action_count: Number of actions to execute
            predicted_load: Optional execution prediction
            
        Returns:
            Optimal number of concurrent executions
        """
        if not self.auto_scale:
            return min(self.base_concurrent, action_count)
        
        # Get current system metrics
        current_metrics = await self.load_monitor.get_current_metrics()
        avg_metrics = self.load_monitor.get_average_load(minutes=5)
        
        # Base calculation on system resources
        optimal_concurrency = self.base_concurrent
        
        # Adjust based on CPU usage
        if current_metrics.cpu_usage < 30:
            optimal_concurrency = min(self.max_concurrent, optimal_concurrency * 2)
        elif current_metrics.cpu_usage > 80:
            optimal_concurrency = max(1, optimal_concurrency // 2)
        elif current_metrics.cpu_usage > 60:
            optimal_concurrency = max(2, int(optimal_concurrency * 0.8))
        
        # Adjust based on memory usage
        if current_metrics.memory_usage > 90:
            optimal_concurrency = max(1, optimal_concurrency // 3)
        elif current_metrics.memory_usage > 75:
            optimal_concurrency = max(1, optimal_concurrency // 2)
        
        # Consider prediction if available
        if predicted_load and self.enable_prediction:
            if predicted_load.confidence_score > 0.7:
                predicted_concurrency = predicted_load.recommended_concurrency
                # Weighted average between system-based and prediction-based
                weight = predicted_load.confidence_score
                optimal_concurrency = int(
                    optimal_concurrency * (1 - weight) + 
                    predicted_concurrency * weight
                )
        
        # Ensure within bounds
        optimal_concurrency = max(1, min(optimal_concurrency, action_count, self.max_concurrent))
        
        # Log scaling events
        if optimal_concurrency != self.base_concurrent:
            self.execution_stats["adaptive_scaling_events"] += 1
            logger.info(
                f"Adaptive scaling: {self.base_concurrent} -> {optimal_concurrency} "
                f"(CPU: {current_metrics.cpu_usage:.1f}%, "
                f"Memory: {current_metrics.memory_usage:.1f}%)"
            )
        
        return optimal_concurrency

    async def predict_execution(self, 
                              actions: List[Dict[str, Any]], 
                              query: str) -> ExecutionPrediction:
        """
        Predict execution requirements based on historical data.
        
        Args:
            actions: List of actions to execute
            query: Original query
            
        Returns:
            Execution prediction with resource estimates
        """
        if not self.enable_prediction or not self.execution_history:
            # Default prediction
            return ExecutionPrediction(
                estimated_duration=len(actions) * 2.0,  # 2s per action
                estimated_memory_mb=len(actions) * 50.0,  # 50MB per action
                recommended_concurrency=min(3, len(actions)),
                confidence_score=0.3
            )
        
        # Find similar executions
        similar_executions = self._find_similar_executions(actions, query)
        
        if not similar_executions:
            return ExecutionPrediction(
                estimated_duration=len(actions) * 1.5,
                estimated_memory_mb=len(actions) * 40.0,
                recommended_concurrency=min(self.base_concurrent, len(actions)),
                confidence_score=0.4
            )
        
        # Calculate averages from similar executions
        avg_duration = sum(e["duration"] for e in similar_executions) / len(similar_executions)
        avg_memory = sum(e.get("memory_mb", 50) for e in similar_executions) / len(similar_executions)
        avg_concurrency = sum(e.get("concurrency", 3) for e in similar_executions) / len(similar_executions)
        
        # Adjust for current action count
        duration_factor = len(actions) / (similar_executions[0].get("action_count", 1))
        estimated_duration = avg_duration * duration_factor
        estimated_memory = avg_memory * duration_factor
        
        # Confidence based on similarity and sample size
        confidence = min(0.9, 0.5 + (len(similar_executions) * 0.1))
        
        return ExecutionPrediction(
            estimated_duration=estimated_duration,
            estimated_memory_mb=estimated_memory,
            recommended_concurrency=int(avg_concurrency),
            confidence_score=confidence
        )

    def _find_similar_executions(self, 
                               actions: List[Dict[str, Any]], 
                               query: str) -> List[Dict[str, Any]]:
        """Find similar executions from history for prediction."""
        if not self.execution_history:
            return []
        
        # Extract features for comparison
        action_types = set(action.get("type", "") for action in actions)
        query_length = len(query.split())
        
        similar = []
        for execution in self.execution_history[-100:]:  # Last 100 executions
            exec_action_types = set(execution.get("action_types", []))
            exec_query_length = execution.get("query_length", 0)
            
            # Calculate similarity score
            type_similarity = len(action_types & exec_action_types) / max(len(action_types | exec_action_types), 1)
            length_similarity = 1 - abs(query_length - exec_query_length) / max(query_length, exec_query_length, 1)
            
            overall_similarity = (type_similarity + length_similarity) / 2
            
            if overall_similarity > 0.6:  # 60% similarity threshold
                similar.append(execution)
        
        return sorted(similar, key=lambda x: x.get("similarity", 0), reverse=True)[:10]

    async def execute_parallel(
        self, actions: List[Dict[str, Any]], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """
        Execute multiple agent actions in parallel with adaptive optimization.

        Args:
            actions: List of action dictionaries with type and parameters
            agents: Dictionary of agent instances
            query: Original query

        Returns:
            Dict with merged results and enhanced metadata
        """
        if not actions:
            return {
                "results": [], 
                "parallel": False, 
                "execution_time": 0.0,
                "optimization_applied": False
            }

        # Single action - no parallelization needed
        if len(actions) == 1:
            return await self._execute_single(actions[0], agents, query)

        start_time = datetime.now()
        
        # Predict execution requirements
        prediction = await self.predict_execution(actions, query)
        
        # Get optimal concurrency
        optimal_concurrency = await self.get_optimal_concurrency(
            len(actions), prediction
        )

        logger.info(
            f"Executing {len(actions)} actions with {optimal_concurrency} concurrent workers "
            f"(predicted duration: {prediction.estimated_duration:.1f}s, "
            f"confidence: {prediction.confidence_score:.2f})"
        )

        # Create batches for execution
        action_batches = self._create_batches(actions, optimal_concurrency)
        
        # Execute batches
        all_results = []
        batch_timings = []
        
        for batch_idx, batch in enumerate(action_batches):
            batch_start = datetime.now()
            
            # Create tasks for batch
            tasks = [
                self._execute_action_safe(action, agents, query)
                for action in batch
            ]
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_duration = (datetime.now() - batch_start).total_seconds()
            batch_timings.append(batch_duration)
            
            # Process batch results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch {batch_idx}, action {i} failed: {result}")
                    # Add error result
                    all_results.append({
                        "results": [],
                        "error": str(result),
                        "action_type": batch[i].get("type", "unknown")
                    })
                else:
                    all_results.extend(result.get("results", []))

        # Calculate execution time
        total_execution_time = (datetime.now() - start_time).total_seconds()

        # Merge and deduplicate results
        merged_results = await self._intelligent_merge_results(all_results, query)

        # Update execution history for future predictions
        self._update_execution_history(actions, query, total_execution_time, optimal_concurrency)

        # Update stats
        self._update_enhanced_stats(len(actions), total_execution_time, prediction, optimal_concurrency)

        # Generate optimization insights
        optimization_insights = self._generate_optimization_insights(
            actions, total_execution_time, batch_timings, prediction
        )

        logger.info(
            f"Parallel execution completed: {len(merged_results)} results in {total_execution_time:.2f}s "
            f"(speedup: {self._calculate_speedup(len(actions), total_execution_time):.1f}x)"
        )

        return {
            "results": merged_results,
            "parallel": True,
            "execution_time": total_execution_time,
            "concurrency_used": optimal_concurrency,
            "prediction": {
                "estimated_duration": prediction.estimated_duration,
                "actual_duration": total_execution_time,
                "accuracy": self._calculate_prediction_accuracy(prediction, total_execution_time),
                "confidence": prediction.confidence_score
            },
            "optimization_insights": optimization_insights,
            "batch_timings": batch_timings,
            "system_metrics": await self.load_monitor.get_current_metrics()
        }

        logger.info(
            f"Parallel execution completed: {len(merged_results)} results "
            f"in {total_execution_time:.2f}s "
            f"(speedup: {self._calculate_speedup(len(actions), total_execution_time):.1f}x)"
        )

        return {
            "results": merged_results,
            "parallel": True,
            "execution_time": total_execution_time,
            "concurrency_used": optimal_concurrency,
            "prediction": {
                "estimated_duration": prediction.estimated_duration,
                "actual_duration": total_execution_time,
                "accuracy": self._calculate_prediction_accuracy(prediction, total_execution_time),
                "confidence": prediction.confidence_score
            },
            "optimization_insights": optimization_insights,
            "batch_timings": batch_timings,
            "system_metrics": await self.load_monitor.get_current_metrics()
        }

    async def _execute_single(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute a single action."""
        start_time = datetime.now()

        try:
            result = await self._execute_action(action, agents, query)
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "results": result.get("results", []),
                "parallel": False,
                "execution_time": execution_time,
                "actions_executed": 1,
                "successful_actions": 1,
                "errors": [],
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Single action execution failed: {e}")

            return {
                "results": [],
                "parallel": False,
                "execution_time": execution_time,
                "actions_executed": 1,
                "successful_actions": 0,
                "errors": [{"action": action.get("type", "unknown"), "error": str(e)}],
            }

    async def _execute_action_safe(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute action with error handling."""
        try:
            return await self._execute_action(action, agents, query)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"results": [], "error": str(e)}

    async def _execute_action(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute a single agent action."""
        action_type = action.get("type", "vector_search")
        action_input = action.get("input", {})

        # Get agent
        if action_type == "vector_search":
            agent = agents.get("vector_agent")
            if agent:
                results = await agent.search(
                    query=action_input.get("query", query),
                    top_k=action_input.get("top_k", 10),
                )
                return {
                    "results": [
                        r.to_dict() if hasattr(r, "to_dict") else r for r in results
                    ]
                }

        elif action_type == "web_search":
            agent = agents.get("search_agent")
            if agent:
                results = await agent.search_web(
                    query=action_input.get("query", query),
                    num_results=action_input.get("num_results", 5),
                )
                return {
                    "results": [
                        r.to_dict() if hasattr(r, "to_dict") else r for r in results
                    ]
                }

        elif action_type == "local_data":
            agent = agents.get("local_agent")
            if agent:
                if "file_path" in action_input:
                    content = await agent.read_file(action_input["file_path"])
                    return {"results": [{"type": "file", "content": content}]}
                elif "database_query" in action_input:
                    rows = await agent.query_database(
                        query=action_input["database_query"],
                        db_name=action_input.get("database", "default"),
                    )
                    return {"results": rows}

        return {"results": []}

    def _merge_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate results from multiple agents.

        Args:
            results: List of result dictionaries

        Returns:
            Merged and deduplicated results
        """
        if not results:
            return []

        # Use ID or text for deduplication
        seen = set()
        merged = []

        for result in results:
            # Generate unique key
            result_id = result.get("id") or result.get("chunk_id") or result.get("url")

            if not result_id:
                # Use text hash as fallback
                text = result.get(
                    "text", result.get("content", result.get("snippet", ""))
                )
                result_id = hash(text[:100]) if text else id(result)

            if result_id not in seen:
                seen.add(result_id)
                merged.append(result)

        # Sort by score if available
        merged.sort(
            key=lambda x: x.get("score", x.get("combined_score", 0)), reverse=True
        )

        return merged

    def _update_stats(self, num_actions: int, execution_time: float) -> None:
        """Update execution statistics."""
        self.execution_stats["total_parallel_executions"] += 1

        # Estimate time saved (assuming sequential would take sum of individual times)
        # Conservative estimate: 40% time saved
        estimated_sequential_time = execution_time * 1.67  # Inverse of 0.6
        time_saved = estimated_sequential_time - execution_time

        self.execution_stats["total_time_saved"] += time_saved

        # Update average speedup
        total_execs = self.execution_stats["total_parallel_executions"]
        self.execution_stats["average_speedup"] = (
            estimated_sequential_time / execution_time if execution_time > 0 else 1.0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {**self.execution_stats, "max_concurrent": self.max_concurrent}

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.execution_stats = {
            "total_parallel_executions": 0,
            "total_time_saved": 0.0,
            "average_speedup": 0.0,
        }
        logger.info("Parallel executor stats reset")

    def __repr__(self) -> str:
        return (
            f"ParallelAgentExecutor(max_concurrent={self.max_concurrent}, "
            f"executions={self.execution_stats['total_parallel_executions']})"
        )
    def _create_batches(self, actions: List[Dict[str, Any]], concurrency: int) -> List[List[Dict[str, Any]]]:
        """Create batches of actions for parallel execution."""
        if concurrency >= len(actions):
            return [actions]
        
        batch_size = max(1, len(actions) // concurrency)
        batches = []
        
        for i in range(0, len(actions), batch_size):
            batch = actions[i:i + batch_size]
            batches.append(batch)
        
        return batches

    async def _intelligent_merge_results(self, 
                                       results: List[Dict[str, Any]], 
                                       query: str) -> List[Dict[str, Any]]:
        """
        Intelligently merge and deduplicate results with confidence weighting.
        """
        if not results:
            return []
        
        # Extract successful results
        successful_results = []
        for result in results:
            if "error" not in result and "results" in result:
                successful_results.extend(result["results"])
        
        if not successful_results:
            return []
        
        # Basic deduplication by content similarity
        unique_results = []
        seen_content = set()
        
        for result in successful_results:
            # Create content hash for deduplication
            content = str(result.get("content", "")) + str(result.get("title", ""))
            content_hash = hash(content.lower().strip())
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                
                # Add confidence score if not present
                if "confidence" not in result:
                    result["confidence"] = self._estimate_result_confidence(result, query)
                
                unique_results.append(result)
        
        # Sort by confidence score (descending)
        unique_results.sort(key=lambda x: x.get("confidence", 0.5), reverse=True)
        
        return unique_results

    def _estimate_result_confidence(self, result: Dict[str, Any], query: str) -> float:
        """Estimate confidence score for a result based on various factors."""
        confidence = 0.5  # Base confidence
        
        # Factor 1: Content length (longer content often more reliable)
        content_length = len(str(result.get("content", "")))
        if content_length > 500:
            confidence += 0.2
        elif content_length > 200:
            confidence += 0.1
        
        # Factor 2: Source reliability (if available)
        source = result.get("source", "")
        if "official" in source.lower() or "documentation" in source.lower():
            confidence += 0.2
        
        # Factor 3: Query relevance (simple keyword matching)
        query_words = set(query.lower().split())
        content_words = set(str(result.get("content", "")).lower().split())
        relevance = len(query_words & content_words) / max(len(query_words), 1)
        confidence += relevance * 0.3
        
        return min(1.0, confidence)

    def _update_execution_history(self, 
                                actions: List[Dict[str, Any]], 
                                query: str, 
                                duration: float, 
                                concurrency: int):
        """Update execution history for future predictions."""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "action_count": len(actions),
            "action_types": [action.get("type", "") for action in actions],
            "query_length": len(query.split()),
            "duration": duration,
            "concurrency": concurrency,
            "memory_mb": 0,  # TODO: Implement memory tracking
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only recent history
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)

    def _update_enhanced_stats(self, 
                             action_count: int, 
                             execution_time: float, 
                             prediction: ExecutionPrediction, 
                             concurrency: int):
        """Update enhanced execution statistics."""
        self.execution_stats["total_parallel_executions"] += 1
        
        # Calculate speedup (estimated sequential time vs actual parallel time)
        estimated_sequential_time = action_count * 2.0  # Assume 2s per action
        speedup = estimated_sequential_time / execution_time
        
        # Update running averages
        total_executions = self.execution_stats["total_parallel_executions"]
        current_avg_speedup = self.execution_stats["average_speedup"]
        self.execution_stats["average_speedup"] = (
            (current_avg_speedup * (total_executions - 1) + speedup) / total_executions
        )
        
        # Update prediction accuracy
        if prediction.confidence_score > 0.5:
            accuracy = self._calculate_prediction_accuracy(prediction, execution_time)
            current_accuracy = self.execution_stats["prediction_accuracy"]
            self.execution_stats["prediction_accuracy"] = (
                (current_accuracy * (total_executions - 1) + accuracy) / total_executions
            )
        
        # Calculate resource efficiency
        optimal_time = prediction.estimated_duration
        efficiency = min(1.0, optimal_time / execution_time) if execution_time > 0 else 0.5
        current_efficiency = self.execution_stats["resource_efficiency"]
        self.execution_stats["resource_efficiency"] = (
            (current_efficiency * (total_executions - 1) + efficiency) / total_executions
        )

    def _calculate_prediction_accuracy(self, 
                                     prediction: ExecutionPrediction, 
                                     actual_duration: float) -> float:
        """Calculate prediction accuracy (0-1 scale)."""
        if prediction.estimated_duration <= 0:
            return 0.0
        
        error_ratio = abs(prediction.estimated_duration - actual_duration) / prediction.estimated_duration
        accuracy = max(0.0, 1.0 - error_ratio)
        return accuracy

    def _calculate_speedup(self, action_count: int, execution_time: float) -> float:
        """Calculate speedup compared to sequential execution."""
        estimated_sequential_time = action_count * 2.0  # Assume 2s per action
        return estimated_sequential_time / execution_time if execution_time > 0 else 1.0

    def _generate_optimization_insights(self, 
                                      actions: List[Dict[str, Any]], 
                                      execution_time: float, 
                                      batch_timings: List[float],
                                      prediction: ExecutionPrediction) -> Dict[str, Any]:
        """Generate optimization insights and recommendations."""
        insights = {
            "performance_score": "good",  # good, fair, poor
            "bottlenecks": [],
            "recommendations": [],
            "efficiency_metrics": {}
        }
        
        # Analyze batch timing variance
        if len(batch_timings) > 1:
            avg_batch_time = sum(batch_timings) / len(batch_timings)
            max_batch_time = max(batch_timings)
            
            if max_batch_time > avg_batch_time * 1.5:
                insights["bottlenecks"].append({
                    "type": "uneven_batch_distribution",
                    "description": "Some batches took significantly longer than others",
                    "impact": "medium"
                })
                insights["recommendations"].append({
                    "type": "load_balancing",
                    "description": "Consider redistributing actions across batches",
                    "priority": "medium"
                })
        
        # Analyze prediction accuracy
        if prediction.confidence_score > 0.5:
            accuracy = self._calculate_prediction_accuracy(prediction, execution_time)
            if accuracy < 0.7:
                insights["recommendations"].append({
                    "type": "prediction_improvement",
                    "description": "Prediction accuracy could be improved with more historical data",
                    "priority": "low"
                })
        
        # Performance scoring
        speedup = self._calculate_speedup(len(actions), execution_time)
        if speedup > 2.0:
            insights["performance_score"] = "excellent"
        elif speedup > 1.5:
            insights["performance_score"] = "good"
        elif speedup > 1.2:
            insights["performance_score"] = "fair"
        else:
            insights["performance_score"] = "poor"
            insights["recommendations"].append({
                "type": "concurrency_increase",
                "description": "Consider increasing concurrency for better performance",
                "priority": "high"
            })
        
        # Efficiency metrics
        insights["efficiency_metrics"] = {
            "speedup_factor": speedup,
            "prediction_accuracy": self._calculate_prediction_accuracy(prediction, execution_time),
            "resource_utilization": min(1.0, len(actions) / self.max_concurrent),
            "batch_balance_score": 1.0 - (max(batch_timings) - min(batch_timings)) / max(batch_timings) if batch_timings else 1.0
        }
        
        return insights

    async def _execute_single(self, action: Dict[str, Any], agents: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Execute a single action (fallback for non-parallel execution)."""
        start_time = datetime.now()
        
        try:
            result = await self._execute_action_safe(action, agents, query)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "results": result.get("results", []),
                "parallel": False,
                "execution_time": execution_time,
                "optimization_applied": False
            }
        except Exception as e:
            logger.error(f"Single action execution failed: {e}")
            return {
                "results": [],
                "parallel": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e),
                "optimization_applied": False
            }

    async def _execute_action_safe(self, action: Dict[str, Any], agents: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Safely execute a single action with error handling."""
        try:
            action_type = action.get("type", "")
            
            if action_type == "vector_search" and "vector_search" in agents:
                result = await agents["vector_search"].search(
                    query=action.get("query", query),
                    limit=action.get("limit", 5)
                )
                return {"results": result if isinstance(result, list) else [result]}
            
            elif action_type == "web_search" and "web_search" in agents:
                result = await agents["web_search"].search(
                    query=action.get("query", query),
                    limit=action.get("limit", 5)
                )
                return {"results": result if isinstance(result, list) else [result]}
            
            elif action_type == "local_data" and "local_data" in agents:
                result = await agents["local_data"].search(
                    query=action.get("query", query),
                    path=action.get("path", "")
                )
                return {"results": result if isinstance(result, list) else [result]}
            
            else:
                logger.warning(f"Unknown action type or missing agent: {action_type}")
                return {"results": [], "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"results": [], "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced execution statistics."""
        return {
            **self.execution_stats,
            "execution_history_size": len(self.execution_history),
            "system_metrics": self.load_monitor.metrics_history[-1] if self.load_monitor.metrics_history else None
        }


# Backward compatibility alias
ParallelAgentExecutor = AdaptiveParallelExecutor