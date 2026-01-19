"""
Agentflow Orchestrator

Orchestrates multi-agent execution based on orchestration type.
Supports sequential, parallel, hierarchical, and adaptive patterns.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from backend.db.models.flows import Agentflow, AgentflowAgent, AgentflowEdge, FlowExecution
from backend.services.agent_builder.agentflow_agent_executor import AgentflowAgentExecutor
from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService

logger = logging.getLogger(__name__)


class AgentflowOrchestrator:
    """
    Orchestrates agent execution in agentflows.
    
    Supports multiple orchestration patterns:
    - Sequential: Agents execute one after another
    - Parallel: Agents execute simultaneously
    - Hierarchical: Manager agents coordinate worker agents
    - Adaptive: Dynamic routing based on conditions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_executor = AgentflowAgentExecutor(db)
        self.integration_service = AgentWorkflowIntegrationService(db)
    
    async def execute_agentflow(
        self,
        agentflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute an agentflow with the specified orchestration pattern.
        
        Args:
            agentflow_id: ID of the agentflow
            input_data: Input data for the flow
            user_id: User ID for execution
            
        Returns:
            Execution result with outputs from all agents
        """
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())
        
        logger.info(f"Starting agentflow execution: {agentflow_id}, execution_id: {execution_id}")
        
        # Get agentflow
        agentflow = self.db.query(Agentflow).filter(
            Agentflow.id == uuid.UUID(agentflow_id)
        ).first()
        
        if not agentflow:
            return {
                "success": False,
                "error": f"Agentflow {agentflow_id} not found",
            }
        
        # Create execution record
        execution = FlowExecution(
            id=uuid.UUID(execution_id),
            agentflow_id=uuid.UUID(agentflow_id),
            user_id=uuid.UUID(user_id),
            input_data=input_data,
            status="running",
            started_at=start_time,
        )
        self.db.add(execution)
        self.db.commit()
        
        try:
            # Get execution plan
            plan = self.integration_service.get_agentflow_execution_plan(agentflow_id)
            
            # Execute based on orchestration type
            orchestration_type = agentflow.orchestration_type
            
            if orchestration_type == "sequential":
                result = await self._execute_sequential(plan, input_data, user_id)
            elif orchestration_type == "parallel":
                result = await self._execute_parallel(plan, input_data, user_id)
            elif orchestration_type == "hierarchical":
                result = await self._execute_hierarchical(plan, input_data, user_id)
            elif orchestration_type == "adaptive":
                result = await self._execute_adaptive(plan, input_data, user_id)
            else:
                # Default to sequential for advanced types
                logger.warning(f"Orchestration type {orchestration_type} not fully implemented, using sequential")
                result = await self._execute_sequential(plan, input_data, user_id)
            
            # Update execution record
            execution.status = "completed" if result.get("success") else "failed"
            execution.output_data = result.get("output", {})
            execution.error_message = result.get("error")
            execution.completed_at = datetime.utcnow()
            
            # Update agentflow statistics
            agentflow.execution_count = (agentflow.execution_count or 0) + 1
            agentflow.last_execution_status = execution.status
            agentflow.last_execution_at = execution.completed_at
            
            self.db.commit()
            
            duration_ms = int((execution.completed_at - start_time).total_seconds() * 1000)
            
            return {
                "success": result.get("success", False),
                "execution_id": execution_id,
                "agentflow_id": agentflow_id,
                "orchestration_type": orchestration_type,
                "output": result.get("output", {}),
                "agent_results": result.get("agent_results", []),
                "error": result.get("error"),
                "duration_ms": duration_ms,
            }
            
        except Exception as e:
            logger.error(f"Agentflow execution failed: {e}", exc_info=True)
            
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
            }
    
    async def _execute_sequential(
        self,
        plan: Dict[str, Any],
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute agents sequentially, passing output from one to the next.
        """
        logger.info("Executing agentflow in sequential mode")
        
        execution_context = {
            "input": input_data,
            "agent_results": {},
        }
        
        agent_results = []
        current_input = input_data
        
        stages = plan.get("stages", [])
        
        for stage in stages:
            stage_agents = stage.get("agents", [])
            
            for agent_info in stage_agents:
                # Get AgentflowAgent
                agentflow_agent = self.db.query(AgentflowAgent).filter(
                    AgentflowAgent.id == uuid.UUID(agent_info["id"])
                ).first()
                
                if not agentflow_agent:
                    logger.warning(f"Agent {agent_info['id']} not found, skipping")
                    continue
                
                # Execute agent
                result = await self.agent_executor.execute_agent(
                    agentflow_agent=agentflow_agent,
                    input_data=current_input,
                    execution_context=execution_context,
                    user_id=user_id,
                )
                
                agent_results.append(result)
                
                # Store result in context
                execution_context["agent_results"][agent_info["id"]] = result
                
                # Use output as input for next agent
                if result.get("success"):
                    current_input = result.get("output", {})
                else:
                    # Stop on failure
                    return {
                        "success": False,
                        "error": f"Agent {agent_info['name']} failed: {result.get('error')}",
                        "agent_results": agent_results,
                        "output": {},
                    }
        
        # Final output is the last agent's output
        final_output = current_input if agent_results else {}
        
        return {
            "success": True,
            "output": final_output,
            "agent_results": agent_results,
        }
    
    async def _execute_parallel(
        self,
        plan: Dict[str, Any],
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute agents in parallel groups.
        """
        logger.info("Executing agentflow in parallel mode")
        
        execution_context = {
            "input": input_data,
            "agent_results": {},
        }
        
        all_agent_results = []
        groups = plan.get("groups", [])
        
        for group in groups:
            group_agents = group.get("agents", [])
            
            # Execute all agents in group concurrently
            tasks = []
            for agent_info in group_agents:
                agentflow_agent = self.db.query(AgentflowAgent).filter(
                    AgentflowAgent.id == uuid.UUID(agent_info["id"])
                ).first()
                
                if agentflow_agent:
                    task = self.agent_executor.execute_agent(
                        agentflow_agent=agentflow_agent,
                        input_data=input_data,
                        execution_context=execution_context,
                        user_id=user_id,
                    )
                    tasks.append((agent_info["id"], task))
            
            # Wait for all agents in group to complete
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # Process results
            for (agent_id, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    result = {
                        "success": False,
                        "agent_id": agent_id,
                        "error": str(result),
                    }
                
                all_agent_results.append(result)
                execution_context["agent_results"][agent_id] = result
        
        # Aggregate outputs from all agents
        aggregated_output = {
            "results": [r.get("output", {}) for r in all_agent_results if r.get("success")],
            "summary": f"Executed {len(all_agent_results)} agents in parallel",
        }
        
        # Check if any failed
        failed = [r for r in all_agent_results if not r.get("success")]
        if failed:
            return {
                "success": False,
                "error": f"{len(failed)} agents failed",
                "agent_results": all_agent_results,
                "output": aggregated_output,
            }
        
        return {
            "success": True,
            "output": aggregated_output,
            "agent_results": all_agent_results,
        }
    
    async def _execute_hierarchical(
        self,
        plan: Dict[str, Any],
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute with hierarchical coordination (manager delegates to workers).
        """
        logger.info("Executing agentflow in hierarchical mode")
        
        execution_context = {
            "input": input_data,
            "agent_results": {},
        }
        
        agent_results = []
        
        # Execute manager agents first
        managers = plan.get("managers", [])
        manager_outputs = []
        
        for manager_info in managers:
            agentflow_agent = self.db.query(AgentflowAgent).filter(
                AgentflowAgent.id == uuid.UUID(manager_info["id"])
            ).first()
            
            if agentflow_agent:
                result = await self.agent_executor.execute_agent(
                    agentflow_agent=agentflow_agent,
                    input_data=input_data,
                    execution_context=execution_context,
                    user_id=user_id,
                )
                
                agent_results.append(result)
                execution_context["agent_results"][manager_info["id"]] = result
                
                if result.get("success"):
                    manager_outputs.append(result.get("output", {}))
        
        # Execute worker agents with manager's guidance
        workers = plan.get("workers", [])
        worker_tasks = []
        
        for worker_info in workers:
            agentflow_agent = self.db.query(AgentflowAgent).filter(
                AgentflowAgent.id == uuid.UUID(worker_info["id"])
            ).first()
            
            if agentflow_agent:
                # Pass manager output as context
                worker_input = {
                    **input_data,
                    "manager_guidance": manager_outputs,
                }
                
                task = self.agent_executor.execute_agent(
                    agentflow_agent=agentflow_agent,
                    input_data=worker_input,
                    execution_context=execution_context,
                    user_id=user_id,
                )
                worker_tasks.append((worker_info["id"], task))
        
        # Wait for workers
        worker_results = await asyncio.gather(*[task for _, task in worker_tasks], return_exceptions=True)
        
        for (worker_id, _), result in zip(worker_tasks, worker_results):
            if isinstance(result, Exception):
                result = {
                    "success": False,
                    "agent_id": worker_id,
                    "error": str(result),
                }
            
            agent_results.append(result)
            execution_context["agent_results"][worker_id] = result
        
        # Aggregate results
        final_output = {
            "manager_decisions": manager_outputs,
            "worker_results": [r.get("output", {}) for r in agent_results if r.get("success") and r.get("role") != "manager"],
        }
        
        return {
            "success": True,
            "output": final_output,
            "agent_results": agent_results,
        }
    
    async def _execute_adaptive(
        self,
        plan: Dict[str, Any],
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute with adaptive routing based on conditions.
        """
        logger.info("Executing agentflow in adaptive mode")
        
        execution_context = {
            "input": input_data,
            "agent_results": {},
        }
        
        agent_results = []
        agents = plan.get("agents", [])
        edges = plan.get("edges", [])
        
        # Start with first agent
        current_agent_id = agents[0]["id"] if agents else None
        visited = set()
        
        while current_agent_id and current_agent_id not in visited:
            visited.add(current_agent_id)
            
            # Find agent
            agent_info = next((a for a in agents if a["id"] == current_agent_id), None)
            if not agent_info:
                break
            
            agentflow_agent = self.db.query(AgentflowAgent).filter(
                AgentflowAgent.id == uuid.UUID(current_agent_id)
            ).first()
            
            if not agentflow_agent:
                break
            
            # Execute agent
            result = await self.agent_executor.execute_agent(
                agentflow_agent=agentflow_agent,
                input_data=input_data,
                execution_context=execution_context,
                user_id=user_id,
            )
            
            agent_results.append(result)
            execution_context["agent_results"][current_agent_id] = result
            
            if not result.get("success"):
                break
            
            # Find next agent based on conditions
            next_agent_id = None
            for edge in edges:
                if edge["source"] == current_agent_id:
                    condition = edge.get("condition", {})
                    if self._evaluate_condition(condition, execution_context):
                        next_agent_id = edge["target"]
                        break
            
            current_agent_id = next_agent_id
        
        # Final output
        final_output = agent_results[-1].get("output", {}) if agent_results else {}
        
        return {
            "success": True,
            "output": final_output,
            "agent_results": agent_results,
        }
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> bool:
        """Evaluate a condition for adaptive routing."""
        if not condition:
            return True
        
        # Simple condition evaluation
        # Can be extended with more complex logic
        return True
