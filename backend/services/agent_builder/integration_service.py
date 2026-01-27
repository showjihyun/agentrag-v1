"""
Agent-Workflow Integration Service

Provides integration between Agents and Workflows/Agentflows.
Supports both direct agent execution in agentflows and agent-to-block conversion.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models.agent_builder import Agent, AgentTool, Tool
from backend.db.models.flows import (
    Agentflow,
    AgentflowAgent,
    AgentflowEdge,
    FlowExecution,
)
from backend.db.models.agent_builder import Block, Workflow, WorkflowNode, WorkflowEdge
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class AgentWorkflowIntegrationService:
    """
    Service for integrating Agents with Workflows and Agentflows.
    
    Supports:
    - Adding agents to agentflows
    - Converting agents to blocks
    - Managing agent execution in workflows
    - Data mapping between agents
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # OPTION 1: Direct Agent Integration with Agentflows
    # ========================================================================
    
    def add_agent_to_agentflow(
        self,
        agentflow_id: str,
        agent_id: str,
        role: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        priority: int = 1,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        dependencies: Optional[List[str]] = None,
        input_mapping: Optional[Dict[str, Any]] = None,
        output_mapping: Optional[Dict[str, Any]] = None,
        conditional_logic: Optional[Dict[str, Any]] = None,
        parallel_group: Optional[str] = None,
        position_x: float = 0,
        position_y: float = 0,
    ) -> AgentflowAgent:
        """
        Add an agent to an agentflow.
        
        Args:
            agentflow_id: ID of the agentflow
            agent_id: ID of the agent to add
            role: Role of the agent in the flow (e.g., 'researcher', 'writer', 'reviewer')
            name: Display name (defaults to agent name)
            description: Description of agent's role in this flow
            capabilities: List of capabilities this agent provides
            priority: Execution priority (lower = earlier)
            max_retries: Maximum retry attempts
            timeout_seconds: Timeout for agent execution
            dependencies: List of agent IDs this depends on
            input_mapping: How to map inputs from previous agents
            output_mapping: How to map outputs to next agents
            conditional_logic: Conditions for execution
            parallel_group: Group ID for parallel execution
            position_x: X position in visual editor
            position_y: Y position in visual editor
            
        Returns:
            Created AgentflowAgent instance
        """
        # Validate agentflow exists
        agentflow = self.db.query(Agentflow).filter(
            Agentflow.id == uuid.UUID(agentflow_id)
        ).first()
        if not agentflow:
            raise NotFoundError("Agentflow", agentflow_id)
        
        # Validate agent exists
        agent = self.db.query(Agent).filter(
            Agent.id == uuid.UUID(agent_id)
        ).first()
        if not agent:
            raise NotFoundError("Agent", agent_id)
        
        # Check if agent already in agentflow
        existing = self.db.query(AgentflowAgent).filter(
            and_(
                AgentflowAgent.agentflow_id == uuid.UUID(agentflow_id),
                AgentflowAgent.agent_id == uuid.UUID(agent_id)
            )
        ).first()
        if existing:
            raise ValidationError(f"Agent {agent_id} already in agentflow {agentflow_id}")
        
        # Extract capabilities from agent's tools if not provided
        if capabilities is None:
            capabilities = []
            agent_tools = self.db.query(AgentTool).filter(
                AgentTool.agent_id == agent.id
            ).all()
            for at in agent_tools:
                tool = self.db.query(Tool).filter(Tool.id == at.tool_id).first()
                if tool:
                    capabilities.append(tool.name)
        
        # Create AgentflowAgent
        agentflow_agent = AgentflowAgent(
            agentflow_id=uuid.UUID(agentflow_id),
            agent_id=uuid.UUID(agent_id),
            name=name or agent.name,
            role=role,
            description=description or agent.description,
            capabilities=capabilities,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            dependencies=dependencies or [],
            input_mapping=input_mapping or {},
            output_mapping=output_mapping or {},
            conditional_logic=conditional_logic or {},
            parallel_group=parallel_group,
            position_x=position_x,
            position_y=position_y,
        )
        
        self.db.add(agentflow_agent)
        self.db.flush()
        
        logger.info(f"Added agent {agent_id} to agentflow {agentflow_id} with role {role}")
        
        return agentflow_agent
    
    def remove_agent_from_agentflow(
        self,
        agentflow_id: str,
        agentflow_agent_id: str,
    ) -> None:
        """
        Remove an agent from an agentflow.
        
        Args:
            agentflow_id: ID of the agentflow
            agentflow_agent_id: ID of the AgentflowAgent to remove
        """
        agentflow_agent = self.db.query(AgentflowAgent).filter(
            and_(
                AgentflowAgent.id == uuid.UUID(agentflow_agent_id),
                AgentflowAgent.agentflow_id == uuid.UUID(agentflow_id)
            )
        ).first()
        
        if not agentflow_agent:
            raise NotFoundError(f"AgentflowAgent {agentflow_agent_id} not found in agentflow {agentflow_id}")
        
        # Remove edges connected to this agent
        self.db.query(AgentflowEdge).filter(
            (AgentflowEdge.source_agent_id == agentflow_agent.id) |
            (AgentflowEdge.target_agent_id == agentflow_agent.id)
        ).delete()
        
        # Remove the agent
        self.db.delete(agentflow_agent)
        self.db.flush()
        
        logger.info(f"Removed agent {agentflow_agent_id} from agentflow {agentflow_id}")
    
    def update_agentflow_agent(
        self,
        agentflow_id: str,
        agentflow_agent_id: str,
        **updates,
    ) -> AgentflowAgent:
        """
        Update an agent's configuration in an agentflow.
        
        Args:
            agentflow_id: ID of the agentflow
            agentflow_agent_id: ID of the AgentflowAgent to update
            **updates: Fields to update
            
        Returns:
            Updated AgentflowAgent instance
        """
        agentflow_agent = self.db.query(AgentflowAgent).filter(
            and_(
                AgentflowAgent.id == uuid.UUID(agentflow_agent_id),
                AgentflowAgent.agentflow_id == uuid.UUID(agentflow_id)
            )
        ).first()
        
        if not agentflow_agent:
            raise NotFoundError(f"AgentflowAgent {agentflow_agent_id} not found")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(agentflow_agent, key) and value is not None:
                setattr(agentflow_agent, key, value)
        
        self.db.flush()
        
        logger.info(f"Updated agentflow agent {agentflow_agent_id}")
        
        return agentflow_agent
    
    def add_edge_between_agents(
        self,
        agentflow_id: str,
        source_agent_id: str,
        target_agent_id: str,
        edge_type: str = "data_flow",
        condition: Optional[Dict[str, Any]] = None,
        data_mapping: Optional[Dict[str, Any]] = None,
        label: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
    ) -> AgentflowEdge:
        """
        Add an edge between two agents in an agentflow.
        
        Args:
            agentflow_id: ID of the agentflow
            source_agent_id: ID of source AgentflowAgent
            target_agent_id: ID of target AgentflowAgent
            edge_type: Type of edge (data_flow, control_flow, conditional)
            condition: Condition for edge activation
            data_mapping: How to map data between agents
            label: Edge label
            style: Visual styling
            
        Returns:
            Created AgentflowEdge instance
        """
        # Validate agents exist
        source = self.db.query(AgentflowAgent).filter(
            AgentflowAgent.id == uuid.UUID(source_agent_id)
        ).first()
        target = self.db.query(AgentflowAgent).filter(
            AgentflowAgent.id == uuid.UUID(target_agent_id)
        ).first()
        
        if not source or not target:
            raise NotFoundError("Source or target agent not found")
        
        # Check if edge already exists
        existing = self.db.query(AgentflowEdge).filter(
            and_(
                AgentflowEdge.source_agent_id == uuid.UUID(source_agent_id),
                AgentflowEdge.target_agent_id == uuid.UUID(target_agent_id)
            )
        ).first()
        if existing:
            raise ValidationError("Edge already exists between these agents")
        
        # Create edge
        edge = AgentflowEdge(
            agentflow_id=uuid.UUID(agentflow_id),
            source_agent_id=uuid.UUID(source_agent_id),
            target_agent_id=uuid.UUID(target_agent_id),
            edge_type=edge_type,
            condition=condition or {},
            data_mapping=data_mapping or {},
            label=label,
            style=style or {},
        )
        
        self.db.add(edge)
        self.db.flush()
        
        logger.info(f"Added edge from {source_agent_id} to {target_agent_id}")
        
        return edge
    
    def get_agentflow_execution_plan(
        self,
        agentflow_id: str,
    ) -> Dict[str, Any]:
        """
        Generate an execution plan for an agentflow based on its orchestration type.
        
        Args:
            agentflow_id: ID of the agentflow
            
        Returns:
            Execution plan with agent order and dependencies
        """
        agentflow = self.db.query(Agentflow).filter(
            Agentflow.id == uuid.UUID(agentflow_id)
        ).first()
        if not agentflow:
            raise NotFoundError(f"Agentflow {agentflow_id} not found")
        
        agents = self.db.query(AgentflowAgent).filter(
            AgentflowAgent.agentflow_id == uuid.UUID(agentflow_id)
        ).order_by(AgentflowAgent.priority).all()
        
        edges = self.db.query(AgentflowEdge).filter(
            AgentflowEdge.agentflow_id == uuid.UUID(agentflow_id)
        ).all()
        
        orchestration_type = agentflow.orchestration_type
        
        # Build execution plan based on orchestration type
        if orchestration_type == "sequential":
            return self._build_sequential_plan(agents, edges)
        elif orchestration_type == "parallel":
            return self._build_parallel_plan(agents, edges)
        elif orchestration_type == "hierarchical":
            return self._build_hierarchical_plan(agents, edges, agentflow.supervisor_config)
        elif orchestration_type == "adaptive":
            return self._build_adaptive_plan(agents, edges)
        else:
            # Default to sequential for advanced types
            return self._build_sequential_plan(agents, edges)
    
    def _build_sequential_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge],
    ) -> Dict[str, Any]:
        """Build sequential execution plan."""
        return {
            "type": "sequential",
            "stages": [
                {
                    "stage": idx,
                    "agents": [
                        {
                            "id": str(agent.id),
                            "agent_id": str(agent.agent_id),
                            "name": agent.name,
                            "role": agent.role,
                            "priority": agent.priority,
                        }
                    ],
                }
                for idx, agent in enumerate(agents)
            ],
            "edges": [
                {
                    "source": str(edge.source_agent_id),
                    "target": str(edge.target_agent_id),
                    "type": edge.edge_type,
                    "data_mapping": edge.data_mapping,
                }
                for edge in edges
            ],
        }
    
    def _build_parallel_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge],
    ) -> Dict[str, Any]:
        """Build parallel execution plan."""
        # Group agents by parallel_group
        groups: Dict[str, List[AgentflowAgent]] = {}
        for agent in agents:
            group = agent.parallel_group or "default"
            if group not in groups:
                groups[group] = []
            groups[group].append(agent)
        
        return {
            "type": "parallel",
            "groups": [
                {
                    "group": group_name,
                    "agents": [
                        {
                            "id": str(agent.id),
                            "agent_id": str(agent.agent_id),
                            "name": agent.name,
                            "role": agent.role,
                        }
                        for agent in group_agents
                    ],
                }
                for group_name, group_agents in groups.items()
            ],
            "edges": [
                {
                    "source": str(edge.source_agent_id),
                    "target": str(edge.target_agent_id),
                    "type": edge.edge_type,
                    "data_mapping": edge.data_mapping,
                }
                for edge in edges
            ],
        }
    
    def _build_hierarchical_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge],
        supervisor_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build hierarchical execution plan with manager/worker roles."""
        managers = [a for a in agents if a.role == "manager"]
        workers = [a for a in agents if a.role != "manager"]
        
        return {
            "type": "hierarchical",
            "supervisor": supervisor_config,
            "managers": [
                {
                    "id": str(agent.id),
                    "agent_id": str(agent.agent_id),
                    "name": agent.name,
                    "role": agent.role,
                }
                for agent in managers
            ],
            "workers": [
                {
                    "id": str(agent.id),
                    "agent_id": str(agent.agent_id),
                    "name": agent.name,
                    "role": agent.role,
                    "capabilities": agent.capabilities,
                }
                for agent in workers
            ],
            "edges": [
                {
                    "source": str(edge.source_agent_id),
                    "target": str(edge.target_agent_id),
                    "type": edge.edge_type,
                    "data_mapping": edge.data_mapping,
                }
                for edge in edges
            ],
        }
    
    def _build_adaptive_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge],
    ) -> Dict[str, Any]:
        """Build adaptive execution plan with conditional routing."""
        return {
            "type": "adaptive",
            "agents": [
                {
                    "id": str(agent.id),
                    "agent_id": str(agent.agent_id),
                    "name": agent.name,
                    "role": agent.role,
                    "capabilities": agent.capabilities,
                    "conditional_logic": agent.conditional_logic,
                }
                for agent in agents
            ],
            "edges": [
                {
                    "source": str(edge.source_agent_id),
                    "target": str(edge.target_agent_id),
                    "type": edge.edge_type,
                    "condition": edge.condition,
                    "data_mapping": edge.data_mapping,
                }
                for edge in edges
            ],
        }
    
    # ========================================================================
    # OPTION 2: Agent to Block Conversion
    # ========================================================================
    
    def convert_agent_to_block(
        self,
        agent_id: str,
        create_new: bool = True,
    ) -> Block:
        """
        Convert an agent to a reusable block.
        
        Args:
            agent_id: ID of the agent to convert
            create_new: If True, create a new block; if False, update existing
            
        Returns:
            Created or updated Block instance
        """
        agent = self.db.query(Agent).filter(
            Agent.id == uuid.UUID(agent_id)
        ).first()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        # Check if block already exists for this agent
        existing_block = self.db.query(Block).filter(
            Block.name == f"Agent: {agent.name}"
        ).first()
        
        if existing_block and not create_new:
            block = existing_block
        else:
            block = Block(
                user_id=agent.user_id,
                name=f"Agent: {agent.name}",
                description=agent.description or f"Block created from agent {agent.name}",
                block_type="composite",  # Agent blocks are composite
                is_public=agent.is_public,
            )
            self.db.add(block)
            self.db.flush()
        
        # Build input/output schemas
        input_schema = {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input text for the agent",
                },
                "context": {
                    "type": "object",
                    "description": "Additional context",
                },
            },
            "required": ["input"],
        }
        
        output_schema = {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "Agent response",
                },
                "metadata": {
                    "type": "object",
                    "description": "Execution metadata",
                },
            },
        }
        
        # Build configuration from agent
        configuration = {
            "agent_id": str(agent.id),
            "agent_type": agent.agent_type,
            "llm_provider": agent.llm_provider,
            "llm_model": agent.llm_model,
            "configuration": agent.configuration,
            "context_items": agent.context_items,
            "mcp_servers": agent.mcp_servers,
        }
        
        # Get agent tools
        agent_tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent.id
        ).all()
        tool_ids = [str(at.tool_id) for at in agent_tools]
        configuration["tool_ids"] = tool_ids
        
        # Update block
        block.input_schema = input_schema
        block.output_schema = output_schema
        block.configuration = configuration
        block.implementation = "agent_executor"  # Special implementation type
        
        self.db.flush()
        
        logger.info(f"Converted agent {agent_id} to block {block.id}")
        
        return block
    
    def add_agent_block_to_workflow(
        self,
        workflow_id: str,
        agent_id: str,
        position_x: float = 0,
        position_y: float = 0,
        auto_convert: bool = True,
        role: str = "worker",
        max_retries: int = 3,
        timeout_seconds: int = 60,
    ) -> WorkflowNode:
        """
        Add an agent as a block node to a workflow.
        
        Args:
            workflow_id: ID of the workflow
            agent_id: ID of the agent
            position_x: X position in visual editor
            position_y: Y position in visual editor
            auto_convert: If True, automatically convert agent to block
            role: Agent role in workflow
            max_retries: Maximum retry attempts
            timeout_seconds: Timeout for agent execution
            
        Returns:
            Created WorkflowNode instance
        """
        workflow = self.db.query(Workflow).filter(
            Workflow.id == uuid.UUID(workflow_id)
        ).first()
        if not workflow:
            raise NotFoundError(f"Workflow {workflow_id} not found")
        
        agent = self.db.query(Agent).filter(
            Agent.id == uuid.UUID(agent_id)
        ).first()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        # Option 1: Convert agent to block (for visual representation)
        if auto_convert:
            block = self.convert_agent_to_block(agent_id, create_new=False)
            block_id = block.id
            
            # Create workflow node with block reference
            node = WorkflowNode(
                workflow_id=uuid.UUID(workflow_id),
                node_type="agent",  # Special node type for agents
                node_ref_id=str(block_id),
                name=agent.name,
                description=agent.description,
                configuration={
                    "agent_id": str(agent_id),
                    "block_id": str(block_id),
                    "role": role,
                    "max_retries": max_retries,
                    "timeout_seconds": timeout_seconds,
                },
                position_x=position_x,
                position_y=position_y,
            )
        else:
            # Option 2: Direct agent reference (simpler, no block conversion)
            node = WorkflowNode(
                workflow_id=uuid.UUID(workflow_id),
                node_type="agent",
                node_ref_id=str(agent_id),  # Direct agent reference
                name=agent.name,
                description=agent.description,
                configuration={
                    "agent_id": str(agent_id),
                    "agentId": str(agent_id),  # For compatibility
                    "role": role,
                    "max_retries": max_retries,
                    "timeout_seconds": timeout_seconds,
                },
                position_x=position_x,
                position_y=position_y,
            )
        
        self.db.add(node)
        self.db.flush()
        
        logger.info(f"Added agent {agent_id} as node to workflow {workflow_id}")
        
        return node
    
    def sync_agent_to_block(
        self,
        agent_id: str,
    ) -> Block:
        """
        Sync agent changes to its corresponding block.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Updated Block instance
        """
        return self.convert_agent_to_block(agent_id, create_new=False)
