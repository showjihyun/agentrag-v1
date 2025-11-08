"""Workflow validation logic."""

import re
from typing import List, Dict, Any, Set, Tuple
from backend.models.agent_builder import WorkflowCreate, WorkflowUpdate, WorkflowNodeCreate, WorkflowEdgeCreate


class WorkflowValidator:
    """Validator for Workflow operations."""
    
    # Name constraints
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 255
    
    # Description constraints
    MAX_DESCRIPTION_LENGTH = 2000
    
    # Valid node types
    VALID_NODE_TYPES = ["agent", "block", "control"]
    
    # Valid edge types
    VALID_EDGE_TYPES = ["normal", "conditional"]
    
    # Valid control node types
    VALID_CONTROL_TYPES = ["start", "end", "condition", "loop", "parallel"]
    
    @classmethod
    def validate_create(cls, data: WorkflowCreate) -> Tuple[List[str], List[str]]:
        """
        Validate workflow creation data.
        
        Args:
            data: Workflow creation data
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate name
        name_errors = cls._validate_name(data.name)
        errors.extend(name_errors)
        
        # Validate description
        if data.description:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # Validate nodes
        if not data.nodes or len(data.nodes) == 0:
            errors.append("Workflow must have at least one node")
            return errors, warnings
        
        node_errors, node_warnings = cls._validate_nodes(data.nodes)
        errors.extend(node_errors)
        warnings.extend(node_warnings)
        
        # Validate edges
        edge_errors, edge_warnings = cls._validate_edges(data.edges, data.nodes)
        errors.extend(edge_errors)
        warnings.extend(edge_warnings)
        
        # Validate entry point
        if data.entry_point:
            entry_errors = cls._validate_entry_point(data.entry_point, data.nodes)
            errors.extend(entry_errors)
        else:
            errors.append("Entry point is required")
        
        # Validate graph structure
        if not errors:  # Only if no basic errors
            graph_errors, graph_warnings = cls._validate_graph_structure(
                data.nodes,
                data.edges,
                data.entry_point
            )
            errors.extend(graph_errors)
            warnings.extend(graph_warnings)
        
        return errors, warnings
    
    @classmethod
    def validate_update(cls, data: WorkflowUpdate) -> Tuple[List[str], List[str]]:
        """
        Validate workflow update data.
        
        Args:
            data: Workflow update data
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate name if provided
        if data.name is not None:
            name_errors = cls._validate_name(data.name)
            errors.extend(name_errors)
        
        # Validate description if provided
        if data.description is not None:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # If nodes/edges/entry_point are being updated, validate them
        if data.nodes is not None or data.edges is not None or data.entry_point is not None:
            # Need all three for validation
            if data.nodes is None or data.edges is None or data.entry_point is None:
                errors.append("When updating workflow structure, nodes, edges, and entry_point must all be provided")
            else:
                # Validate like create
                node_errors, node_warnings = cls._validate_nodes(data.nodes)
                errors.extend(node_errors)
                warnings.extend(node_warnings)
                
                edge_errors, edge_warnings = cls._validate_edges(data.edges, data.nodes)
                errors.extend(edge_errors)
                warnings.extend(edge_warnings)
                
                entry_errors = cls._validate_entry_point(data.entry_point, data.nodes)
                errors.extend(entry_errors)
                
                if not errors:
                    graph_errors, graph_warnings = cls._validate_graph_structure(
                        data.nodes,
                        data.edges,
                        data.entry_point
                    )
                    errors.extend(graph_errors)
                    warnings.extend(graph_warnings)
        
        return errors, warnings
    
    @classmethod
    def _validate_name(cls, name: str) -> List[str]:
        """Validate workflow name."""
        errors = []
        
        if not name or len(name.strip()) == 0:
            errors.append("Name is required")
            return errors
        
        name = name.strip()
        
        if len(name) < cls.MIN_NAME_LENGTH:
            errors.append(f"Name must be at least {cls.MIN_NAME_LENGTH} characters")
        
        if len(name) > cls.MAX_NAME_LENGTH:
            errors.append(f"Name must not exceed {cls.MAX_NAME_LENGTH} characters")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_()]+$', name):
            errors.append("Name contains invalid characters")
        
        return errors
    
    @classmethod
    def _validate_description(cls, description: str) -> List[str]:
        """Validate workflow description."""
        errors = []
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            errors.append(f"Description must not exceed {cls.MAX_DESCRIPTION_LENGTH} characters")
        
        return errors
    
    @classmethod
    def _validate_nodes(cls, nodes: List[WorkflowNodeCreate]) -> Tuple[List[str], List[str]]:
        """Validate workflow nodes."""
        errors = []
        warnings = []
        
        if not nodes:
            errors.append("Nodes list cannot be empty")
            return errors, warnings
        
        node_ids = set()
        
        for i, node in enumerate(nodes):
            # Check for duplicate IDs
            if node.id in node_ids:
                errors.append(f"Duplicate node ID: {node.id}")
            node_ids.add(node.id)
            
            # Validate node type
            if node.node_type not in cls.VALID_NODE_TYPES:
                errors.append(
                    f"Invalid node type for node {node.id}: {node.node_type}. "
                    f"Must be one of: {', '.join(cls.VALID_NODE_TYPES)}"
                )
            
            # Validate node_ref_id for agent/block nodes
            if node.node_type in ["agent", "block"]:
                if not node.node_ref_id:
                    errors.append(f"Node {node.id} of type {node.node_type} must have node_ref_id")
            
            # Validate control node configuration
            if node.node_type == "control":
                if not node.configuration or "control_type" not in node.configuration:
                    errors.append(f"Control node {node.id} must have control_type in configuration")
                elif node.configuration["control_type"] not in cls.VALID_CONTROL_TYPES:
                    errors.append(
                        f"Invalid control type for node {node.id}: {node.configuration['control_type']}"
                    )
        
        return errors, warnings
    
    @classmethod
    def _validate_edges(
        cls,
        edges: List[WorkflowEdgeCreate],
        nodes: List[WorkflowNodeCreate]
    ) -> Tuple[List[str], List[str]]:
        """Validate workflow edges."""
        errors = []
        warnings = []
        
        node_ids = {node.id for node in nodes}
        edge_ids = set()
        
        for edge in edges:
            # Check for duplicate IDs
            if edge.id in edge_ids:
                errors.append(f"Duplicate edge ID: {edge.id}")
            edge_ids.add(edge.id)
            
            # Validate source node exists
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge {edge.id} source node not found: {edge.source_node_id}")
            
            # Validate target node exists
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge {edge.id} target node not found: {edge.target_node_id}")
            
            # Validate edge type
            if edge.edge_type not in cls.VALID_EDGE_TYPES:
                errors.append(
                    f"Invalid edge type for edge {edge.id}: {edge.edge_type}. "
                    f"Must be one of: {', '.join(cls.VALID_EDGE_TYPES)}"
                )
            
            # Validate conditional edges have conditions
            if edge.edge_type == "conditional":
                if not edge.condition or len(edge.condition.strip()) == 0:
                    errors.append(f"Conditional edge {edge.id} must have a condition")
        
        return errors, warnings
    
    @classmethod
    def _validate_entry_point(cls, entry_point: str, nodes: List[WorkflowNodeCreate]) -> List[str]:
        """Validate entry point."""
        errors = []
        
        node_ids = {node.id for node in nodes}
        
        if entry_point not in node_ids:
            errors.append(f"Entry point node not found: {entry_point}")
        
        return errors
    
    @classmethod
    def _validate_graph_structure(
        cls,
        nodes: List[WorkflowNodeCreate],
        edges: List[WorkflowEdgeCreate],
        entry_point: str
    ) -> Tuple[List[str], List[str]]:
        """Validate graph structure (cycles, disconnected nodes, etc.)."""
        errors = []
        warnings = []
        
        # Build adjacency list
        graph = {node.id: [] for node in nodes}
        for edge in edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)
        
        # Check for cycles
        has_cycle, cycle_path = cls._detect_cycle(graph)
        if has_cycle:
            errors.append(f"Workflow contains cycle: {' -> '.join(cycle_path)}")
        
        # Check for disconnected nodes
        disconnected = cls._find_disconnected_nodes(graph, entry_point)
        if disconnected:
            warnings.append(f"Disconnected nodes found: {', '.join(disconnected)}")
        
        # Check for unreachable nodes
        unreachable = cls._find_unreachable_nodes(graph, entry_point)
        if unreachable:
            warnings.append(f"Unreachable nodes from entry point: {', '.join(unreachable)}")
        
        return errors, warnings
    
    @classmethod
    def _detect_cycle(cls, graph: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """Detect cycles in graph using DFS."""
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
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    path.append(neighbor)
                    return True
            
            rec_stack.remove(node_id)
            path.pop()
            return False
        
        for node_id in graph:
            if node_id not in visited:
                if dfs(node_id):
                    return True, path
        
        return False, []
    
    @classmethod
    def _find_disconnected_nodes(cls, graph: Dict[str, List[str]], entry_point: str) -> List[str]:
        """Find nodes that are not connected to the main graph."""
        # This is a simplified check - just finds nodes with no incoming or outgoing edges
        disconnected = []
        
        # Build reverse graph (incoming edges)
        reverse_graph = {node_id: [] for node_id in graph}
        for node_id, neighbors in graph.items():
            for neighbor in neighbors:
                reverse_graph[neighbor].append(node_id)
        
        for node_id in graph:
            if node_id == entry_point:
                continue
            
            # Node is disconnected if it has no incoming and no outgoing edges
            if len(graph[node_id]) == 0 and len(reverse_graph[node_id]) == 0:
                disconnected.append(node_id)
        
        return disconnected
    
    @classmethod
    def _find_unreachable_nodes(cls, graph: Dict[str, List[str]], entry_point: str) -> List[str]:
        """Find nodes that are not reachable from entry point."""
        visited = set()
        queue = [entry_point]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Find unreachable nodes
        all_nodes = set(graph.keys())
        unreachable = all_nodes - visited
        
        return list(unreachable)
