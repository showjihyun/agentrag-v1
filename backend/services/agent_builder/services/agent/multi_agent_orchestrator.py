"""
Multi-Agent Orchestrator for Agent Builder.

Coordinates multiple agents to work together on complex tasks.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session

from backend.services.agent_builder.agent_service import AgentService
from backend.services.agent_builder.workflow_executor import WorkflowExecutor
from backend.services.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class OrchestrationType(str, Enum):
    """Types of multi-agent orchestration patterns."""
    SEQUENTIAL = "sequential"  # Agents execute one after another
    PARALLEL = "parallel"      # Agents execute simultaneously
    HIERARCHICAL = "hierarchical"  # Manager agent delegates to worker agents
    DEBATE = "debate"          # Agents debate and reach consensus
    VOTING = "voting"          # Agents vote on best solution


class AgentRole(str, Enum):
    """Roles in multi-agent system."""
    MANAGER = "manager"        # Coordinates other agents
    WORKER = "worker"          # Executes specific tasks
    CRITIC = "critic"          # Reviews and critiques outputs
    SYNTHESIZER = "synthesizer"  # Combines multiple outputs


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents to collaborate on complex tasks.
    
    Features:
    - Multiple orchestration patterns
    - Dynamic agent selection
    - Context sharing between agents
    - Result aggregation
    - Error handling and fallback
    """
    
    def __init__(
        self,
        db: Session,
        agent_service: Optional[AgentService] = None,
        workflow_executor: Optional[WorkflowExecutor] = None,
        retry_handler: Optional[RetryHandler] = None
    ):
        """
        Initialize multi-agent orchestrator.
        
        Args:
            db: Database session
            agent_service: Agent service instance
            workflow_executor: Workflow executor instance
            retry_handler: Retry handler instance
        """
        self.db = db
        self.agent_service = agent_service or AgentService(db)
        self.workflow_executor = workflow_executor or WorkflowExecutor(db)
        self.retry_handler = retry_handler or RetryHandler(
            max_retries=3,
            base_delay=1.0
        )
        
        logger.info("MultiAgentOrchestrator initialized")
    
    async def orchestrate(
        self,
        agent_ids: List[str],
        task: str,
        strategy: OrchestrationType,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Orchestrate multiple agents to complete a task.
        
        Args:
            agent_ids: List of agent IDs to orchestrate
            task: Task description
            strategy: Orchestration strategy
            context: Shared context
            max_iterations: Maximum iterations for iterative strategies
            
        Returns:
            Orchestration result with outputs from all agents
        """
        logger.info(f"Starting orchestration with {len(agent_ids)} agents using {strategy} strategy")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Load agents
            agents = await self._load_agents(agent_ids)
            
            if not agents:
                raise ValueError("No valid agents found")
            
            # Initialize shared context
            shared_context = context or {}
            shared_context["task"] = task
            shared_context["orchestration_type"] = strategy.value
            
            # Execute orchestration based on strategy
            if strategy == OrchestrationType.SEQUENTIAL:
                result = await self._orchestrate_sequential(agents, task, shared_context)
            elif strategy == OrchestrationType.PARALLEL:
                result = await self._orchestrate_parallel(agents, task, shared_context)
            elif strategy == OrchestrationType.HIERARCHICAL:
                result = await self._orchestrate_hierarchical(agents, task, shared_context)
            elif strategy == OrchestrationType.DEBATE:
                result = await self._orchestrate_debate(agents, task, shared_context, max_iterations)
            elif strategy == OrchestrationType.VOTING:
                result = await self._orchestrate_voting(agents, task, shared_context)
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "strategy": strategy.value,
                "result": result,
                "duration_ms": duration_ms,
                "agents_used": len(agents),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _load_agents(self, agent_ids: List[str]) -> List[Any]:
        """Load agents from database."""
        agents = []
        
        for agent_id in agent_ids:
            try:
                agent = self.agent_service.get_agent(agent_id)
                if agent:
                    agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
        
        return agents
    
    async def _orchestrate_sequential(
        self,
        agents: List[Any],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sequential orchestration: agents execute one after another.
        Each agent's output becomes input for the next agent.
        """
        logger.info("Executing sequential orchestration")
        
        results = []
        current_input = task
        
        for i, agent in enumerate(agents):
            logger.info(f"Executing agent {i+1}/{len(agents)}: {agent.name}")
            
            try:
                # Execute agent
                output = await self._execute_agent(
                    agent,
                    current_input,
                    {**context, "previous_results": results}
                )
                
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "input": current_input,
                    "output": output,
                    "step": i + 1
                })
                
                # Use output as input for next agent
                current_input = output.get("content", output)
                
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "error": str(e),
                    "step": i + 1
                })
                # Continue with original input
        
        return {
            "final_output": current_input,
            "steps": results,
            "total_steps": len(results)
        }
    
    async def _orchestrate_parallel(
        self,
        agents: List[Any],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parallel orchestration: all agents execute simultaneously.
        Results are aggregated at the end.
        """
        logger.info("Executing parallel orchestration")
        
        # Execute all agents concurrently
        tasks = [
            self._execute_agent(agent, task, context)
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        agent_outputs = []
        for i, (agent, result) in enumerate(zip(agents, results)):
            if isinstance(result, Exception):
                agent_outputs.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "error": str(result)
                })
            else:
                agent_outputs.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": result
                })
        
        # Aggregate results
        aggregated = await self._aggregate_results(agent_outputs, task)
        
        return {
            "aggregated_output": aggregated,
            "individual_outputs": agent_outputs,
            "total_agents": len(agents)
        }
    
    async def _orchestrate_hierarchical(
        self,
        agents: List[Any],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hierarchical orchestration: manager agent delegates to worker agents.
        First agent is the manager, others are workers.
        """
        logger.info("Executing hierarchical orchestration")
        
        if len(agents) < 2:
            raise ValueError("Hierarchical orchestration requires at least 2 agents")
        
        manager = agents[0]
        workers = agents[1:]
        
        # Manager analyzes task and creates subtasks
        manager_output = await self._execute_agent(
            manager,
            f"Analyze this task and break it into subtasks for {len(workers)} workers: {task}",
            context
        )
        
        # Extract subtasks (simplified - in production, use structured output)
        subtasks = self._extract_subtasks(manager_output, len(workers))
        
        # Delegate to workers
        worker_tasks = [
            self._execute_agent(worker, subtask, context)
            for worker, subtask in zip(workers, subtasks)
        ]
        
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Manager synthesizes results
        synthesis_input = f"Original task: {task}\n\nWorker results:\n"
        for i, result in enumerate(worker_results):
            if not isinstance(result, Exception):
                synthesis_input += f"\nWorker {i+1}: {result.get('content', result)}\n"
        
        final_output = await self._execute_agent(
            manager,
            f"Synthesize these worker results into a final answer:\n{synthesis_input}",
            context
        )
        
        return {
            "final_output": final_output,
            "manager": {"agent_id": manager.id, "agent_name": manager.name},
            "subtasks": subtasks,
            "worker_results": [
                {
                    "agent_id": w.id,
                    "agent_name": w.name,
                    "result": r if not isinstance(r, Exception) else {"error": str(r)}
                }
                for w, r in zip(workers, worker_results)
            ]
        }
    
    async def _orchestrate_debate(
        self,
        agents: List[Any],
        task: str,
        context: Dict[str, Any],
        max_iterations: int
    ) -> Dict[str, Any]:
        """
        Debate orchestration: agents debate and refine their answers.
        """
        logger.info(f"Executing debate orchestration with {max_iterations} rounds")
        
        debate_history = []
        
        # Initial responses
        current_responses = {}
        for agent in agents:
            response = await self._execute_agent(agent, task, context)
            current_responses[agent.id] = response
            debate_history.append({
                "round": 0,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "response": response
            })
        
        # Debate rounds
        for round_num in range(1, max_iterations + 1):
            logger.info(f"Debate round {round_num}/{max_iterations}")
            
            new_responses = {}
            
            for agent in agents:
                # Show other agents' responses
                other_responses = "\n\n".join([
                    f"{a.name}: {current_responses[a.id].get('content', current_responses[a.id])}"
                    for a in agents if a.id != agent.id
                ])
                
                debate_prompt = f"""Original task: {task}

Your previous response: {current_responses[agent.id].get('content', current_responses[agent.id])}

Other agents' responses:
{other_responses}

Consider the other responses and refine your answer. What do you agree or disagree with?"""
                
                response = await self._execute_agent(agent, debate_prompt, context)
                new_responses[agent.id] = response
                
                debate_history.append({
                    "round": round_num,
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "response": response
                })
            
            current_responses = new_responses
        
        # Final consensus
        consensus = await self._build_consensus(agents, current_responses, task)
        
        return {
            "consensus": consensus,
            "debate_history": debate_history,
            "total_rounds": max_iterations + 1
        }
    
    async def _orchestrate_voting(
        self,
        agents: List[Any],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Voting orchestration: agents propose solutions and vote on the best one.
        """
        logger.info("Executing voting orchestration")
        
        # Phase 1: Generate proposals
        proposals = []
        for agent in agents:
            response = await self._execute_agent(agent, task, context)
            proposals.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "proposal": response
            })
        
        # Phase 2: Voting
        votes = {i: 0 for i in range(len(proposals))}
        vote_details = []
        
        for agent in agents:
            # Present all proposals
            proposals_text = "\n\n".join([
                f"Proposal {i+1} by {p['agent_name']}:\n{p['proposal'].get('content', p['proposal'])}"
                for i, p in enumerate(proposals)
            ])
            
            vote_prompt = f"""Task: {task}

Here are the proposals:
{proposals_text}

Vote for the best proposal by responding with just the number (1-{len(proposals)}).
Consider accuracy, completeness, and clarity."""
            
            vote_response = await self._execute_agent(agent, vote_prompt, context)
            
            # Extract vote (simplified)
            try:
                vote_num = int(vote_response.get("content", "1").strip().split()[0]) - 1
                if 0 <= vote_num < len(proposals):
                    votes[vote_num] += 1
                    vote_details.append({
                        "voter": agent.name,
                        "voted_for": proposals[vote_num]["agent_name"]
                    })
            except:
                logger.warning(f"Invalid vote from {agent.name}")
        
        # Determine winner
        winner_idx = max(votes, key=votes.get)
        winner = proposals[winner_idx]
        
        return {
            "winning_proposal": winner,
            "votes": votes,
            "vote_details": vote_details,
            "all_proposals": proposals
        }
    
    async def _execute_agent(
        self,
        agent: Any,
        input_text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single agent."""
        try:
            # Use workflow executor to run agent
            result = await self.workflow_executor._execute_agent(
                agent,
                {"query": input_text, **context},
                context
            )
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {"error": str(e), "content": ""}
    
    async def _aggregate_results(
        self,
        outputs: List[Dict[str, Any]],
        task: str
    ) -> str:
        """Aggregate multiple agent outputs into a single result."""
        # Simple aggregation - in production, use an LLM to synthesize
        valid_outputs = [
            o["output"].get("content", o["output"])
            for o in outputs
            if "error" not in o
        ]
        
        if not valid_outputs:
            return "All agents failed to produce output"
        
        # Combine outputs
        combined = "\n\n".join([
            f"Agent {i+1} output:\n{output}"
            for i, output in enumerate(valid_outputs)
        ])
        
        return f"Aggregated results from {len(valid_outputs)} agents:\n\n{combined}"
    
    def _extract_subtasks(
        self,
        manager_output: Dict[str, Any],
        num_workers: int
    ) -> List[str]:
        """Extract subtasks from manager output."""
        # Simplified extraction - in production, use structured output
        content = manager_output.get("content", "")
        
        # Try to split by numbered list
        lines = content.split("\n")
        subtasks = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                # Remove numbering/bullets
                task = line.lstrip("0123456789.-* ")
                if task:
                    subtasks.append(task)
        
        # Ensure we have enough subtasks
        while len(subtasks) < num_workers:
            subtasks.append(f"Help with: {content[:100]}")
        
        return subtasks[:num_workers]
    
    async def _build_consensus(
        self,
        agents: List[Any],
        responses: Dict[str, Dict[str, Any]],
        task: str
    ) -> str:
        """Build consensus from debate responses."""
        # Combine final responses
        final_responses = "\n\n".join([
            f"{agent.name}: {responses[agent.id].get('content', responses[agent.id])}"
            for agent in agents
        ])
        
        return f"Consensus after debate:\n\n{final_responses}"


# Example usage
EXAMPLE_SEQUENTIAL = {
    "agent_ids": ["agent1", "agent2", "agent3"],
    "task": "Analyze this document and create a summary",
    "strategy": "sequential",
    "context": {"document": "..."}
}

EXAMPLE_PARALLEL = {
    "agent_ids": ["agent1", "agent2", "agent3"],
    "task": "Research this topic from different perspectives",
    "strategy": "parallel",
    "context": {"topic": "AI safety"}
}

EXAMPLE_HIERARCHICAL = {
    "agent_ids": ["manager_agent", "worker1", "worker2", "worker3"],
    "task": "Create a comprehensive report on market trends",
    "strategy": "hierarchical",
    "context": {}
}
