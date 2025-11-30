"""
Agent Execution Monitoring

Provides real-time monitoring and analytics for agent executions:
- Execution tracking
- Token usage and cost tracking
- Performance metrics
- Error tracking
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import json

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TokenUsage:
    """Token usage tracking."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, prompt: int, completion: int):
        """Add token usage."""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion


@dataclass
class CostEstimate:
    """Cost estimation for execution."""
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    
    def calculate(self, token_usage: TokenUsage, model: str):
        """Calculate cost based on token usage and model."""
        # Pricing per 1K tokens (approximate)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
        
        model_pricing = pricing.get(model, {"input": 0.001, "output": 0.002})
        
        self.input_cost = (token_usage.prompt_tokens / 1000) * model_pricing["input"]
        self.output_cost = (token_usage.completion_tokens / 1000) * model_pricing["output"]
        self.total_cost = self.input_cost + self.output_cost


@dataclass
class ExecutionStep:
    """Single step in agent execution."""
    step_id: str
    step_type: str  # "llm_call", "tool_call", "retrieval"
    name: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecution:
    """Agent execution record."""
    execution_id: str
    agent_id: str
    agent_name: str
    user_id: str
    status: ExecutionStatus
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    
    # Input/Output
    input_text: str = ""
    output_text: Optional[str] = None
    
    # Token tracking
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    cost_estimate: CostEstimate = field(default_factory=CostEstimate)
    
    # Execution steps
    steps: List[ExecutionStep] = field(default_factory=list)
    
    # Model info
    llm_provider: str = ""
    llm_model: str = ""
    
    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "user_id": self.user_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "input_text": self.input_text[:500] if self.input_text else None,
            "output_text": self.output_text[:500] if self.output_text else None,
            "token_usage": asdict(self.token_usage),
            "cost_estimate": asdict(self.cost_estimate),
            "steps": [asdict(s) for s in self.steps],
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "error": self.error,
            "error_type": self.error_type,
            "metadata": self.metadata,
        }


