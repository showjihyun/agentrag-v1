"""
Planning Block - Agentic Design Pattern

Implements the Planning pattern with task decomposition.
Breaks down complex tasks into manageable subtasks and executes them.

Key Features:
- Automatic task decomposition
- Subtask dependency management
- Progress tracking
- Adaptive replanning on failure
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import asyncio

from backend.services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class SubtaskStatus(str, Enum):
    """Status of a subtask."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Subtask:
    """Represents a single subtask in the plan."""
    
    def __init__(
        self,
        id: str,
        description: str,
        dependencies: List[str] = None,
        estimated_complexity: float = 0.5,
        required_tools: List[str] = None,
    ):
        self.id = id
        self.description = description
        self.dependencies = dependencies or []
        self.estimated_complexity = estimated_complexity
        self.required_tools = required_tools or []
        self.status = SubtaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "dependencies": self.dependencies,
            "estimated_complexity": self.estimated_complexity,
            "required_tools": self.required_tools,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class PlanningBlock:
    """
    Planning Block for task decomposition and execution.
    
    Decomposes complex tasks into subtasks, manages dependencies,
    and executes them in the correct order.
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        max_subtasks: int = 10,
        enable_replanning: bool = True,
        parallel_execution: bool = False,
    ):
        """
        Initialize Planning Block.
        
        Args:
            llm_manager: LLM manager for planning
            max_subtasks: Maximum number of subtasks to generate
            enable_replanning: Whether to replan on failure
            parallel_execution: Execute independent subtasks in parallel
        """
        self.llm_manager = llm_manager
        self.max_subtasks = max_subtasks
        self.enable_replanning = enable_replanning
        self.parallel_execution = parallel_execution
        
        self.current_plan: List[Subtask] = []
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        executor: Callable[[Subtask, Dict[str, Any]], Any],
        available_tools: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute planning workflow.
        
        Args:
            task: Main task description
            context: Context information
            executor: Async function to execute each subtask
            available_tools: List of available tool names
            
        Returns:
            Dict containing:
                - success: Whether all subtasks completed
                - plan: List of subtasks
                - results: Results from each subtask
                - execution_time: Total execution time
                - replanning_count: Number of replans
        """
        start_time = datetime.utcnow()
        replanning_count = 0
        
        logger.info(f"Starting planning for task: {task}")
        
        # Step 1: Generate initial plan
        self.current_plan = await self._generate_plan(
            task=task,
            context=context,
            available_tools=available_tools or [],
        )
        
        logger.info(f"Generated plan with {len(self.current_plan)} subtasks")
        
        # Step 2: Execute plan
        execution_result = await self._execute_plan(
            executor=executor,
            context=context,
        )
        
        # Step 3: Handle failures with replanning
        while not execution_result["success"] and self.enable_replanning and replanning_count < 2:
            replanning_count += 1
            logger.warning(f"Plan execution failed, replanning (attempt {replanning_count})")
            
            # Analyze failures
            failed_subtasks = [
                st for st in self.current_plan 
                if st.status == SubtaskStatus.FAILED
            ]
            
            # Generate new plan considering failures
            self.current_plan = await self._replan(
                task=task,
                context=context,
                failed_subtasks=failed_subtasks,
                available_tools=available_tools or [],
            )
            
            # Execute new plan
            execution_result = await self._execute_plan(
                executor=executor,
                context=context,
            )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Collect results
        results = {
            st.id: st.result 
            for st in self.current_plan 
            if st.status == SubtaskStatus.COMPLETED
        }
        
        return {
            "success": execution_result["success"],
            "plan": [st.to_dict() for st in self.current_plan],
            "results": results,
            "execution_time": execution_time,
            "replanning_count": replanning_count,
            "total_subtasks": len(self.current_plan),
            "completed_subtasks": len([st for st in self.current_plan if st.status == SubtaskStatus.COMPLETED]),
            "failed_subtasks": len([st for st in self.current_plan if st.status == SubtaskStatus.FAILED]),
        }
    
    async def _generate_plan(
        self,
        task: str,
        context: Dict[str, Any],
        available_tools: List[str],
    ) -> List[Subtask]:
        """
        Generate plan by decomposing task into subtasks.
        
        Returns:
            List of Subtask objects
        """
        planning_prompt = f"""You are an expert task planner. Break down the following task into clear, actionable subtasks.

Task: {task}

Context:
{self._format_context(context)}

Available Tools: {', '.join(available_tools) if available_tools else 'None'}

Generate a plan with up to {self.max_subtasks} subtasks. For each subtask, provide:
1. ID (e.g., "subtask_1", "subtask_2")
2. Description (clear, actionable description)
3. Dependencies (IDs of subtasks that must complete first)
4. Estimated Complexity (0.0-1.0, where 1.0 is most complex)
5. Required Tools (list of tool names needed)

Respond in JSON format:
{{
    "subtasks": [
        {{
            "id": "subtask_1",
            "description": "...",
            "dependencies": [],
            "estimated_complexity": 0.3,
            "required_tools": ["tool1"]
        }}
    ]
}}"""
        
        try:
            response = await self.llm_manager.generate(
                prompt=planning_prompt,
                temperature=0.5,
            )
            
            import json
            plan_data = json.loads(response)
            
            subtasks = []
            for st_data in plan_data.get("subtasks", [])[:self.max_subtasks]:
                subtask = Subtask(
                    id=st_data.get("id", f"subtask_{len(subtasks) + 1}"),
                    description=st_data.get("description", ""),
                    dependencies=st_data.get("dependencies", []),
                    estimated_complexity=st_data.get("estimated_complexity", 0.5),
                    required_tools=st_data.get("required_tools", []),
                )
                subtasks.append(subtask)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error generating plan: {e}", exc_info=True)
            # Fallback: create single subtask
            return [
                Subtask(
                    id="subtask_1",
                    description=task,
                    dependencies=[],
                    estimated_complexity=0.5,
                    required_tools=[],
                )
            ]
    
    async def _execute_plan(
        self,
        executor: Callable,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute all subtasks in the plan.
        
        Returns:
            Dict with success status and execution details
        """
        completed_subtasks = set()
        failed = False
        
        # Build dependency graph
        remaining_subtasks = set(st.id for st in self.current_plan)
        
        while remaining_subtasks and not failed:
            # Find subtasks ready to execute (dependencies met)
            ready_subtasks = [
                st for st in self.current_plan
                if st.id in remaining_subtasks
                and all(dep in completed_subtasks for dep in st.dependencies)
            ]
            
            if not ready_subtasks:
                logger.error("Circular dependency or unmet dependencies detected")
                failed = True
                break
            
            # Execute ready subtasks
            if self.parallel_execution and len(ready_subtasks) > 1:
                # Parallel execution
                results = await asyncio.gather(
                    *[self._execute_subtask(st, executor, context) for st in ready_subtasks],
                    return_exceptions=True,
                )
                
                for st, result in zip(ready_subtasks, results):
                    if isinstance(result, Exception):
                        st.status = SubtaskStatus.FAILED
                        st.error = str(result)
                        failed = True
                    elif result:
                        completed_subtasks.add(st.id)
                        remaining_subtasks.remove(st.id)
                    else:
                        failed = True
            else:
                # Sequential execution
                for st in ready_subtasks:
                    success = await self._execute_subtask(st, executor, context)
                    if success:
                        completed_subtasks.add(st.id)
                        remaining_subtasks.remove(st.id)
                    else:
                        failed = True
                        break
        
        return {
            "success": not failed and len(remaining_subtasks) == 0,
            "completed": len(completed_subtasks),
            "remaining": len(remaining_subtasks),
        }
    
    async def _execute_subtask(
        self,
        subtask: Subtask,
        executor: Callable,
        context: Dict[str, Any],
    ) -> bool:
        """
        Execute a single subtask.
        
        Returns:
            True if successful, False otherwise
        """
        subtask.status = SubtaskStatus.IN_PROGRESS
        subtask.start_time = datetime.utcnow()
        
        logger.info(f"Executing subtask: {subtask.id} - {subtask.description}")
        
        try:
            result = await executor(subtask, context)
            subtask.result = result
            subtask.status = SubtaskStatus.COMPLETED
            subtask.end_time = datetime.utcnow()
            
            logger.info(f"Subtask {subtask.id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Subtask {subtask.id} failed: {e}", exc_info=True)
            subtask.status = SubtaskStatus.FAILED
            subtask.error = str(e)
            subtask.end_time = datetime.utcnow()
            return False
    
    async def _replan(
        self,
        task: str,
        context: Dict[str, Any],
        failed_subtasks: List[Subtask],
        available_tools: List[str],
    ) -> List[Subtask]:
        """
        Generate new plan considering previous failures.
        
        Returns:
            New list of Subtask objects
        """
        failure_info = "\n".join([
            f"- {st.id}: {st.description} (Error: {st.error})"
            for st in failed_subtasks
        ])
        
        replanning_prompt = f"""The previous plan failed. Generate a new plan that addresses the failures.

Original Task: {task}

Failed Subtasks:
{failure_info}

Context:
{self._format_context(context)}

Available Tools: {', '.join(available_tools) if available_tools else 'None'}

Generate an improved plan that:
1. Avoids the previous failures
2. Uses alternative approaches
3. Breaks down complex subtasks further if needed

Respond in the same JSON format as before."""
        
        try:
            response = await self.llm_manager.generate(
                prompt=replanning_prompt,
                temperature=0.7,  # Higher temperature for creative alternatives
            )
            
            import json
            plan_data = json.loads(response)
            
            subtasks = []
            for st_data in plan_data.get("subtasks", [])[:self.max_subtasks]:
                subtask = Subtask(
                    id=st_data.get("id", f"subtask_{len(subtasks) + 1}"),
                    description=st_data.get("description", ""),
                    dependencies=st_data.get("dependencies", []),
                    estimated_complexity=st_data.get("estimated_complexity", 0.5),
                    required_tools=st_data.get("required_tools", []),
                )
                subtasks.append(subtask)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error in replanning: {e}", exc_info=True)
            # Return original plan if replanning fails
            return self.current_plan
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompts."""
        parts = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                import json
                parts.append(f"{key}: {json.dumps(value, indent=2)}")
        return "\n".join(parts)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current execution progress."""
        if not self.current_plan:
            return {"status": "no_plan"}
        
        total = len(self.current_plan)
        completed = len([st for st in self.current_plan if st.status == SubtaskStatus.COMPLETED])
        failed = len([st for st in self.current_plan if st.status == SubtaskStatus.FAILED])
        in_progress = len([st for st in self.current_plan if st.status == SubtaskStatus.IN_PROGRESS])
        
        return {
            "total_subtasks": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
        }
