"""
Workflow Aggregate Root

The aggregate root for all operations on the Workflow domain.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID, uuid4

from .entities import WorkflowEntity, NodeEntity, EdgeEntity
from .value_objects import NodeType, EdgeType, NodeConfig, Position, ExecutionContext
from .events import (
    DomainEvent, WorkflowCreated, WorkflowUpdated, WorkflowDeleted,
    WorkflowValidated, WorkflowCloned
)


class WorkflowAggregate:
    """
    Workflow Aggregate Root.
    
    Manages the Workflow entity and its nodes/edges.
    Provides validation and business rule enforcement.
    """
    
    def __init__(self, workflow: WorkflowEntity):
        self._workflow = workflow
        self._events: List[DomainEvent] = []
    
    @property
    def id(self) -> UUID:
        return self._workflow.id
    
    @property
    def workflow(self) -> WorkflowEntity:
        return self._workflow
    
    @property
    def events(self) -> List[DomainEvent]:
        return self._events.copy()
    
    def clear_events(self) -> None:
        self._events.clear()
    
    # ========================================================================
    # FACTORY METHODS
    # ========================================================================
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        entry_point: Optional[str] = None,
        is_public: bool = False,
    ) -> "WorkflowAggregate":
        """
        Factory method to create a new Workflow aggregate.
        """
        workflow_id = uuid4()
        
        # Convert node dicts to entities
        node_entities = []
        if nodes:
            for node_data in nodes:
                node_entities.append(NodeEntity.from_dict(node_data, workflow_id))
        
        # Convert edge dicts to entities
        edge_entities = []
        if edges:
            for edge_data in edges:
                edge_entities.append(EdgeEntity.from_dict(edge_data, workflow_id))
        
        # Determine entry point
        if not entry_point and node_entities:
            # Find start node or first node
            start_nodes = [n for n in node_entities if n.is_entry_point]
            if start_nodes:
                entry_point = start_nodes[0].id
            else:
                entry_point = node_entities[0].id
        
        workflow = WorkflowEntity(
            id=workflow_id,
            user_id=user_id,
            name=name,
            description=description,
            nodes=node_entities,
            edges=edge_entities,
            entry_point=entry_point,
            is_public=is_public,
        )
        
        aggregate = cls(workflow)
        
        aggregate._events.append(WorkflowCreated(
            aggregate_id=workflow_id,
            user_id=user_id,
            workflow_name=name,
            node_count=len(node_entities),
            edge_count=len(edge_entities),
            is_public=is_public,
        ))
        
        return aggregate
    
    @classmethod
    def from_graph_definition(
        cls,
        user_id: UUID,
        name: str,
        graph_def: Dict[str, Any],
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> "WorkflowAggregate":
        """Create from graph definition format."""
        return cls.create(
            user_id=user_id,
            name=name,
            description=description,
            nodes=graph_def.get("nodes", []),
            edges=graph_def.get("edges", []),
            entry_point=graph_def.get("entry_point"),
            is_public=is_public,
        )
    
    # ========================================================================
    # COMMANDS
    # ========================================================================
    
    def update(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> None:
        """Update workflow metadata."""
        updated_fields = []
        
        if name is not None and name != self._workflow.name:
            self._workflow.name = name
            updated_fields.append("name")
        
        if description is not None:
            self._workflow.description = description
            updated_fields.append("description")
        
        if is_public is not None and is_public != self._workflow.is_public:
            self._workflow.is_public = is_public
            updated_fields.append("is_public")
        
        if updated_fields:
            self._workflow.updated_at = datetime.utcnow()
            self._events.append(WorkflowUpdated(
                aggregate_id=self._workflow.id,
                user_id=user_id,
                updated_fields=updated_fields,
            ))
    
    def update_graph(
        self,
        user_id: UUID,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        entry_point: Optional[str] = None,
    ) -> None:
        """Update the workflow graph (nodes and edges)."""
        old_node_count = len(self._workflow.nodes)
        old_edge_count = len(self._workflow.edges)
        
        # Convert to entities
        new_nodes = [NodeEntity.from_dict(n, self._workflow.id) for n in nodes]
        new_edges = [EdgeEntity.from_dict(e, self._workflow.id) for e in edges]
        
        self._workflow.nodes = new_nodes
        self._workflow.edges = new_edges
        
        if entry_point:
            self._workflow.entry_point = entry_point
        elif new_nodes:
            start_nodes = [n for n in new_nodes if n.is_entry_point]
            if start_nodes:
                self._workflow.entry_point = start_nodes[0].id
        
        self._workflow.updated_at = datetime.utcnow()
        
        self._events.append(WorkflowUpdated(
            aggregate_id=self._workflow.id,
            user_id=user_id,
            updated_fields=["nodes", "edges", "entry_point"],
            nodes_added=max(0, len(new_nodes) - old_node_count),
            nodes_removed=max(0, old_node_count - len(new_nodes)),
            edges_added=max(0, len(new_edges) - old_edge_count),
            edges_removed=max(0, old_edge_count - len(new_edges)),
        ))
    
    def add_node(
        self,
        node_type: NodeType,
        config: Dict[str, Any],
        position: Tuple[float, float] = (0, 0),
        node_id: Optional[str] = None,
    ) -> NodeEntity:
        """Add a node to the workflow."""
        node = NodeEntity(
            id=node_id or str(uuid4()),
            workflow_id=self._workflow.id,
            node_type=node_type,
            config=NodeConfig.from_dict(config),
            position=Position(x=position[0], y=position[1]),
        )
        self._workflow.add_node(node)
        return node
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and its connected edges."""
        self._workflow.remove_node(node_id)
    
    def add_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        edge_type: EdgeType = EdgeType.NORMAL,
        condition: Optional[str] = None,
        edge_id: Optional[str] = None,
    ) -> EdgeEntity:
        """Add an edge to the workflow."""
        from .value_objects import EdgeCondition
        
        edge = EdgeEntity(
            id=edge_id or str(uuid4()),
            workflow_id=self._workflow.id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            condition=EdgeCondition(expression=condition) if condition else None,
        )
        self._workflow.add_edge(edge)
        return edge
    
    def remove_edge(self, edge_id: str) -> None:
        """Remove an edge."""
        self._workflow.remove_edge(edge_id)
    
    def delete(self, user_id: UUID, hard: bool = False) -> None:
        """Delete the workflow."""
        if not hard:
            self._workflow.soft_delete()
        
        self._events.append(WorkflowDeleted(
            aggregate_id=self._workflow.id,
            user_id=user_id,
            workflow_name=self._workflow.name,
            deletion_type="hard" if hard else "soft",
        ))
    
    def clone(self, user_id: UUID, new_name: Optional[str] = None) -> "WorkflowAggregate":
        """Clone this workflow."""
        cloned = WorkflowAggregate.create(
            user_id=user_id,
            name=new_name or f"{self._workflow.name} (Copy)",
            description=self._workflow.description,
            nodes=[n.to_dict() for n in self._workflow.nodes],
            edges=[e.to_dict() for e in self._workflow.edges],
            entry_point=self._workflow.entry_point,
            is_public=False,
        )
        
        self._events.append(WorkflowCloned(
            aggregate_id=self._workflow.id,
            source_workflow_id=self._workflow.id,
            new_workflow_id=cloned.id,
            user_id=user_id,
            new_workflow_name=cloned.workflow.name,
        ))
        
        return cloned
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the workflow structure.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for nodes
        if not self._workflow.nodes:
            errors.append("Workflow must have at least one node")
            return False, errors, warnings
        
        node_ids = self._workflow.node_ids
        
        # Validate entry point
        if self._workflow.entry_point and self._workflow.entry_point not in node_ids:
            errors.append(f"Entry point '{self._workflow.entry_point}' not found in nodes")
        
        # Validate edges
        for edge in self._workflow.edges:
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge source '{edge.source_node_id}' not found")
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge target '{edge.target_node_id}' not found")
            if edge.is_conditional and not edge.condition:
                errors.append(f"Conditional edge '{edge.id}' missing condition")
            if edge.source_node_id == edge.target_node_id:
                warnings.append(f"Self-loop detected on node '{edge.source_node_id}'")
        
        # Check for cycles (excluding intentional loops)
        has_cycle, cycle_path = self._detect_cycle()
        if has_cycle:
            loop_nodes = [n for n in self._workflow.nodes if n.node_type == NodeType.LOOP]
            loop_node_ids = {n.id for n in loop_nodes}
            if not any(nid in loop_node_ids for nid in cycle_path):
                errors.append(f"Unintentional cycle detected: {' -> '.join(cycle_path)}")
            else:
                warnings.append(f"Loop detected (intentional): {' -> '.join(cycle_path)}")
        
        # Check for disconnected nodes
        disconnected = self._find_disconnected_nodes()
        if disconnected:
            warnings.append(f"Disconnected nodes: {', '.join(disconnected)}")
        
        # Check for end nodes
        if not self._workflow.exit_nodes:
            warnings.append("No end node found")
        
        is_valid = len(errors) == 0
        
        self._events.append(WorkflowValidated(
            aggregate_id=self._workflow.id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        ))
        
        return is_valid, errors, warnings
    
    def _detect_cycle(self) -> Tuple[bool, List[str]]:
        """Detect cycles using DFS."""
        graph = {node.id: [] for node in self._workflow.nodes}
        for edge in self._workflow.edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)
        
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    path.append(neighbor)
                    return True
            
            rec_stack.remove(node_id)
            path.pop()
            return False
        
        for node in self._workflow.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True, path
        
        return False, []
    
    def _find_disconnected_nodes(self) -> List[str]:
        """Find nodes not reachable from entry point."""
        if not self._workflow.entry_point:
            return []
        
        graph = {node.id: [] for node in self._workflow.nodes}
        for edge in self._workflow.edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)
        
        visited = set()
        queue = [self._workflow.entry_point]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            queue.extend(graph.get(node_id, []))
        
        return list(self._workflow.node_ids - visited)
