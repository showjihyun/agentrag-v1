"""
Agent Team Orchestrator - Multi-Agent Collaboration System
Supports sequential, parallel, and hierarchical execution modes
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Predefined agent roles."""
    RESEARCHER = "researcher"
    WRITER = "writer"
    EDITOR = "editor"
    ANALYST = "analyst"
    CODER = "coder"
    REVIEWER = "reviewer"
    MANAGER = "manager"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_DELEGATION = "waiting_delegation"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    """Team execution mode."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


@dataclass
class AgentConfig:
    """Agent configuration with role, goal, and backstory."""
    
    id: str
    name: str
    role: AgentRole
    goal: str
    backstory: str
    tools: List[str] = field(default_factory=list)
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_iterations: int = 10
    allow_delegation: bool = False
    delegate_to: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    verbose: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "goal": self.goal,
            "backstory": self.backstory,
            "tools": self.tools,
            "llm_model": self.llm_model,
            "temperature": self.temperature,
            "max_iterations": self.max_iterations,
            "allow_delegation": self.allow_delegation,
            "delegate_to": self.delegate_to,
            "memory_enabled": self.memory_enabled,
            "verbose": self.verbose,
        }


@dataclass
class TaskConfig:
    """Task configuration for agent execution."""
    
    id: str
    description: str
    agent_id: str
    expected_output: str
    context_from: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    async_execution: bool = False
    human_input: bool = False
    output_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "agent_id": self.agent_id,
            "expected_output": self.expected_output,
            "context_from": self.context_from,
            "tools": self.tools,
            "async_execution": self.async_execution,
            "human_input": self.human_input,
            "output_file": self.output_file,
        }


@dataclass
class TaskResult:
    """Result of a task execution."""
    
    task_id: str
    agent_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tokens_used: int = 0
    delegated_to: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


@dataclass
class AgentTeamConfig:
    """Agent Team configuration for multi-agent orchestration."""
    
    id: str
    name: str
    description: str
    agents: List[AgentConfig]
    tasks: List[TaskConfig]
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    manager_agent_id: Optional[str] = None
    verbose: bool = False
    memory_enabled: bool = True
    max_rpm: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": [a.to_dict() for a in self.agents],
            "tasks": [t.to_dict() for t in self.tasks],
            "execution_mode": self.execution_mode.value,
            "manager_agent_id": self.manager_agent_id,
            "verbose": self.verbose,
            "memory_enabled": self.memory_enabled,
            "max_rpm": self.max_rpm,
        }


class AgentTeamOrchestrator:
    """
    Orchestrates multi-agent collaboration.
    Supports sequential, parallel, and hierarchical execution modes.
    """
    
    def __init__(self, team_config: AgentTeamConfig):
        self.config = team_config
        self.agents: Dict[str, AgentConfig] = {a.id: a for a in team_config.agents}
        self.tasks: Dict[str, TaskConfig] = {t.id: t for t in team_config.tasks}
        self.results: Dict[str, TaskResult] = {}
        self.execution_context: Dict[str, Any] = {}
        self._callbacks: List[callable] = []
        
    def add_callback(self, callback: callable):
        """Add execution callback for real-time updates."""
        self._callbacks.append(callback)
        
    async def _notify(self, event: str, data: Dict[str, Any]):
        """Notify all callbacks of an event."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event, data)
                else:
                    callback(event, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def execute(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent team with all tasks.
        
        Args:
            inputs: Initial inputs for the team
            
        Returns:
            Execution results with all task outputs
        """
        inputs = inputs or {}
        self.execution_context = {"inputs": inputs, "task_outputs": {}}
        
        await self._notify("team_started", {
            "team_id": self.config.id,
            "team_name": self.config.name,
            "mode": self.config.execution_mode.value,
            "task_count": len(self.tasks),
        })
        
        try:
            if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential()
            elif self.config.execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel()
            elif self.config.execution_mode == ExecutionMode.HIERARCHICAL:
                results = await self._execute_hierarchical()
            else:
                raise ValueError(f"Unknown execution mode: {self.config.execution_mode}")
            
            await self._notify("team_completed", {
                "team_id": self.config.id,
                "success": True,
                "results": {k: v.output for k, v in results.items()},
            })
            
            return {
                "success": True,
                "results": {k: v.output for k, v in results.items()},
                "task_results": [r.to_dict() if hasattr(r, 'to_dict') else vars(r) for r in results.values()],
            }
            
        except Exception as e:
            logger.error(f"Agent team execution failed: {e}", exc_info=True)
            await self._notify("team_failed", {
                "team_id": self.config.id,
                "error": str(e),
            })
            return {
                "success": False,
                "error": str(e),
                "results": {},
            }
    
    async def _execute_sequential(self) -> Dict[str, TaskResult]:
        """Execute tasks sequentially."""
        task_order = self._get_task_order()
        
        for task_id in task_order:
            task = self.tasks[task_id]
            result = await self._execute_task(task)
            self.results[task_id] = result
            self.execution_context["task_outputs"][task_id] = result.output
            
            if result.status == TaskStatus.FAILED:
                logger.warning(f"Task {task_id} failed, stopping sequential execution")
                break
                
        return self.results
    
    async def _execute_parallel(self) -> Dict[str, TaskResult]:
        """Execute independent tasks in parallel."""
        independent_tasks = []
        dependent_tasks = []
        
        for task in self.config.tasks:
            if not task.context_from:
                independent_tasks.append(task)
            else:
                dependent_tasks.append(task)
        
        if independent_tasks:
            parallel_results = await asyncio.gather(
                *[self._execute_task(task) for task in independent_tasks],
                return_exceptions=True
            )
            
            for task, result in zip(independent_tasks, parallel_results):
                if isinstance(result, Exception):
                    result = TaskResult(
                        task_id=task.id,
                        agent_id=task.agent_id,
                        status=TaskStatus.FAILED,
                        error=str(result),
                    )
                self.results[task.id] = result
                self.execution_context["task_outputs"][task.id] = result.output
        
        for task in dependent_tasks:
            result = await self._execute_task(task)
            self.results[task.id] = result
            self.execution_context["task_outputs"][task.id] = result.output
            
        return self.results
    
    async def _execute_hierarchical(self) -> Dict[str, TaskResult]:
        """Execute tasks with manager agent coordination."""
        if not self.config.manager_agent_id:
            raise ValueError("Hierarchical mode requires a manager agent")
        
        manager = self.agents.get(self.config.manager_agent_id)
        if not manager:
            raise ValueError(f"Manager agent {self.config.manager_agent_id} not found")
        
        task_plan = await self._get_manager_plan(manager)
        
        for task_assignment in task_plan:
            task_id = task_assignment["task_id"]
            assigned_agent_id = task_assignment.get("agent_id")
            
            task = self.tasks[task_id]
            
            if assigned_agent_id and assigned_agent_id != task.agent_id:
                original_agent = task.agent_id
                task.agent_id = assigned_agent_id
                logger.info(f"Manager delegated task {task_id} from {original_agent} to {assigned_agent_id}")
            
            result = await self._execute_task(task)
            self.results[task_id] = result
            self.execution_context["task_outputs"][task_id] = result.output
            
        return self.results
    
    async def _execute_task(self, task: TaskConfig) -> TaskResult:
        """Execute a single task with an agent."""
        agent = self.agents.get(task.agent_id)
        if not agent:
            return TaskResult(
                task_id=task.id,
                agent_id=task.agent_id,
                status=TaskStatus.FAILED,
                error=f"Agent {task.agent_id} not found",
            )
        
        await self._notify("task_started", {
            "task_id": task.id,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "description": task.description,
        })
        
        result = TaskResult(
            task_id=task.id,
            agent_id=agent.id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        
        try:
            context = self._build_task_context(task)
            
            if task.human_input:
                result.status = TaskStatus.WAITING_DELEGATION
                await self._notify("task_waiting_human", {
                    "task_id": task.id,
                    "context": context,
                })
            
            output = await self._run_agent(agent, task, context)
            
            result.output = output
            result.status = TaskStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            await self._notify("task_completed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "output": output,
                "duration_ms": result.duration_ms,
            })
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            
            if agent.allow_delegation and agent.delegate_to:
                delegated_result = await self._try_delegation(task, agent, str(e))
                if delegated_result:
                    return delegated_result
            
            await self._notify("task_failed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "error": str(e),
            })
        
        return result
    
    async def _run_agent(
        self, 
        agent: AgentConfig, 
        task: TaskConfig, 
        context: Dict[str, Any]
    ) -> Any:
        """Run an agent on a task."""
        system_prompt = self._build_agent_prompt(agent)
        
        task_prompt = f"""
Task: {task.description}

Expected Output: {task.expected_output}

Context:
{self._format_context(context)}

Please complete this task according to your role and goal.
"""
        
        from backend.services.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        response = await llm_manager.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_prompt},
            ],
            model=agent.llm_model,
            temperature=agent.temperature,
        )
        
        return response.get("content", response)
    
    def _build_agent_prompt(self, agent: AgentConfig) -> str:
        """Build system prompt for an agent."""
        return f"""You are {agent.name}, a {agent.role.value}.

Role: {agent.role.value}
Goal: {agent.goal}

Backstory:
{agent.backstory}

You have access to the following tools: {', '.join(agent.tools) if agent.tools else 'None'}

Guidelines:
- Stay in character and act according to your role
- Focus on achieving your goal
- Provide detailed, actionable outputs
- If you cannot complete a task, explain why clearly
"""
    
    def _build_task_context(self, task: TaskConfig) -> Dict[str, Any]:
        """Build context from previous task outputs."""
        context = {
            "inputs": self.execution_context.get("inputs", {}),
            "previous_outputs": {},
        }
        
        for context_task_id in task.context_from:
            if context_task_id in self.execution_context.get("task_outputs", {}):
                context["previous_outputs"][context_task_id] = \
                    self.execution_context["task_outputs"][context_task_id]
        
        return context
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt."""
        parts = []
        
        if context.get("inputs"):
            parts.append(f"Inputs: {context['inputs']}")
        
        if context.get("previous_outputs"):
            parts.append("Previous Task Outputs:")
            for task_id, output in context["previous_outputs"].items():
                parts.append(f"  - {task_id}: {output}")
        
        return "\n".join(parts) if parts else "No additional context"
    
    async def _try_delegation(
        self, 
        task: TaskConfig, 
        original_agent: AgentConfig,
        error: str
    ) -> Optional[TaskResult]:
        """Try to delegate a failed task to another agent."""
        for delegate_id in original_agent.delegate_to:
            delegate = self.agents.get(delegate_id)
            if not delegate:
                continue
            
            logger.info(f"Delegating task {task.id} from {original_agent.id} to {delegate_id}")
            
            await self._notify("task_delegated", {
                "task_id": task.id,
                "from_agent": original_agent.id,
                "to_agent": delegate_id,
                "reason": error,
            })
            
            delegated_task = TaskConfig(
                id=task.id,
                description=task.description,
                agent_id=delegate_id,
                expected_output=task.expected_output,
                context_from=task.context_from,
                tools=task.tools,
            )
            
            result = await self._execute_task(delegated_task)
            result.delegated_to = delegate_id
            
            if result.status == TaskStatus.COMPLETED:
                return result
        
        return None
    
    async def _get_manager_plan(self, manager: AgentConfig) -> List[Dict[str, Any]]:
        """Get task execution plan from manager agent."""
        return [{"task_id": t.id, "agent_id": t.agent_id} for t in self.config.tasks]
    
    def _get_task_order(self) -> List[str]:
        """Get topologically sorted task order based on dependencies."""
        visited = set()
        order = []
        
        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.context_from:
                    visit(dep_id)
                order.append(task_id)
        
        for task_id in self.tasks:
            visit(task_id)
        
        return order


# Predefined agent templates
AGENT_TEMPLATES = {
    "researcher": AgentConfig(
        id="researcher",
        name="Research Specialist",
        role=AgentRole.RESEARCHER,
        goal="Find comprehensive and accurate information on any topic",
        backstory="You are an expert researcher with years of experience in gathering and synthesizing information from various sources.",
        tools=["web_search", "wikipedia_search", "arxiv_search"],
        allow_delegation=True,
        delegate_to=["analyst"],
    ),
    "writer": AgentConfig(
        id="writer",
        name="Content Writer",
        role=AgentRole.WRITER,
        goal="Create engaging, well-structured content",
        backstory="You are a skilled writer with expertise in creating compelling content for different audiences.",
        tools=[],
        allow_delegation=True,
        delegate_to=["editor"],
    ),
    "editor": AgentConfig(
        id="editor",
        name="Content Editor",
        role=AgentRole.EDITOR,
        goal="Refine and improve content for clarity and impact",
        backstory="You are a meticulous editor with a keen eye for detail.",
        tools=[],
    ),
    "analyst": AgentConfig(
        id="analyst",
        name="Data Analyst",
        role=AgentRole.ANALYST,
        goal="Analyze data and provide actionable insights",
        backstory="You are an experienced data analyst who can interpret complex data sets.",
        tools=["calculator", "python_code"],
    ),
    "coder": AgentConfig(
        id="coder",
        name="Software Developer",
        role=AgentRole.CODER,
        goal="Write clean, efficient, and well-documented code",
        backstory="You are a skilled software developer with expertise in multiple programming languages.",
        tools=["python_code", "javascript_code"],
        allow_delegation=True,
        delegate_to=["reviewer"],
    ),
    "reviewer": AgentConfig(
        id="reviewer",
        name="Code Reviewer",
        role=AgentRole.REVIEWER,
        goal="Review code for quality, security, and best practices",
        backstory="You are an experienced code reviewer who ensures code quality and security.",
        tools=["python_code"],
    ),
}


def create_team_from_template(
    template_name: str,
    tasks: List[Dict[str, Any]],
    **kwargs
) -> AgentTeamConfig:
    """Create an agent team from a predefined template."""
    templates = {
        "research_team": {
            "agents": ["researcher", "analyst", "writer"],
            "mode": ExecutionMode.SEQUENTIAL,
        },
        "content_team": {
            "agents": ["researcher", "writer", "editor"],
            "mode": ExecutionMode.SEQUENTIAL,
        },
        "dev_team": {
            "agents": ["coder", "reviewer"],
            "mode": ExecutionMode.SEQUENTIAL,
        },
    }
    
    template = templates.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")
    
    agents = [AGENT_TEMPLATES[a] for a in template["agents"]]
    
    task_configs = []
    for i, task_data in enumerate(tasks):
        task_configs.append(TaskConfig(
            id=task_data.get("id", f"task_{i}"),
            description=task_data["description"],
            agent_id=task_data.get("agent_id", agents[i % len(agents)].id),
            expected_output=task_data.get("expected_output", "Completed task output"),
            context_from=task_data.get("context_from", []),
        ))
    
    return AgentTeamConfig(
        id=str(uuid.uuid4()),
        name=kwargs.get("name", f"{template_name}_team"),
        description=kwargs.get("description", f"Team based on {template_name} template"),
        agents=agents,
        tasks=task_configs,
        execution_mode=template["mode"],
        **{k: v for k, v in kwargs.items() if k not in ["name", "description"]},
    )
