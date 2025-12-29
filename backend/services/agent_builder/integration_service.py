"""
Integration Service for AgentWorkflows, Agents, and Blocks

This service manages the complex relationships and data flow between
AgentWorkflows, Agents, and Blocks, ensuring proper integration and execution.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.flows import Agentflow, AgentflowAgent, AgentflowEdge
from backend.db.models.agent_builder import Agent, Block
from backend.services.agent_builder.shared.errors import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


class AgentWorkflowIntegrationService:
    """Service for managing AgentWorkflow, Agent, and Block integration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_agentflow_with_agents(
        self,
        user_id: str,
        agentflow_data: Dict[str, Any],
        agents_config: List[Dict[str, Any]],
        edges_config: Optional[List[Dict[str, Any]]] = None
    ) -> Agentflow:
        """
        Create an Agentflow with associated agents and connections.
        
        Args:
            user_id: User ID
            agentflow_data: Agentflow configuration
            agents_config: List of agent configurations
            edges_config: Optional list of edge configurations
            
        Returns:
            Created Agentflow with all relationships
        """
        try:
            # Create Agentflow
            agentflow = Agentflow(
                user_id=uuid.UUID(user_id),
                name=agentflow_data["name"],
                description=agentflow_data.get("description"),
                orchestration_type=agentflow_data.get("orchestration_type", "sequential"),
                supervisor_config=agentflow_data.get("supervisor_config", {}),
                graph_definition=agentflow_data.get("graph_definition", {}),
                tags=agentflow_data.get("tags", []),
                category=agentflow_data.get("category"),
            )
            
            self.db.add(agentflow)
            self.db.flush()  # Get the ID
            
            # Create AgentflowAgent associations
            agentflow_agents = []
            for agent_config in agents_config:
                # Validate agent exists
                agent = self.db.query(Agent).filter(
                    Agent.id == uuid.UUID(agent_config["agent_id"])
                ).first()
                
                if not agent:
                    raise NotFoundError(f"Agent {agent_config['agent_id']} not found")
                
                # Create or find associated block
                block_id = None
                if agent_config.get("create_block", False):
                    block_id = self._create_agent_block(user_id, agent, agent_config)
                elif agent_config.get("block_id"):
                    block_id = uuid.UUID(agent_config["block_id"])
                
                agentflow_agent = AgentflowAgent(
                    agentflow_id=agentflow.id,
                    agent_id=agent.id,
                    block_id=block_id,
                    name=agent_config.get("name", agent.name),
                    role=agent_config.get("role", "worker"),
                    description=agent_config.get("description", agent.description),
                    capabilities=agent_config.get("capabilities", []),
                    priority=agent_config.get("priority", 1),
                    max_retries=agent_config.get("max_retries", 3),
                    timeout_seconds=agent_config.get("timeout_seconds", 60),
                    dependencies=agent_config.get("dependencies", []),
                    input_mapping=agent_config.get("input_mapping", {}),
                    output_mapping=agent_config.get("output_mapping", {}),
                    conditional_logic=agent_config.get("conditional_logic", {}),
                    parallel_group=agent_config.get("parallel_group"),
                    position_x=agent_config.get("position_x", 0),
                    position_y=agent_config.get("position_y", 0),
                )
                
                self.db.add(agentflow_agent)
                agentflow_agents.append(agentflow_agent)
            
            self.db.flush()  # Get AgentflowAgent IDs
            
            # Create edges if provided
            if edges_config:
                self._create_agentflow_edges(agentflow.id, agentflow_agents, edges_config)
            
            # Update graph definition with agent and block information
            self._update_graph_definition(agentflow, agentflow_agents)
            
            self.db.commit()
            return agentflow
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create agentflow with agents: {e}")
            raise
    
    def _create_agent_block(
        self,
        user_id: str,
        agent: Agent,
        agent_config: Dict[str, Any]
    ) -> uuid.UUID:
        """Create a Block representation for an Agent."""
        block = Block(
            user_id=uuid.UUID(user_id),
            name=f"{agent.name} Block",
            description=f"Block representation of agent: {agent.name}",
            block_type="composite",  # Agent blocks are composite
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input text for the agent"},
                    "context": {"type": "object", "description": "Context data"}
                },
                "required": ["input"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "output": {"type": "string", "description": "Agent response"},
                    "metadata": {"type": "object", "description": "Execution metadata"}
                },
                "required": ["output"]
            },
            configuration={
                "agent_id": str(agent.id),
                "agent_type": agent.agent_type,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "tools": [{"tool_id": str(tool.tool_id)} for tool in agent.tools],
                "visual_config": agent_config.get("visual_config", {})
            },
            implementation=f"agent_executor:{agent.id}",
        )
        
        self.db.add(block)
        self.db.flush()
        return block.id
    
    def _create_agentflow_edges(
        self,
        agentflow_id: uuid.UUID,
        agentflow_agents: List[AgentflowAgent],
        edges_config: List[Dict[str, Any]]
    ):
        """Create edges between AgentflowAgents."""
        agent_map = {agent.name: agent for agent in agentflow_agents}
        
        for edge_config in edges_config:
            source_name = edge_config["source"]
            target_name = edge_config["target"]
            
            if source_name not in agent_map or target_name not in agent_map:
                logger.warning(f"Edge references unknown agents: {source_name} -> {target_name}")
                continue
            
            edge = AgentflowEdge(
                agentflow_id=agentflow_id,
                source_agent_id=agent_map[source_name].id,
                target_agent_id=agent_map[target_name].id,
                edge_type=edge_config.get("edge_type", "data_flow"),
                condition=edge_config.get("condition", {}),
                data_mapping=edge_config.get("data_mapping", {}),
                label=edge_config.get("label"),
                style=edge_config.get("style", {}),
            )
            
            self.db.add(edge)
    
    def _update_graph_definition(
        self,
        agentflow: Agentflow,
        agentflow_agents: List[AgentflowAgent]
    ):
        """Update the graph definition with agent and block information."""
        nodes = []
        edges = []
        
        # Create nodes from agents
        for agent in agentflow_agents:
            node = {
                "id": str(agent.id),
                "type": "agent",
                "data": {
                    "agent_id": str(agent.agent_id) if agent.agent_id else None,
                    "block_id": str(agent.block_id) if agent.block_id else None,
                    "name": agent.name,
                    "role": agent.role,
                    "capabilities": agent.capabilities,
                    "priority": agent.priority,
                    "max_retries": agent.max_retries,
                    "timeout_seconds": agent.timeout_seconds,
                    "input_mapping": agent.input_mapping,
                    "output_mapping": agent.output_mapping,
                    "conditional_logic": agent.conditional_logic,
                },
                "position": {
                    "x": agent.position_x,
                    "y": agent.position_y,
                }
            }
            nodes.append(node)
        
        # Create edges from dependencies and explicit edges
        for agent in agentflow_agents:
            for dep_name in agent.dependencies:
                # Find dependency agent
                dep_agent = next((a for a in agentflow_agents if a.name == dep_name), None)
                if dep_agent:
                    edge = {
                        "id": f"{dep_agent.id}-{agent.id}",
                        "source": str(dep_agent.id),
                        "target": str(agent.id),
                        "type": "dependency",
                        "data": {"type": "dependency"}
                    }
                    edges.append(edge)
        
        # Add explicit edges from database
        db_edges = self.db.query(AgentflowEdge).filter(
            AgentflowEdge.agentflow_id == agentflow.id
        ).all()
        
        for db_edge in db_edges:
            edge = {
                "id": str(db_edge.id),
                "source": str(db_edge.source_agent_id),
                "target": str(db_edge.target_agent_id),
                "type": db_edge.edge_type,
                "data": {
                    "type": db_edge.edge_type,
                    "condition": db_edge.condition,
                    "data_mapping": db_edge.data_mapping,
                    "label": db_edge.label,
                    "style": db_edge.style,
                }
            }
            edges.append(edge)
        
        # Update graph definition
        agentflow.graph_definition = {
            "nodes": nodes,
            "edges": edges,
            "viewport": {"x": 0, "y": 0, "zoom": 1},
            "metadata": {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "orchestration_type": agentflow.orchestration_type,
                "supervisor_enabled": bool(agentflow.supervisor_config.get("enabled", False)),
            }
        }
    
    def get_agentflow_execution_plan(self, agentflow_id: str) -> Dict[str, Any]:
        """
        Generate an execution plan for an Agentflow.
        
        Returns:
            Execution plan with agent order, dependencies, and parallel groups
        """
        agentflow = self.db.query(Agentflow).filter(
            Agentflow.id == uuid.UUID(agentflow_id)
        ).first()
        
        if not agentflow:
            raise NotFoundError(f"Agentflow {agentflow_id} not found")
        
        agents = self.db.query(AgentflowAgent).filter(
            AgentflowAgent.agentflow_id == agentflow.id
        ).order_by(AgentflowAgent.priority).all()
        
        edges = self.db.query(AgentflowEdge).filter(
            AgentflowEdge.agentflow_id == agentflow.id
        ).all()
        
        # Build execution plan based on orchestration type
        if agentflow.orchestration_type == "sequential":
            execution_plan = self._build_sequential_plan(agents, edges)
        elif agentflow.orchestration_type == "parallel":
            execution_plan = self._build_parallel_plan(agents, edges)
        elif agentflow.orchestration_type == "hierarchical":
            execution_plan = self._build_hierarchical_plan(agents, edges)
        else:
            execution_plan = self._build_adaptive_plan(agents, edges, agentflow.orchestration_type)
        
        return {
            "agentflow_id": str(agentflow.id),
            "orchestration_type": agentflow.orchestration_type,
            "execution_plan": execution_plan,
            "supervisor_config": agentflow.supervisor_config,
            "total_agents": len(agents),
            "total_edges": len(edges),
        }
    
    def _build_sequential_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge]
    ) -> List[Dict[str, Any]]:
        """Build sequential execution plan."""
        return [
            {
                "step": i + 1,
                "agent_id": str(agent.id),
                "name": agent.name,
                "role": agent.role,
                "dependencies": agent.dependencies,
                "parallel_group": None,
                "execution_type": "sequential"
            }
            for i, agent in enumerate(agents)
        ]
    
    def _build_parallel_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge]
    ) -> List[Dict[str, Any]]:
        """Build parallel execution plan."""
        # Group agents by parallel_group or treat all as parallel
        groups = {}
        for agent in agents:
            group_key = agent.parallel_group or "default"
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(agent)
        
        plan = []
        for group_name, group_agents in groups.items():
            plan.append({
                "step": len(plan) + 1,
                "execution_type": "parallel",
                "parallel_group": group_name,
                "agents": [
                    {
                        "agent_id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "dependencies": agent.dependencies,
                    }
                    for agent in group_agents
                ]
            })
        
        return plan
    
    def _build_hierarchical_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge]
    ) -> List[Dict[str, Any]]:
        """Build hierarchical execution plan."""
        # Find root agents (no incoming edges)
        agent_ids = {str(agent.id) for agent in agents}
        target_ids = {str(edge.target_agent_id) for edge in edges}
        root_ids = agent_ids - target_ids
        
        # Build hierarchy levels
        levels = []
        processed = set()
        current_level = list(root_ids)
        
        while current_level:
            level_agents = [
                agent for agent in agents 
                if str(agent.id) in current_level
            ]
            
            levels.append({
                "level": len(levels) + 1,
                "execution_type": "parallel",
                "agents": [
                    {
                        "agent_id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "dependencies": agent.dependencies,
                    }
                    for agent in level_agents
                ]
            })
            
            processed.update(current_level)
            
            # Find next level (agents whose dependencies are all processed)
            next_level = []
            for agent in agents:
                if str(agent.id) not in processed:
                    deps_satisfied = all(
                        dep_name in [a.name for a in agents if str(a.id) in processed]
                        for dep_name in agent.dependencies
                    )
                    if deps_satisfied:
                        next_level.append(str(agent.id))
            
            current_level = next_level
        
        return levels
    
    def _build_adaptive_plan(
        self,
        agents: List[AgentflowAgent],
        edges: List[AgentflowEdge],
        orchestration_type: str
    ) -> Dict[str, Any]:
        """Build adaptive execution plan for advanced orchestration types."""
        return {
            "execution_type": "adaptive",
            "orchestration_type": orchestration_type,
            "agents": [
                {
                    "agent_id": str(agent.id),
                    "name": agent.name,
                    "role": agent.role,
                    "capabilities": agent.capabilities,
                    "priority": agent.priority,
                    "dependencies": agent.dependencies,
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
            "adaptive_config": {
                "dynamic_routing": orchestration_type == "dynamic_routing",
                "consensus_building": orchestration_type == "consensus_building",
                "swarm_intelligence": orchestration_type == "swarm_intelligence",
                "event_driven": orchestration_type == "event_driven",
                "reflection": orchestration_type == "reflection",
            }
        }
    
    def validate_agentflow_integrity(self, agentflow_id: str) -> Dict[str, Any]:
        """
        Validate the integrity of an Agentflow's agent and block relationships.
        
        Returns:
            Validation report with issues and recommendations
        """
        agentflow = self.db.query(Agentflow).filter(
            Agentflow.id == uuid.UUID(agentflow_id)
        ).first()
        
        if not agentflow:
            raise NotFoundError(f"Agentflow {agentflow_id} not found")
        
        agents = self.db.query(AgentflowAgent).filter(
            AgentflowAgent.agentflow_id == agentflow.id
        ).all()
        
        edges = self.db.query(AgentflowEdge).filter(
            AgentflowEdge.agentflow_id == agentflow.id
        ).all()
        
        issues = []
        recommendations = []
        
        # Check for orphaned agents
        for agent in agents:
            if agent.agent_id:
                db_agent = self.db.query(Agent).filter(Agent.id == agent.agent_id).first()
                if not db_agent:
                    issues.append(f"Agent {agent.name} references non-existent agent {agent.agent_id}")
            
            if agent.block_id:
                db_block = self.db.query(Block).filter(Block.id == agent.block_id).first()
                if not db_block:
                    issues.append(f"Agent {agent.name} references non-existent block {agent.block_id}")
        
        # Check for circular dependencies
        def has_circular_dependency(agent_name, visited, path):
            if agent_name in path:
                return True
            if agent_name in visited:
                return False
            
            visited.add(agent_name)
            path.add(agent_name)
            
            agent = next((a for a in agents if a.name == agent_name), None)
            if agent:
                for dep in agent.dependencies:
                    if has_circular_dependency(dep, visited, path):
                        return True
            
            path.remove(agent_name)
            return False
        
        visited = set()
        for agent in agents:
            if agent.name not in visited:
                if has_circular_dependency(agent.name, visited, set()):
                    issues.append(f"Circular dependency detected involving agent {agent.name}")
        
        # Check edge consistency
        agent_ids = {str(agent.id) for agent in agents}
        for edge in edges:
            if str(edge.source_agent_id) not in agent_ids:
                issues.append(f"Edge references non-existent source agent {edge.source_agent_id}")
            if str(edge.target_agent_id) not in agent_ids:
                issues.append(f"Edge references non-existent target agent {edge.target_agent_id}")
        
        # Generate recommendations
        if len(agents) == 0:
            recommendations.append("Add at least one agent to the agentflow")
        elif len(agents) == 1:
            recommendations.append("Consider adding more agents for better workflow distribution")
        
        if agentflow.orchestration_type == "parallel" and not any(agent.parallel_group for agent in agents):
            recommendations.append("Define parallel groups for better parallel execution control")
        
        if agentflow.supervisor_config.get("enabled") and not agentflow.supervisor_config.get("llm_provider"):
            recommendations.append("Configure supervisor LLM provider for AI-powered orchestration")
        
        return {
            "agentflow_id": str(agentflow.id),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "recommendations": recommendations,
            "agent_count": len(agents),
            "edge_count": len(edges),
            "orchestration_type": agentflow.orchestration_type,
        }