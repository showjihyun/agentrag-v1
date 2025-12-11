"""
Workflow Domain Entities

Core domain entities for the Workflow bounded context.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from uuid import UUID, uuid4

from .value_objects import NodeType, EdgeType, NodeConfig, Position, EdgeCondition


@dataclass
class NodeEntity:
    """Workflow node entity."""
    id: str
    workflow_id: UUID
    node_type: NodeType
    config: NodeConfig
    position: Position = field(default_factory=Position)
    node_ref_id: Optional[str] = None  # Reference to agent/tool/block
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_entry_point(self) -> bool:
        return self.node_type in (NodeType.START, NodeType.TRIGGER, NodeType.WEBHOOK, NodeType.SCHEDULE)
    
    @property
    def is_exit_point(self) -> bool:
        return self.node_type == NodeType.END
    
    @property
    def is_control_flow(self) -> bool:
        return self.node_type in (
            NodeType.CONDITION, NodeType.LOOP, NodeType.PARALLEL, 
            NodeType.MERGE, NodeType.DELAY
        )
    
    @property
    def is_ai_node(self) -> bool:
        return self.node_type in (NodeType.AGENT, NodeType.AI_AGENT, NodeType.LLM)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "node_ref_id": self.node_ref_id,
            "position_x": self.position.x,
            "position_y": self.position.y,
            "configuration": self.config.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workflow_id: UUID) -> "NodeEntity":
        node_type_str = data.get("node_type", "block")
        try:
            node_type = NodeType(node_type_str)
        except ValueError:
            node_type = NodeType.BLOCK
        
        config = NodeConfig.from_dict(data.get("configuration", {}))
        
        return cls(
            id=data.get("id", str(uuid4())),
            workflow_id=workflow_id,
            node_type=node_type,
            config=config,
            position=Position(
                x=data.get("position_x", 0),
                y=data.get("position_y", 0),
            ),
            node_ref_id=data.get("node_ref_id"),
        )


@dataclass
class EdgeEntity:
    """Workflow edge entity."""
    id: str
    workflow_id: UUID
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType = EdgeType.NORMAL
    condition: Optional[EdgeCondition] = None
    label: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_conditional(self) -> bool:
        return self.edge_type == EdgeType.CONDITIONAL
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type.value,
            "label": self.label,
        }
        if self.condition:
            result["condition"] = self.condition.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workflow_id: UUID) -> "EdgeEntity":
        edge_type_str = data.get("edge_type", "normal")
        try:
            edge_type = EdgeType(edge_type_str)
        except ValueError:
            edge_type = EdgeType.NORMAL
        
        condition = None
        if data.get("condition"):
            if isinstance(data["condition"], dict):
                condition = EdgeCondition(
                    expression=data["condition"].get("expression", ""),
                    label=data["condition"].get("label"),
                )
            else:
                condition = EdgeCondition(expression=str(data["condition"]))
        
        return cls(
            id=data.get("id", str(uuid4())),
            workflow_id=workflow_id,
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            edge_type=edge_type,
            condition=condition,
            label=data.get("label"),
        )


@dataclass
class WorkflowEntity:
    """Workflow domain entity."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    nodes: List[NodeEntity] = field(default_factory=list)
    edges: List[EdgeEntity] = field(default_factory=list)
    entry_point: Optional[str] = None
    is_public: bool = False
    is_active: bool = True
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    @property
    def node_ids(self) -> Set[str]:
        return {node.id for node in self.nodes}
    
    @property
    def entry_nodes(self) -> List[NodeEntity]:
        """Get all entry point nodes."""
        return [n for n in self.nodes if n.is_entry_point]
    
    @property
    def exit_nodes(self) -> List[NodeEntity]:
        """Get all exit point nodes."""
        return [n for n in self.nodes if n.is_exit_point]
    
    def get_node(self, node_id: str) -> Optional[NodeEntity]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_outgoing_edges(self, node_id: str) -> List[EdgeEntity]:
        """Get all edges originating from a node."""
        return [e for e in self.edges if e.source_node_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[EdgeEntity]:
        """Get all edges targeting a node."""
        return [e for e in self.edges if e.target_node_id == node_id]
    
    def get_next_nodes(self, node_id: str) -> List[NodeEntity]:
        """Get all nodes that follow a given node."""
        outgoing = self.get_outgoing_edges(node_id)
        return [self.get_node(e.target_node_id) for e in outgoing if self.get_node(e.target_node_id)]
    
    def add_node(self, node: NodeEntity) -> None:
        """Add a node to the workflow."""
        self.nodes.append(node)
        self.updated_at = datetime.utcnow()
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and its connected edges."""
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source_node_id != node_id and e.target_node_id != node_id]
        self.updated_at = datetime.utcnow()
    
    def add_edge(self, edge: EdgeEntity) -> None:
        """Add an edge to the workflow."""
        self.edges.append(edge)
        self.updated_at = datetime.utcnow()
    
    def remove_edge(self, edge_id: str) -> None:
        """Remove an edge."""
        self.edges = [e for e in self.edges if e.id != edge_id]
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the workflow."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def to_graph_definition(self) -> Dict[str, Any]:
        """Convert to graph definition format."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "entry_point": self.entry_point,
        }
    
    @classmethod
    def from_graph_definition(
        cls,
        workflow_id: UUID,
        user_id: UUID,
        name: str,
        graph_def: Dict[str, Any],
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> "WorkflowEntity":
        """Create workflow from graph definition."""
        nodes = [
            NodeEntity.from_dict(n, workflow_id)
            for n in graph_def.get("nodes", [])
        ]
        edges = [
            EdgeEntity.from_dict(e, workflow_id)
            for e in graph_def.get("edges", [])
        ]
        
        return cls(
            id=workflow_id,
            user_id=user_id,
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            entry_point=graph_def.get("entry_point"),
            is_public=is_public,
        )
