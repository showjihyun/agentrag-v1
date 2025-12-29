"""
Agent Builder Facade

Provides a unified interface to the DDD-based agent builder services.
This facade maintains backward compatibility with existing code while
using the new domain-driven architecture internally.

Supports both:
- Application Services (simple API)
- CQRS Commands/Queries (explicit read/write separation)
"""

from typing import Optional, Dict, Any, List, AsyncGenerator
from sqlalchemy.orm import Session

from .application import (
    WorkflowApplicationService,
    AgentApplicationService,
    ExecutionApplicationService,
    # CQRS
    WorkflowCommandHandler,
    WorkflowQueryHandler,
    AgentCommandHandler,
    AgentQueryHandler,
    ExecutionQueryHandler,
    CreateWorkflowCommand,
    CreateAgentCommand,
    ExecuteWorkflowCommand,
)
from .infrastructure import (
    UnifiedExecutor,
    WorkflowRepositoryImpl,
    AgentRepositoryImpl,
    ExecutionRepositoryImpl,
    get_executor,
)
from backend.services.agent_builder.block_service import BlockService


class AgentBuilderFacade:
    """
    Unified facade for agent builder operations.
    
    Usage:
        facade = AgentBuilderFacade(db)
        
        # Workflow operations
        workflow = facade.create_workflow(user_id, name, nodes, edges)
        result = await facade.execute_workflow(workflow_id, input_data, user_id)
        
        # Agent operations
        agent = facade.create_agent(user_id, name, agent_type)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._workflow_service: Optional[WorkflowApplicationService] = None
        self._agent_service: Optional[AgentApplicationService] = None
        self._execution_service: Optional[ExecutionApplicationService] = None
        self._block_service: Optional[BlockService] = None
    
    @property
    def workflows(self) -> WorkflowApplicationService:
        """Get workflow application service."""
        if self._workflow_service is None:
            self._workflow_service = WorkflowApplicationService(self.db)
        return self._workflow_service
    
    @property
    def agents(self) -> AgentApplicationService:
        """Get agent application service."""
        if self._agent_service is None:
            self._agent_service = AgentApplicationService(self.db)
        return self._agent_service
    
    @property
    def executions(self) -> ExecutionApplicationService:
        """Get execution application service."""
        if self._execution_service is None:
            self._execution_service = ExecutionApplicationService(self.db)
        return self._execution_service
    
    @property
    def blocks(self) -> BlockService:
        """Get block service."""
        if self._block_service is None:
            self._block_service = BlockService(self.db)
        return self._block_service
    
    # ========================================================================
    # WORKFLOW SHORTCUTS
    # ========================================================================
    
    def create_workflow(
        self,
        user_id: str,
        name: str,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        """Create a new workflow."""
        return self.workflows.create_workflow(
            user_id=user_id,
            name=name,
            nodes=nodes,
            edges=edges,
            description=description,
            **kwargs,
        )
    
    def get_workflow(self, workflow_id: str):
        """Get workflow by ID."""
        return self.workflows.get_workflow(workflow_id)
    
    def update_workflow(
        self,
        workflow_id: str,
        user_id: str,
        name: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        """Update an existing workflow."""
        return self.workflows.update_workflow(
            workflow_id=workflow_id,
            user_id=user_id,
            name=name,
            nodes=nodes,
            edges=edges,
            description=description,
            **kwargs,
        )
    
    def delete_workflow(self, workflow_id: str, user_id: str, hard: bool = False):
        """Delete a workflow."""
        return self.workflows.delete_workflow(workflow_id, user_id, hard)
    
    def list_workflows(
        self,
        user_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        **kwargs,
    ):
        """List workflows with filtering."""
        return self.workflows.list_workflows(
            user_id=user_id,
            offset=offset,
            limit=limit,
            **kwargs,
        )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        **kwargs,
    ):
        """Execute a workflow."""
        return await self.workflows.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=user_id,
            **kwargs,
        )
    
    async def execute_workflow_streaming(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with streaming updates."""
        async for update in self.workflows.execute_workflow_streaming(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=user_id,
        ):
            yield update
    
    # ========================================================================
    # AGENT SHORTCUTS
    # ========================================================================
    
    def create_agent(
        self,
        user_id: str,
        name: str,
        agent_type: str = "assistant",
        **kwargs,
    ):
        """Create a new agent."""
        return self.agents.create_agent(
            user_id=user_id,
            name=name,
            agent_type=agent_type,
            **kwargs,
        )
    
    def get_agent(self, agent_id: str):
        """Get agent by ID."""
        return self.agents.get_agent(agent_id)
    
    # ========================================================================
    # BLOCK SHORTCUTS
    # ========================================================================
    
    def create_block(self, user_id: str, block_data):
        """Create a new block."""
        return self.blocks.create_block(user_id, block_data)
    
    def get_block(self, block_id: str):
        """Get block by ID."""
        return self.blocks.get_block(block_id)
    
    def update_block(self, block_id: str, block_data):
        """Update a block."""
        return self.blocks.update_block(block_id, block_data)
    
    def delete_block(self, block_id: str):
        """Delete a block."""
        return self.blocks.delete_block(block_id)
    
    def list_blocks(self, **kwargs):
        """List blocks with filtering."""
        return self.blocks.list_blocks(**kwargs)
    
    async def test_block(self, block_id: str, test_input, user_id: str, save_execution: bool = True):
        """Test a block."""
        return await self.blocks.test_block(block_id, test_input, user_id, save_execution)
    
    def get_block_versions(self, block_id: str):
        """Get block version history."""
        return self.blocks.get_block_versions(block_id)
    
    # ========================================================================
    # EXECUTION SHORTCUTS
    # ========================================================================
    
    def get_execution(self, execution_id: str):
        """Get execution by ID."""
        return self.executions.get_execution(execution_id)
    
    def get_execution_stats(self, workflow_id: Optional[str] = None, **kwargs):
        """Get execution statistics."""
        return self.executions.get_execution_stats(workflow_id=workflow_id, **kwargs)
    
    # ========================================================================
    # CQRS HANDLERS
    # ========================================================================
    
    @property
    def workflow_commands(self) -> WorkflowCommandHandler:
        """Get workflow command handler."""
        return WorkflowCommandHandler(self.db)
    
    @property
    def workflow_queries(self) -> WorkflowQueryHandler:
        """Get workflow query handler."""
        return WorkflowQueryHandler(self.db)
    
    @property
    def agent_commands(self) -> AgentCommandHandler:
        """Get agent command handler."""
        return AgentCommandHandler(self.db)
    
    @property
    def agent_queries(self) -> AgentQueryHandler:
        """Get agent query handler."""
        return AgentQueryHandler(self.db)
    
    @property
    def execution_queries(self) -> ExecutionQueryHandler:
        """Get execution query handler."""
        return ExecutionQueryHandler(self.db)
    
    # ========================================================================
    # LEGACY EXECUTOR ADAPTER
    # ========================================================================
    
    def get_legacy_executor(self, use_unified: bool = True):
        """
        Get executor adapter for backward compatibility.
        
        Args:
            use_unified: Use new UnifiedExecutor (True) or legacy (False)
        """
        return get_executor(self.db, use_unified=use_unified)


# Backward compatibility aliases
def get_facade(db: Session) -> AgentBuilderFacade:
    """Get an AgentBuilderFacade instance."""
    return AgentBuilderFacade(db)
