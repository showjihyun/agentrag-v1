"""
Reflection Orchestrator - 2025 Trend Pattern

Implements self-reflective coordination where agents analyze their own performance,
learn from experiences, and continuously improve their collaboration patterns.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import statistics
from dataclasses import dataclass, field
from enum import Enum
import uuid

from ..base_orchestrator import BaseOrchestrator
from ....domain.entities.agent import Agent
from ....domain.entities.workflow import Workflow
from ....domain.value_objects.orchestration_config import OrchestrationConfig
from .....core.event_bus import EventBus

logger = logging.getLogger(__name__)

class ReflectionType(Enum):
    """Types of reflection analysis"""
    PERFORMANCE = "performance"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    ADAPTATION = "adaptation"
    ERROR_ANALYSIS = "error_analysis"
    STRATEGY = "strategy"

class ImprovementAction(Enum):
    """Types of improvement actions"""
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_CHANGE = "strategy_change"
    COLLABORATION_PATTERN = "collaboration_pattern"
    RESOURCE_ALLOCATION = "resource_allocation"
    COMMUNICATION_STYLE = "communication_style"
    ERROR_PREVENTION = "error_prevention"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    target: Optional[float] = None
    trend: Optional[str] = None  # "improving", "declining", "stable"
    importance: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ReflectionInsight:
    """Insight generated from reflection"""
    id: str
    reflection_type: ReflectionType
    agent_id: str
    insight: str
    confidence: float
    supporting_evidence: List[str]
    suggested_actions: List[str]
    priority: int = 1
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ImprovementPlan:
    """Plan for implementing improvements"""
    id: str
    agent_id: str
    action_type: ImprovementAction
    description: str
    parameters: Dict[str, Any]
    expected_impact: float
    implementation_cost: float
    timeline: str
    success_metrics: List[str]
    status: str = "planned"  # planned, implementing, completed, failed

@dataclass
class AgentReflectionState:
    """Reflection state for individual agent"""
    agent_id: str
    performance_history: List[PerformanceMetric] = field(default_factory=list)
    insights: List[ReflectionInsight] = field(default_factory=list)
    improvement_plans: List[ImprovementPlan] = field(default_factory=list)
    learning_rate: float = 0.1
    adaptation_threshold: float = 0.2
    last_reflection: Optional[datetime] = None
    reflection_frequency: timedelta = field(default_factory=lambda: timedelta(minutes=10))

class ReflectionOrchestrator(BaseOrchestrator):
    """
    Reflection Orchestrator
    
    Coordinates agents with continuous self-improvement:
    - Performance analysis and monitoring
    - Learning from past experiences
    - Adaptive strategy adjustment
    - Collaborative improvement
    """
    
    def __init__(self, config: OrchestrationConfig, event_bus: EventBus):
        super().__init__(config, event_bus)
        self.agent_states: Dict[str, AgentReflectionState] = {}
        self.collective_insights: List[ReflectionInsight] = []
        self.improvement_history: List[Dict[str, Any]] = []
        
        # Reflection parameters
        self.reflection_interval = config.get_parameter("reflection_interval", 60)  # seconds
        self.min_data_points = config.get_parameter("min_data_points", 5)
        self.improvement_threshold = config.get_parameter("improvement_threshold", 0.1)
        self.max_insights_per_agent = config.get_parameter("max_insights_per_agent", 10)
        
        # Learning parameters
        self.learning_decay = config.get_parameter("learning_decay", 0.95)
        self.adaptation_sensitivity = config.get_parameter("adaptation_sensitivity", 0.15)
        self.collective_learning_weight = config.get_parameter("collective_learning_weight", 0.3)
        
        self._setup_event_handlers()
        self._start_reflection_loop()
    
    def _setup_event_handlers(self):
        """Setup event handlers for reflection"""
        self.event_bus.subscribe("agent_performance_update", self._handle_performance_update)
        self.event_bus.subscribe("agent_error_occurred", self._handle_error_occurred)
        self.event_bus.subscribe("collaboration_feedback", self._handle_collaboration_feedback)
    
    def _start_reflection_loop(self):
        """Start the background reflection loop"""
        asyncio.create_task(self._reflection_processing_loop())
    
    async def orchestrate(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate agents with continuous reflection and improvement
        
        Args:
            workflow: The workflow to execute
            agents: List of available agents
            context: Execution context
            
        Returns:
            Orchestration results with reflection insights
        """
        try:
            logger.info(f"Starting reflection-based orchestration for workflow {workflow.id}")
            
            # Initialize reflection states
            await self._initialize_reflection_states(agents, context)
            
            # Execute with continuous reflection
            results = await self._execute_with_reflection(workflow, agents, context)
            
            # Perform final reflection
            final_insights = await self._perform_final_reflection()
            
            # Generate improvement recommendations
            improvements = await self._generate_improvement_recommendations()
            
            return {
                "status": "completed",
                "results": results,
                "reflection_insights": final_insights,
                "improvement_recommendations": improvements,
                "learning_metrics": await self._collect_learning_metrics(),
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Reflection orchestration failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "reflection_state": self._get_current_reflection_state()
            }
    
    async def _initialize_reflection_states(self, agents: List[Agent], context: Dict[str, Any]):
        """Initialize reflection states for all agents"""
        logger.info(f"Initializing reflection states for {len(agents)} agents")
        
        for agent in agents:
            if agent.id not in self.agent_states:
                self.agent_states[agent.id] = AgentReflectionState(
                    agent_id=agent.id,
                    learning_rate=context.get("learning_rate", 0.1),
                    adaptation_threshold=context.get("adaptation_threshold", 0.2)
                )
            
            # Load historical performance if available
            await self._load_historical_performance(agent.id, context)
        
        await self.event_bus.publish("reflection_states_initialized", {
            "agent_count": len(agents),
            "states_created": len(self.agent_states)
        })
    
    async def _execute_with_reflection(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with continuous reflection"""
        execution_phases = self._plan_execution_phases(workflow, agents, context)
        results = {}
        
        for phase_idx, phase in enumerate(execution_phases):
            logger.info(f"Executing phase {phase_idx + 1}/{len(execution_phases)}")
            
            # Execute phase
            phase_results = await self._execute_phase_with_monitoring(phase, context)
            results[f"phase_{phase_idx + 1}"] = phase_results
            
            # Perform reflection after each phase
            await self._perform_phase_reflection(phase, phase_results)
            
            # Apply immediate improvements if needed
            await self._apply_immediate_improvements(phase["agents"])
        
        return results
    
    def _plan_execution_phases(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan execution phases for reflective orchestration"""
        # Simple phase planning - can be made more sophisticated
        agent_groups = self._group_agents_by_capability(agents)
        
        phases = []
        for group_name, group_agents in agent_groups.items():
            phases.append({
                "name": f"{group_name}_phase",
                "agents": group_agents,
                "expected_duration": 60,  # seconds
                "reflection_points": ["mid_phase", "end_phase"]
            })
        
        return phases
    
    def _group_agents_by_capability(self, agents: List[Agent]) -> Dict[str, List[Agent]]:
        """Group agents by their capabilities for phased execution"""
        # Mock implementation - group by role or capability
        groups = {"primary": [], "secondary": [], "support": []}
        
        for i, agent in enumerate(agents):
            if i % 3 == 0:
                groups["primary"].append(agent)
            elif i % 3 == 1:
                groups["secondary"].append(agent)
            else:
                groups["support"].append(agent)
        
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    async def _execute_phase_with_monitoring(self, phase: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a phase with performance monitoring"""
        phase_agents = phase["agents"]
        start_time = datetime.now()
        
        # Execute agents in parallel with monitoring
        tasks = []
        for agent in phase_agents:
            task = asyncio.create_task(
                self._execute_agent_with_monitoring(agent, context)
            )
            tasks.append((agent.id, task))
        
        # Collect results
        results = {}
        for agent_id, task in tasks:
            try:
                result = await task
                results[agent_id] = result
                
                # Record performance metrics
                await self._record_performance_metrics(agent_id, result, start_time)
                
            except Exception as e:
                logger.error(f"Agent {agent_id} failed in phase: {str(e)}")
                results[agent_id] = {"status": "failed", "error": str(e)}
                
                # Record error for reflection
                await self._record_error_for_reflection(agent_id, str(e))
        
        return {
            "phase_name": phase["name"],
            "results": results,
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "success_rate": sum(1 for r in results.values() if r.get("status") == "completed") / len(results)
        }
    
    async def _execute_agent_with_monitoring(self, agent: Agent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual agent with performance monitoring"""
        start_time = datetime.now()
        
        # Get agent's reflection state for context
        agent_state = self.agent_states.get(agent.id)
        if agent_state:
            # Add reflection insights to context
            context["reflection_insights"] = [
                insight.insight for insight in agent_state.insights[-3:]  # Recent insights
            ]
            context["improvement_suggestions"] = [
                plan.description for plan in agent_state.improvement_plans 
                if plan.status == "implementing"
            ]
        
        # Mock agent execution with performance tracking
        await asyncio.sleep(1.0)  # Simulate execution
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Simulate performance metrics
        performance_score = max(0.1, min(1.0, 0.8 + (hash(agent.id) % 100 - 50) / 250))
        
        return {
            "agent_id": agent.id,
            "status": "completed",
            "output": f"Reflective result from {agent.id}",
            "execution_time": execution_time,
            "performance_score": performance_score,
            "resource_usage": {"cpu": 0.3, "memory": 0.2},
            "quality_metrics": {
                "accuracy": performance_score,
                "completeness": min(1.0, performance_score + 0.1),
                "efficiency": 1.0 / execution_time if execution_time > 0 else 1.0
            }
        }
    
    async def _record_performance_metrics(self, agent_id: str, result: Dict[str, Any], start_time: datetime):
        """Record performance metrics for reflection"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return
        
        # Extract metrics from result
        metrics = [
            PerformanceMetric("execution_time", result.get("execution_time", 0)),
            PerformanceMetric("performance_score", result.get("performance_score", 0)),
            PerformanceMetric("accuracy", result.get("quality_metrics", {}).get("accuracy", 0)),
            PerformanceMetric("efficiency", result.get("quality_metrics", {}).get("efficiency", 0))
        ]
        
        # Add to performance history
        agent_state.performance_history.extend(metrics)
        
        # Trim history to prevent memory issues
        max_history = 100
        if len(agent_state.performance_history) > max_history:
            agent_state.performance_history = agent_state.performance_history[-max_history:]
        
        await self.event_bus.publish("performance_metrics_recorded", {
            "agent_id": agent_id,
            "metrics_count": len(metrics),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _record_error_for_reflection(self, agent_id: str, error: str):
        """Record error for reflection analysis"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return
        
        error_insight = ReflectionInsight(
            id=str(uuid.uuid4()),
            reflection_type=ReflectionType.ERROR_ANALYSIS,
            agent_id=agent_id,
            insight=f"Error occurred: {error}",
            confidence=0.9,
            supporting_evidence=[error],
            suggested_actions=["Review error handling", "Adjust parameters", "Improve validation"],
            priority=1
        )
        
        agent_state.insights.append(error_insight)
        
        await self.event_bus.publish("error_recorded_for_reflection", {
            "agent_id": agent_id,
            "error": error,
            "insight_id": error_insight.id
        })
    
    async def _perform_phase_reflection(self, phase: Dict[str, Any], phase_results: Dict[str, Any]):
        """Perform reflection after each phase"""
        logger.info(f"Performing reflection for phase {phase['name']}")
        
        for agent in phase["agents"]:
            agent_result = phase_results["results"].get(agent.id, {})
            await self._perform_agent_reflection(agent.id, agent_result)
        
        # Perform collective reflection
        await self._perform_collective_reflection(phase, phase_results)
    
    async def _perform_agent_reflection(self, agent_id: str, result: Dict[str, Any]):
        """Perform reflection for individual agent"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state or len(agent_state.performance_history) < self.min_data_points:
            return
        
        # Analyze performance trends
        insights = []
        
        # Performance trend analysis
        performance_insight = await self._analyze_performance_trend(agent_id)
        if performance_insight:
            insights.append(performance_insight)
        
        # Collaboration analysis
        collaboration_insight = await self._analyze_collaboration_patterns(agent_id)
        if collaboration_insight:
            insights.append(collaboration_insight)
        
        # Learning progress analysis
        learning_insight = await self._analyze_learning_progress(agent_id)
        if learning_insight:
            insights.append(learning_insight)
        
        # Add insights to agent state
        agent_state.insights.extend(insights)
        
        # Trim insights to prevent memory issues
        if len(agent_state.insights) > self.max_insights_per_agent:
            agent_state.insights = agent_state.insights[-self.max_insights_per_agent:]
        
        agent_state.last_reflection = datetime.now()
        
        await self.event_bus.publish("agent_reflection_completed", {
            "agent_id": agent_id,
            "insights_generated": len(insights),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _analyze_performance_trend(self, agent_id: str) -> Optional[ReflectionInsight]:
        """Analyze performance trends for an agent"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return None
        
        # Get recent performance scores
        recent_scores = [
            metric.value for metric in agent_state.performance_history[-10:]
            if metric.name == "performance_score"
        ]
        
        if len(recent_scores) < 3:
            return None
        
        # Calculate trend
        trend_slope = self._calculate_trend_slope(recent_scores)
        avg_score = statistics.mean(recent_scores)
        
        if trend_slope > self.improvement_threshold:
            trend = "improving"
            insight_text = f"Performance is improving (slope: {trend_slope:.3f})"
            suggested_actions = ["Continue current strategy", "Consider increasing complexity"]
        elif trend_slope < -self.improvement_threshold:
            trend = "declining"
            insight_text = f"Performance is declining (slope: {trend_slope:.3f})"
            suggested_actions = ["Review recent changes", "Adjust parameters", "Seek additional training"]
        else:
            trend = "stable"
            insight_text = f"Performance is stable (avg: {avg_score:.3f})"
            suggested_actions = ["Maintain current approach", "Look for optimization opportunities"]
        
        return ReflectionInsight(
            id=str(uuid.uuid4()),
            reflection_type=ReflectionType.PERFORMANCE,
            agent_id=agent_id,
            insight=insight_text,
            confidence=min(0.9, abs(trend_slope) * 5),
            supporting_evidence=[f"Recent scores: {recent_scores[-5:]}"],
            suggested_actions=suggested_actions,
            priority=2 if trend == "declining" else 3
        )
    
    async def _analyze_collaboration_patterns(self, agent_id: str) -> Optional[ReflectionInsight]:
        """Analyze collaboration patterns"""
        # Mock collaboration analysis
        collaboration_score = 0.7 + (hash(agent_id) % 100 - 50) / 200
        
        if collaboration_score > 0.8:
            insight_text = "Strong collaboration patterns observed"
            suggested_actions = ["Share collaboration strategies with other agents"]
        elif collaboration_score < 0.5:
            insight_text = "Collaboration could be improved"
            suggested_actions = ["Increase communication frequency", "Seek feedback from peers"]
        else:
            return None  # No significant insight
        
        return ReflectionInsight(
            id=str(uuid.uuid4()),
            reflection_type=ReflectionType.COLLABORATION,
            agent_id=agent_id,
            insight=insight_text,
            confidence=0.7,
            supporting_evidence=[f"Collaboration score: {collaboration_score:.3f}"],
            suggested_actions=suggested_actions,
            priority=3
        )
    
    async def _analyze_learning_progress(self, agent_id: str) -> Optional[ReflectionInsight]:
        """Analyze learning progress"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return None
        
        # Calculate learning rate based on improvement over time
        recent_improvements = len([
            insight for insight in agent_state.insights[-5:]
            if insight.reflection_type == ReflectionType.PERFORMANCE and "improving" in insight.insight
        ])
        
        if recent_improvements >= 2:
            insight_text = "Good learning progress detected"
            suggested_actions = ["Continue current learning approach", "Consider advanced challenges"]
        elif recent_improvements == 0:
            insight_text = "Learning progress may be stagnating"
            suggested_actions = ["Try new approaches", "Seek diverse experiences", "Adjust learning rate"]
        else:
            return None
        
        return ReflectionInsight(
            id=str(uuid.uuid4()),
            reflection_type=ReflectionType.LEARNING,
            agent_id=agent_id,
            insight=insight_text,
            confidence=0.6,
            supporting_evidence=[f"Recent improvements: {recent_improvements}/5"],
            suggested_actions=suggested_actions,
            priority=3
        )
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    async def _perform_collective_reflection(self, phase: Dict[str, Any], phase_results: Dict[str, Any]):
        """Perform collective reflection across all agents"""
        logger.info("Performing collective reflection")
        
        # Analyze collective performance
        success_rate = phase_results.get("success_rate", 0)
        execution_time = phase_results.get("execution_time", 0)
        
        collective_insight = ReflectionInsight(
            id=str(uuid.uuid4()),
            reflection_type=ReflectionType.COLLABORATION,
            agent_id="collective",
            insight=f"Phase {phase['name']} completed with {success_rate:.1%} success rate",
            confidence=0.8,
            supporting_evidence=[
                f"Success rate: {success_rate:.1%}",
                f"Execution time: {execution_time:.2f}s"
            ],
            suggested_actions=self._generate_collective_suggestions(success_rate, execution_time),
            priority=2
        )
        
        self.collective_insights.append(collective_insight)
        
        # Share insights across agents
        await self._share_collective_insights()
    
    def _generate_collective_suggestions(self, success_rate: float, execution_time: float) -> List[str]:
        """Generate collective improvement suggestions"""
        suggestions = []
        
        if success_rate < 0.8:
            suggestions.append("Improve error handling and validation")
            suggestions.append("Enhance agent coordination")
        
        if execution_time > 120:  # 2 minutes
            suggestions.append("Optimize execution efficiency")
            suggestions.append("Consider parallel processing")
        
        if success_rate > 0.9 and execution_time < 60:
            suggestions.append("Consider taking on more complex tasks")
            suggestions.append("Share successful strategies")
        
        return suggestions or ["Continue current approach"]
    
    async def _share_collective_insights(self):
        """Share collective insights with individual agents"""
        if not self.collective_insights:
            return
        
        latest_insight = self.collective_insights[-1]
        
        for agent_id, agent_state in self.agent_states.items():
            # Add collective insight to agent's insights
            shared_insight = ReflectionInsight(
                id=str(uuid.uuid4()),
                reflection_type=ReflectionType.COLLABORATION,
                agent_id=agent_id,
                insight=f"Collective insight: {latest_insight.insight}",
                confidence=latest_insight.confidence * self.collective_learning_weight,
                supporting_evidence=latest_insight.supporting_evidence,
                suggested_actions=latest_insight.suggested_actions,
                priority=latest_insight.priority + 1
            )
            
            agent_state.insights.append(shared_insight)
    
    async def _apply_immediate_improvements(self, agents: List[Agent]):
        """Apply immediate improvements based on reflection"""
        for agent in agents:
            agent_state = self.agent_states.get(agent.id)
            if not agent_state:
                continue
            
            # Look for high-priority insights that suggest immediate action
            urgent_insights = [
                insight for insight in agent_state.insights
                if insight.priority <= 2 and 
                   (datetime.now() - insight.timestamp).total_seconds() < 300  # 5 minutes
            ]
            
            for insight in urgent_insights:
                await self._create_improvement_plan(agent.id, insight)
    
    async def _create_improvement_plan(self, agent_id: str, insight: ReflectionInsight):
        """Create improvement plan based on insight"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return
        
        # Determine improvement action type
        action_type = self._determine_action_type(insight)
        
        improvement_plan = ImprovementPlan(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            action_type=action_type,
            description=f"Address: {insight.insight}",
            parameters=self._generate_improvement_parameters(insight, action_type),
            expected_impact=insight.confidence,
            implementation_cost=0.1,  # Mock cost
            timeline="immediate",
            success_metrics=["performance_improvement", "error_reduction"]
        )
        
        agent_state.improvement_plans.append(improvement_plan)
        
        # Implement if it's a simple parameter adjustment
        if action_type == ImprovementAction.PARAMETER_ADJUSTMENT:
            await self._implement_parameter_adjustment(agent_id, improvement_plan)
    
    def _determine_action_type(self, insight: ReflectionInsight) -> ImprovementAction:
        """Determine the type of improvement action needed"""
        if "parameter" in insight.insight.lower():
            return ImprovementAction.PARAMETER_ADJUSTMENT
        elif "collaboration" in insight.insight.lower():
            return ImprovementAction.COLLABORATION_PATTERN
        elif "strategy" in insight.insight.lower():
            return ImprovementAction.STRATEGY_CHANGE
        elif "error" in insight.insight.lower():
            return ImprovementAction.ERROR_PREVENTION
        else:
            return ImprovementAction.PARAMETER_ADJUSTMENT
    
    def _generate_improvement_parameters(self, insight: ReflectionInsight, action_type: ImprovementAction) -> Dict[str, Any]:
        """Generate parameters for improvement action"""
        if action_type == ImprovementAction.PARAMETER_ADJUSTMENT:
            return {
                "learning_rate_adjustment": 0.05 if "declining" in insight.insight else -0.02,
                "adaptation_threshold_adjustment": 0.1 if "stable" in insight.insight else 0.0
            }
        elif action_type == ImprovementAction.COLLABORATION_PATTERN:
            return {
                "communication_frequency": "increase" if "improve" in insight.insight else "maintain",
                "feedback_seeking": True
            }
        else:
            return {}
    
    async def _implement_parameter_adjustment(self, agent_id: str, plan: ImprovementPlan):
        """Implement parameter adjustments"""
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return
        
        parameters = plan.parameters
        
        # Adjust learning rate
        if "learning_rate_adjustment" in parameters:
            adjustment = parameters["learning_rate_adjustment"]
            agent_state.learning_rate = max(0.01, min(0.5, agent_state.learning_rate + adjustment))
        
        # Adjust adaptation threshold
        if "adaptation_threshold_adjustment" in parameters:
            adjustment = parameters["adaptation_threshold_adjustment"]
            agent_state.adaptation_threshold = max(0.05, min(0.5, agent_state.adaptation_threshold + adjustment))
        
        plan.status = "completed"
        
        await self.event_bus.publish("improvement_implemented", {
            "agent_id": agent_id,
            "plan_id": plan.id,
            "action_type": plan.action_type.value
        })
    
    async def _reflection_processing_loop(self):
        """Background reflection processing loop"""
        while True:
            try:
                await self._periodic_reflection_check()
                await asyncio.sleep(self.reflection_interval)
            except Exception as e:
                logger.error(f"Error in reflection processing loop: {str(e)}")
                await asyncio.sleep(self.reflection_interval * 2)  # Longer delay on error
    
    async def _periodic_reflection_check(self):
        """Perform periodic reflection checks"""
        current_time = datetime.now()
        
        for agent_id, agent_state in self.agent_states.items():
            # Check if it's time for reflection
            if (agent_state.last_reflection is None or 
                (current_time - agent_state.last_reflection) >= agent_state.reflection_frequency):
                
                if len(agent_state.performance_history) >= self.min_data_points:
                    await self._perform_agent_reflection(agent_id, {})
    
    async def _perform_final_reflection(self) -> List[Dict[str, Any]]:
        """Perform final reflection at the end of orchestration"""
        logger.info("Performing final reflection")
        
        final_insights = []
        
        for agent_id, agent_state in self.agent_states.items():
            agent_insights = [
                {
                    "agent_id": insight.agent_id,
                    "type": insight.reflection_type.value,
                    "insight": insight.insight,
                    "confidence": insight.confidence,
                    "suggested_actions": insight.suggested_actions,
                    "priority": insight.priority
                }
                for insight in agent_state.insights[-5:]  # Recent insights
            ]
            final_insights.extend(agent_insights)
        
        # Add collective insights
        collective_insights = [
            {
                "agent_id": "collective",
                "type": insight.reflection_type.value,
                "insight": insight.insight,
                "confidence": insight.confidence,
                "suggested_actions": insight.suggested_actions,
                "priority": insight.priority
            }
            for insight in self.collective_insights[-3:]  # Recent collective insights
        ]
        final_insights.extend(collective_insights)
        
        return final_insights
    
    async def _generate_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on reflection"""
        recommendations = []
        
        for agent_id, agent_state in self.agent_states.items():
            # Get pending improvement plans
            pending_plans = [
                plan for plan in agent_state.improvement_plans
                if plan.status == "planned"
            ]
            
            for plan in pending_plans:
                recommendations.append({
                    "agent_id": agent_id,
                    "action_type": plan.action_type.value,
                    "description": plan.description,
                    "expected_impact": plan.expected_impact,
                    "timeline": plan.timeline,
                    "priority": "high" if plan.expected_impact > 0.7 else "medium"
                })
        
        return recommendations
    
    async def _collect_learning_metrics(self) -> Dict[str, Any]:
        """Collect learning and improvement metrics"""
        total_insights = sum(len(state.insights) for state in self.agent_states.values())
        total_improvements = sum(len(state.improvement_plans) for state in self.agent_states.values())
        
        completed_improvements = sum(
            len([plan for plan in state.improvement_plans if plan.status == "completed"])
            for state in self.agent_states.values()
        )
        
        avg_learning_rate = (sum(state.learning_rate for state in self.agent_states.values()) / 
                           len(self.agent_states) if self.agent_states else 0)
        
        return {
            "total_insights_generated": total_insights,
            "collective_insights": len(self.collective_insights),
            "total_improvement_plans": total_improvements,
            "completed_improvements": completed_improvements,
            "improvement_success_rate": completed_improvements / total_improvements if total_improvements > 0 else 0,
            "average_learning_rate": avg_learning_rate,
            "agents_with_improvements": len([
                state for state in self.agent_states.values() 
                if any(plan.status == "completed" for plan in state.improvement_plans)
            ]),
            "reflection_frequency_avg": sum(
                state.reflection_frequency.total_seconds() 
                for state in self.agent_states.values()
            ) / len(self.agent_states) if self.agent_states else 0
        }
    
    def _get_current_reflection_state(self) -> Dict[str, Any]:
        """Get current reflection system state"""
        return {
            "agents_with_states": len(self.agent_states),
            "total_insights": sum(len(state.insights) for state in self.agent_states.values()),
            "collective_insights": len(self.collective_insights),
            "active_improvement_plans": sum(
                len([plan for plan in state.improvement_plans if plan.status in ["planned", "implementing"]])
                for state in self.agent_states.values()
            )
        }
    
    async def _load_historical_performance(self, agent_id: str, context: Dict[str, Any]):
        """Load historical performance data if available"""
        # Mock implementation - in real system, load from database
        historical_data = context.get("historical_performance", {}).get(agent_id, [])
        
        agent_state = self.agent_states.get(agent_id)
        if agent_state and historical_data:
            for data_point in historical_data:
                metric = PerformanceMetric(
                    name=data_point["name"],
                    value=data_point["value"],
                    timestamp=datetime.fromisoformat(data_point["timestamp"])
                )
                agent_state.performance_history.append(metric)
    
    # Event handlers
    async def _handle_performance_update(self, event_data: Dict[str, Any]):
        """Handle performance update events"""
        agent_id = event_data.get("agent_id")
        if agent_id in self.agent_states:
            await self._record_performance_metrics(agent_id, event_data, datetime.now())
    
    async def _handle_error_occurred(self, event_data: Dict[str, Any]):
        """Handle error occurrence events"""
        agent_id = event_data.get("agent_id")
        error = event_data.get("error", "Unknown error")
        if agent_id:
            await self._record_error_for_reflection(agent_id, error)
    
    async def _handle_collaboration_feedback(self, event_data: Dict[str, Any]):
        """Handle collaboration feedback events"""
        # Process collaboration feedback for reflection
        agent_id = event_data.get("agent_id")
        feedback = event_data.get("feedback", {})
        
        if agent_id in self.agent_states:
            collaboration_insight = ReflectionInsight(
                id=str(uuid.uuid4()),
                reflection_type=ReflectionType.COLLABORATION,
                agent_id=agent_id,
                insight=f"Collaboration feedback received: {feedback.get('summary', 'General feedback')}",
                confidence=0.7,
                supporting_evidence=[str(feedback)],
                suggested_actions=feedback.get("suggestions", ["Continue current approach"]),
                priority=3
            )
            
            self.agent_states[agent_id].insights.append(collaboration_insight)