class AgentMonitoringService:
    """
    Service for monitoring agent executions.
    
    Features:
    - Real-time execution tracking
    - Token usage and cost tracking
    - Performance metrics
    - Historical analytics
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.executions: Dict[str, AgentExecution] = {}
        
        # Redis keys
        self.execution_key = "agent:execution:{execution_id}"
        self.agent_stats_key = "agent:stats:{agent_id}"
        self.user_stats_key = "agent:user_stats:{user_id}"
        self.daily_stats_key = "agent:daily:{date}"
    
    async def start_execution(
        self,
        execution_id: str,
        agent_id: str,
        agent_name: str,
        user_id: str,
        input_text: str,
        llm_provider: str,
        llm_model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentExecution:
        """Start tracking an agent execution."""
        execution = AgentExecution(
            execution_id=execution_id,
            agent_id=agent_id,
            agent_name=agent_name,
            user_id=user_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow().isoformat(),
            input_text=input_text,
            llm_provider=llm_provider,
            llm_model=llm_model,
            metadata=metadata or {},
        )
        
        self.executions[execution_id] = execution
        
        # Store in Redis
        await self._save_execution(execution)
        
        # Update stats
        await self._increment_stat(self.agent_stats_key.format(agent_id=agent_id), "total_executions")
        await self._increment_stat(self.user_stats_key.format(user_id=user_id), "total_executions")
        await self._increment_stat(self.daily_stats_key.format(date=datetime.utcnow().strftime("%Y-%m-%d")), "total_executions")
        
        logger.info(f"Started execution {execution_id} for agent {agent_id}")
        return execution
    
    async def add_step(
        self,
        execution_id: str,
        step_id: str,
        step_type: str,
        name: str,
        input_preview: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStep:
        """Add a step to the execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        step = ExecutionStep(
            step_id=step_id,
            step_type=step_type,
            name=name,
            started_at=datetime.utcnow().isoformat(),
            input_preview=input_preview[:200] if input_preview else None,
            metadata=metadata or {},
        )
        
        execution.steps.append(step)
        await self._save_execution(execution)
        
        return step
    
    async def complete_step(
        self,
        execution_id: str,
        step_id: str,
        output_preview: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
    ):
        """Complete a step in the execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        for step in execution.steps:
            if step.step_id == step_id:
                step.completed_at = datetime.utcnow().isoformat()
                step.status = "failed" if error else "completed"
                step.output_preview = output_preview[:200] if output_preview else None
                step.token_usage = token_usage
                step.error = error
                
                # Calculate duration
                started = datetime.fromisoformat(step.started_at)
                completed = datetime.fromisoformat(step.completed_at)
                step.duration_ms = (completed - started).total_seconds() * 1000
                
                # Update token usage
                if token_usage:
                    execution.token_usage.add(
                        token_usage.get("prompt_tokens", 0),
                        token_usage.get("completion_tokens", 0)
                    )
                
                break
        
        await self._save_execution(execution)
    
    async def complete_execution(
        self,
        execution_id: str,
        output_text: Optional[str] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """Complete an agent execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        execution.completed_at = datetime.utcnow().isoformat()
        execution.output_text = output_text
        execution.error = error
        execution.error_type = error_type
        
        if error:
            execution.status = ExecutionStatus.FAILED
        else:
            execution.status = ExecutionStatus.COMPLETED
        
        # Calculate duration
        started = datetime.fromisoformat(execution.started_at)
        completed = datetime.fromisoformat(execution.completed_at)
        execution.duration_ms = (completed - started).total_seconds() * 1000
        
        # Calculate cost
        execution.cost_estimate.calculate(execution.token_usage, execution.llm_model)
        
        await self._save_execution(execution)
        
        # Update stats
        agent_stats_key = self.agent_stats_key.format(agent_id=execution.agent_id)
        user_stats_key = self.user_stats_key.format(user_id=execution.user_id)
        daily_key = self.daily_stats_key.format(date=datetime.utcnow().strftime("%Y-%m-%d"))
        
        if error:
            await self._increment_stat(agent_stats_key, "failed_executions")
            await self._increment_stat(user_stats_key, "failed_executions")
            await self._increment_stat(daily_key, "failed_executions")
        else:
            await self._increment_stat(agent_stats_key, "successful_executions")
            await self._increment_stat(user_stats_key, "successful_executions")
            await self._increment_stat(daily_key, "successful_executions")
        
        # Update token and cost stats
        await self._increment_stat(agent_stats_key, "total_tokens", execution.token_usage.total_tokens)
        await self._increment_stat(user_stats_key, "total_tokens", execution.token_usage.total_tokens)
        await self._increment_float_stat(agent_stats_key, "total_cost", execution.cost_estimate.total_cost)
        await self._increment_float_stat(user_stats_key, "total_cost", execution.cost_estimate.total_cost)
        
        logger.info(
            f"Completed execution {execution_id}: "
            f"status={execution.status.value}, "
            f"duration={execution.duration_ms:.0f}ms, "
            f"tokens={execution.token_usage.total_tokens}, "
            f"cost=${execution.cost_estimate.total_cost:.4f}"
        )
        
        # Clean up in-memory cache
        del self.executions[execution_id]
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details."""
        # Check in-memory first
        if execution_id in self.executions:
            return self.executions[execution_id].to_dict()
        
        # Check Redis
        key = self.execution_key.format(execution_id=execution_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        
        return None
    
    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for an agent."""
        key = self.agent_stats_key.format(agent_id=agent_id)
        stats = await self.redis.hgetall(key)
        
        return {
            "agent_id": agent_id,
            "total_executions": int(stats.get(b"total_executions", 0)),
            "successful_executions": int(stats.get(b"successful_executions", 0)),
            "failed_executions": int(stats.get(b"failed_executions", 0)),
            "total_tokens": int(stats.get(b"total_tokens", 0)),
            "total_cost": float(stats.get(b"total_cost", 0)),
            "success_rate": self._calculate_success_rate(stats),
        }
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user."""
        key = self.user_stats_key.format(user_id=user_id)
        stats = await self.redis.hgetall(key)
        
        return {
            "user_id": user_id,
            "total_executions": int(stats.get(b"total_executions", 0)),
            "successful_executions": int(stats.get(b"successful_executions", 0)),
            "failed_executions": int(stats.get(b"failed_executions", 0)),
            "total_tokens": int(stats.get(b"total_tokens", 0)),
            "total_cost": float(stats.get(b"total_cost", 0)),
            "success_rate": self._calculate_success_rate(stats),
        }
    
    async def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily statistics."""
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        key = self.daily_stats_key.format(date=date)
        stats = await self.redis.hgetall(key)
        
        return {
            "date": date,
            "total_executions": int(stats.get(b"total_executions", 0)),
            "successful_executions": int(stats.get(b"successful_executions", 0)),
            "failed_executions": int(stats.get(b"failed_executions", 0)),
            "success_rate": self._calculate_success_rate(stats),
        }
    
    async def get_recent_executions(
        self,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent executions."""
        # This would typically query a database
        # For now, return from in-memory cache
        executions = list(self.executions.values())
        
        if agent_id:
            executions = [e for e in executions if e.agent_id == agent_id]
        if user_id:
            executions = [e for e in executions if e.user_id == user_id]
        
        # Sort by started_at descending
        executions.sort(key=lambda e: e.started_at, reverse=True)
        
        return [e.to_dict() for e in executions[:limit]]
    
    async def _save_execution(self, execution: AgentExecution):
        """Save execution to Redis."""
        key = self.execution_key.format(execution_id=execution.execution_id)
        await self.redis.setex(
            key,
            3600 * 24,  # 24 hour TTL
            json.dumps(execution.to_dict())
        )
    
    async def _increment_stat(self, key: str, field: str, amount: int = 1):
        """Increment a stat field."""
        await self.redis.hincrby(key, field, amount)
    
    async def _increment_float_stat(self, key: str, field: str, amount: float):
        """Increment a float stat field."""
        await self.redis.hincrbyfloat(key, field, amount)
    
    def _calculate_success_rate(self, stats: Dict) -> float:
        """Calculate success rate from stats."""
        total = int(stats.get(b"total_executions", 0))
        successful = int(stats.get(b"successful_executions", 0))
        
        if total == 0:
            return 0.0
        
        return round(successful / total * 100, 2)


# ============================================================================
# Global Instance
# ============================================================================

_monitoring_service: Optional[AgentMonitoringService] = None


async def get_monitoring_service(redis: Redis) -> AgentMonitoringService:
    """Get or create monitoring service."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = AgentMonitoringService(redis)
    return _monitoring_service
