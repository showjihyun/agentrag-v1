"""
Saga Pattern Implementation for Distributed Transactions

Provides orchestration and compensation for multi-step transactions.
"""

import logging
import uuid
from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class SagaState(str, Enum):
    """Saga execution state."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


@dataclass
class SagaStep:
    """
    Saga step definition.
    
    Each step has an action (forward transaction) and a compensate
    function (rollback transaction).
    """
    
    name: str
    action: Callable
    compensate: Callable
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SagaExecution:
    """Saga execution record."""
    
    id: str
    state: SagaState
    started_at: datetime
    completed_at: Optional[datetime] = None
    completed_steps: List[str] = None
    failed_step: Optional[str] = None
    error: Optional[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.completed_steps is None:
            self.completed_steps = []
        if self.context is None:
            self.context = {}


class SagaOrchestrator:
    """
    Saga Orchestrator for managing distributed transactions.
    
    Implements the Saga pattern with compensation logic for rollback.
    Supports retry, timeout, and error handling.
    """
    
    def __init__(self, name: str = "saga"):
        """
        Initialize Saga Orchestrator.
        
        Args:
            name: Saga name for logging
        """
        self.name = name
        self.steps: List[SagaStep] = []
        self.execution: Optional[SagaExecution] = None
    
    def add_step(
        self,
        name: str,
        action: Callable,
        compensate: Callable,
        timeout: Optional[float] = None,
        max_retries: int = 3
    ) -> "SagaOrchestrator":
        """
        Add a step to the saga.
        
        Args:
            name: Step name
            action: Forward transaction function
            compensate: Compensation (rollback) function
            timeout: Step timeout in seconds
            max_retries: Maximum retry attempts
            
        Returns:
            Self for chaining
        """
        step = SagaStep(
            name=name,
            action=action,
            compensate=compensate,
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.steps.append(step)
        
        logger.info(
            f"Saga step added: {name}",
            extra={"saga": self.name, "step": name}
        )
        
        return self
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the saga.
        
        Args:
            context: Initial context data
            
        Returns:
            Final context after all steps
            
        Raises:
            Exception: If saga fails and compensation also fails
        """
        # Initialize execution
        self.execution = SagaExecution(
            id=str(uuid.uuid4()),
            state=SagaState.RUNNING,
            started_at=datetime.utcnow(),
            context=context or {}
        )
        
        logger.info(
            f"Saga started: {self.name}",
            extra={
                "saga": self.name,
                "execution_id": self.execution.id,
                "steps": len(self.steps)
            }
        )
        
        try:
            # Execute each step
            for step in self.steps:
                await self._execute_step(step)
            
            # Mark as completed
            self.execution.state = SagaState.COMPLETED
            self.execution.completed_at = datetime.utcnow()
            
            logger.info(
                f"Saga completed: {self.name}",
                extra={
                    "saga": self.name,
                    "execution_id": self.execution.id,
                    "duration": (
                        self.execution.completed_at - self.execution.started_at
                    ).total_seconds()
                }
            )
            
            return self.execution.context
            
        except Exception as e:
            # Mark as failed
            self.execution.state = SagaState.FAILED
            self.execution.error = str(e)
            
            logger.error(
                f"Saga failed: {self.name}",
                extra={
                    "saga": self.name,
                    "execution_id": self.execution.id,
                    "failed_step": self.execution.failed_step,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Execute compensation
            await self._compensate()
            
            raise
    
    async def _execute_step(self, step: SagaStep):
        """
        Execute a single saga step with retry logic.
        
        Args:
            step: Step to execute
            
        Raises:
            Exception: If step fails after all retries
        """
        logger.info(
            f"Executing saga step: {step.name}",
            extra={
                "saga": self.name,
                "step": step.name,
                "execution_id": self.execution.id
            }
        )
        
        last_error = None
        
        # Retry loop
        for attempt in range(step.max_retries + 1):
            try:
                # Execute action
                result = await step.action(self.execution.context)
                
                # Update context with result
                if result:
                    self.execution.context.update(result)
                
                # Mark step as completed
                self.execution.completed_steps.append(step.name)
                
                logger.info(
                    f"Saga step completed: {step.name}",
                    extra={
                        "saga": self.name,
                        "step": step.name,
                        "attempt": attempt + 1
                    }
                )
                
                return
                
            except Exception as e:
                last_error = e
                step.retry_count = attempt + 1
                
                if attempt < step.max_retries:
                    logger.warning(
                        f"Saga step failed, retrying: {step.name}",
                        extra={
                            "saga": self.name,
                            "step": step.name,
                            "attempt": attempt + 1,
                            "max_retries": step.max_retries,
                            "error": str(e)
                        }
                    )
                else:
                    logger.error(
                        f"Saga step failed after all retries: {step.name}",
                        extra={
                            "saga": self.name,
                            "step": step.name,
                            "attempts": attempt + 1,
                            "error": str(e)
                        },
                        exc_info=True
                    )
        
        # All retries exhausted
        self.execution.failed_step = step.name
        raise last_error
    
    async def _compensate(self):
        """
        Execute compensation (rollback) for completed steps.
        
        Compensation is executed in reverse order.
        """
        self.execution.state = SagaState.COMPENSATING
        
        logger.info(
            f"Starting saga compensation: {self.name}",
            extra={
                "saga": self.name,
                "execution_id": self.execution.id,
                "steps_to_compensate": len(self.execution.completed_steps)
            }
        )
        
        # Compensate in reverse order
        for step_name in reversed(self.execution.completed_steps):
            step = next(s for s in self.steps if s.name == step_name)
            
            try:
                logger.info(
                    f"Compensating step: {step_name}",
                    extra={
                        "saga": self.name,
                        "step": step_name
                    }
                )
                
                # Execute compensation
                await step.compensate(self.execution.context)
                
                logger.info(
                    f"Step compensated: {step_name}",
                    extra={
                        "saga": self.name,
                        "step": step_name
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Compensation failed for step: {step_name}",
                    extra={
                        "saga": self.name,
                        "step": step_name,
                        "error": str(e)
                    },
                    exc_info=True
                )
                # Continue compensating other steps
        
        self.execution.state = SagaState.COMPENSATED
        self.execution.completed_at = datetime.utcnow()
        
        logger.info(
            f"Saga compensation completed: {self.name}",
            extra={
                "saga": self.name,
                "execution_id": self.execution.id
            }
        )
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current execution status.
        
        Returns:
            Execution status or None if not started
        """
        if not self.execution:
            return None
        
        return {
            "id": self.execution.id,
            "state": self.execution.state.value,
            "started_at": self.execution.started_at.isoformat(),
            "completed_at": (
                self.execution.completed_at.isoformat()
                if self.execution.completed_at
                else None
            ),
            "completed_steps": self.execution.completed_steps,
            "failed_step": self.execution.failed_step,
            "error": self.execution.error,
            "total_steps": len(self.steps)
        }


class SagaBuilder:
    """
    Builder for creating sagas with fluent API.
    
    Example:
        saga = (
            SagaBuilder("create_workflow")
            .step("create_workflow", create_fn, delete_fn)
            .step("create_nodes", create_nodes_fn, delete_nodes_fn)
            .step("compile", compile_fn, clear_cache_fn)
            .build()
        )
    """
    
    def __init__(self, name: str):
        """
        Initialize Saga Builder.
        
        Args:
            name: Saga name
        """
        self.orchestrator = SagaOrchestrator(name)
    
    def step(
        self,
        name: str,
        action: Callable,
        compensate: Callable,
        timeout: Optional[float] = None,
        max_retries: int = 3
    ) -> "SagaBuilder":
        """
        Add a step to the saga.
        
        Args:
            name: Step name
            action: Forward transaction function
            compensate: Compensation function
            timeout: Step timeout
            max_retries: Maximum retries
            
        Returns:
            Self for chaining
        """
        self.orchestrator.add_step(
            name=name,
            action=action,
            compensate=compensate,
            timeout=timeout,
            max_retries=max_retries
        )
        return self
    
    def build(self) -> SagaOrchestrator:
        """
        Build and return the saga orchestrator.
        
        Returns:
            Saga orchestrator
        """
        return self.orchestrator
