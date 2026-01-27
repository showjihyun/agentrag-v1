"""
Agentflow Executor Service

Specialized executor for Agentflows with multi-agent orchestration,
tool execution, and advanced flow control.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json

from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Workflow, WorkflowExecution, Agent
from backend.db.models.flows import Agentflow, AgentflowAgent, AgentflowEdge, FlowExecution
from backend.services.agent_builder.workflow_executor import WorkflowExecutor
from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
from backend.db.models.flows import TokenUsage

logger = logging.getLogger(__name__)


class AgentflowExecutor:
    """
    Specialized executor for Agentflows.
    
    Agentflows are workflows that include AI Agent nodes and support:
    - Multi-agent orchestration
    - Tool execution with retry logic
    - Parallel agent execution
    - Memory management across agents
    - Token usage tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.token_usage: List[Dict[str, Any]] = []
    
    async def execute(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute an Agentflow.
        
        Args:
            workflow: Workflow to execute
            input_data: Input data for the workflow
            user_id: User ID for tracking
            execution_id: Optional execution ID for SSE updates
            
        Returns:
            Execution result
        """
        start_time = datetime.utcnow()
        exec_id = execution_id or str(uuid.uuid4())
        
        logger.info(f"Starting Agentflow execution: {workflow.id}, execution_id: {exec_id}")
        
        # Create execution record
        execution = WorkflowExecution(
            id=uuid.UUID(exec_id) if isinstance(exec_id, str) else exec_id,
            workflow_id=workflow.id,
            user_id=uuid.UUID(user_id),
            input_data=input_data,
            execution_context={},
            status="running",
            started_at=start_time,
        )
        
        self.db.add(execution)
        self.db.commit()
        
        try:
            # Add user_id to input for API key retrieval
            input_with_user = {
                **input_data,
                "_user_id": user_id,
            }
            
            # Use the main workflow executor
            executor = WorkflowExecutor(workflow, self.db, exec_id)
            result = await executor.execute(input_with_user)
            
            # Update execution record
            execution.status = "completed" if result.get("success") else "failed"
            execution.output_data = result.get("output", {})
            execution.execution_context = result.get("execution_context", {})
            execution.error_message = result.get("error")
            execution.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Record token usage from execution context
            await self._record_token_usage(
                execution_context=result.get("execution_context", {}),
                user_id=user_id,
                workflow_id=str(workflow.id),
                execution_id=exec_id,
            )
            
            logger.info(f"Agentflow execution completed: {exec_id}, status: {execution.status}")
            
            return {
                "success": result.get("success", False),
                "execution_id": exec_id,
                "status": execution.status,
                "output": result.get("output"),
                "error": result.get("error"),
                "duration_ms": int((execution.completed_at - start_time).total_seconds() * 1000),
                "token_usage": self.token_usage,
            }
            
        except Exception as e:
            logger.error(f"Agentflow execution failed: {e}", exc_info=True)
            
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": False,
                "execution_id": exec_id,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            }
    
    async def execute_with_streaming(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any],
        user_id: str,
    ):
        """
        Execute an Agentflow with SSE streaming.
        
        Yields:
            SSE formatted events for execution progress
        """
        import json
        
        exec_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        yield f"data: {json.dumps({'type': 'start', 'execution_id': exec_id, 'workflow_id': str(workflow.id)})}\n\n"
        
        try:
            # Create execution record
            execution = WorkflowExecution(
                id=uuid.UUID(exec_id),
                workflow_id=workflow.id,
                user_id=uuid.UUID(user_id),
                input_data=input_data,
                execution_context={},
                status="running",
                started_at=start_time,
            )
            
            self.db.add(execution)
            self.db.commit()
            
            yield f"data: {json.dumps({'type': 'status', 'status': 'running'})}\n\n"
            
            # Add user_id to input
            input_with_user = {
                **input_data,
                "_user_id": user_id,
            }
            
            # Execute workflow
            executor = WorkflowExecutor(workflow, self.db, exec_id)
            result = await executor.execute(input_with_user)
            
            # Send node execution updates
            node_executions = result.get("execution_context", {}).get("node_executions", [])
            for node_exec in node_executions:
                yield f"data: {json.dumps({'type': 'node', 'node': node_exec})}\n\n"
                await asyncio.sleep(0.01)
            
            # Update execution record
            execution.status = "completed" if result.get("success") else "failed"
            execution.output_data = result.get("output", {})
            execution.execution_context = result.get("execution_context", {})
            execution.error_message = result.get("error")
            execution.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Record token usage
            await self._record_token_usage(
                execution_context=result.get("execution_context", {}),
                user_id=user_id,
                workflow_id=str(workflow.id),
                execution_id=exec_id,
            )
            
            # Send completion
            duration_ms = int((execution.completed_at - start_time).total_seconds() * 1000)
            yield f"data: {json.dumps({'type': 'complete', 'status': execution.status, 'output': result.get('output'), 'duration_ms': duration_ms})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Agentflow streaming execution failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    async def _record_token_usage(
        self,
        execution_context: Dict[str, Any],
        user_id: str,
        workflow_id: str,
        execution_id: str,
    ):
        """Record token usage from execution context."""
        try:
            node_executions = execution_context.get("node_executions", [])
            
            for node_exec in node_executions:
                # Check if this is an AI Agent node
                if node_exec.get("tool_id") == "ai_agent" or node_exec.get("node_type") == "ai_agent":
                    ai_details = node_exec.get("ai_agent_details", {})
                    
                    if ai_details:
                        provider = ai_details.get("provider", "unknown")
                        model = ai_details.get("model", "unknown")
                        
                        # Estimate tokens from response length
                        response_length = ai_details.get("response_length", 0)
                        output_tokens = response_length // 4
                        
                        # Estimate input tokens from prompts
                        system_prompt_len = len(ai_details.get("system_prompt", ""))
                        user_message_len = len(ai_details.get("user_message", ""))
                        input_tokens = (system_prompt_len + user_message_len) // 4
                        
                        # Calculate cost
                        from backend.api.agent_builder.cost_tracking import calculate_cost
                        cost = calculate_cost(self.db, provider, model, input_tokens, output_tokens)
                        
                        # Record usage
                        usage = TokenUsage(
                            user_id=uuid.UUID(user_id),
                            workflow_id=uuid.UUID(workflow_id),
                            flow_execution_id=uuid.UUID(execution_id),
                            provider=provider,
                            model=model,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=input_tokens + output_tokens,
                            cost_usd=cost,
                            node_id=node_exec.get("node_id"),
                            node_type="ai_agent",
                        )
                        
                        self.db.add(usage)
                        
                        self.token_usage.append({
                            "node_id": node_exec.get("node_id"),
                            "provider": provider,
                            "model": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost_usd": cost,
                        })
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record token usage: {e}")
            self.db.rollback()


async def execute_agentflow(
    workflow: Workflow,
    db: Session,
    input_data: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """
    Convenience function to execute an Agentflow.
    
    Args:
        workflow: Workflow to execute
        db: Database session
        input_data: Input data
        user_id: User ID
        
    Returns:
        Execution result
    """
    executor = AgentflowExecutor(db)
    return await executor.execute(workflow, input_data, user_id)
