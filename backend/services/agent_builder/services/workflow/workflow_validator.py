"""Workflow Validator for validating workflow structure and configuration."""

import logging
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from uuid import UUID

from backend.db.models.agent_builder import Workflow, AgentBlock, AgentEdge
from backend.models.agent_builder import WorkflowValidationError

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """Validates workflow structure and configuration."""
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Validator.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def validate_workflow(self, workflow_id: UUID) -> Tuple[bool, List[WorkflowValidationError], List[WorkflowValidationError]]:
        """
        Validate a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors: List[WorkflowValidationError] = []
        warnings: List[WorkflowValidationError] = []
        
        # Load workflow
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            errors.append(WorkflowValidationError(
                error_type="workflow_not_found",
                message="Workflow not found",
                severity="error"
            ))
            return False, errors, warnings
        
        # Load blocks and edges
        blocks = self.db.query(AgentBlock).filter(
            AgentBlock.workflow_id == workflow_id,
            AgentBlock.enabled == True
        ).all()
        
        edges = self.db.query(AgentEdge).filter(
            AgentEdge.workflow_id == workflow_id
        ).all()
        
        # Validate blocks
        block_errors, block_warnings = self._validate_blocks(blocks)
        errors.extend(block_errors)
        warnings.extend(block_warnings)
        
        # Validate edges
        edge_errors, edge_warnings = self._validate_edges(blocks, edges)
        errors.extend(edge_errors)
        warnings.extend(edge_warnings)
        
        # Validate graph structure
        graph_errors, graph_warnings = self._validate_graph_structure(blocks, edges)
        errors.extend(graph_errors)
        warnings.extend(graph_warnings)
        
        # Check for cycles
        cycle_errors = self._detect_cycles(blocks, edges)
        errors.extend(cycle_errors)
        
        # Check for disconnected nodes
        disconnected_warnings = self._detect_disconnected_nodes(blocks, edges)
        warnings.extend(disconnected_warnings)
        
        is_valid = len(errors) == 0
        
        logger.info(f"Workflow validation complete: {len(errors)} errors, {len(warnings)} warnings")
        
        return is_valid, errors, warnings
    
    def _validate_blocks(self, blocks: List[AgentBlock]) -> Tuple[List[WorkflowValidationError], List[WorkflowValidationError]]:
        """
        Validate blocks.
        
        Args:
            blocks: List of blocks
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[WorkflowValidationError] = []
        warnings: List[WorkflowValidationError] = []
        
        if len(blocks) == 0:
            warnings.append(WorkflowValidationError(
                error_type="empty_workflow",
                message="Workflow has no blocks",
                severity="warning"
            ))
            return errors, warnings
        
        for block in blocks:
            # Validate required inputs
            if block.inputs:
                for input_name, input_config in block.inputs.items():
                    if input_config.get('required', False):
                        # Check if input is configured in sub_blocks
                        if input_name not in block.sub_blocks or not block.sub_blocks[input_name]:
                            errors.append(WorkflowValidationError(
                                block_id=str(block.id),
                                error_type="missing_required_input",
                                message=f"Block '{block.name}' is missing required input: {input_name}",
                                severity="error"
                            ))
            
            # Validate block configuration
            if not block.config:
                warnings.append(WorkflowValidationError(
                    block_id=str(block.id),
                    error_type="empty_config",
                    message=f"Block '{block.name}' has no configuration",
                    severity="warning"
                ))
            
            # Validate block type
            if not block.type:
                errors.append(WorkflowValidationError(
                    block_id=str(block.id),
                    error_type="invalid_block_type",
                    message=f"Block '{block.name}' has no type",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_edges(self, blocks: List[AgentBlock], edges: List[AgentEdge]) -> Tuple[List[WorkflowValidationError], List[WorkflowValidationError]]:
        """
        Validate edges.
        
        Args:
            blocks: List of blocks
            edges: List of edges
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[WorkflowValidationError] = []
        warnings: List[WorkflowValidationError] = []
        
        block_ids = {block.id for block in blocks}
        
        for edge in edges:
            # Validate source block exists
            if edge.source_block_id not in block_ids:
                errors.append(WorkflowValidationError(
                    edge_id=str(edge.id),
                    error_type="invalid_source_block",
                    message=f"Edge references non-existent source block: {edge.source_block_id}",
                    severity="error"
                ))
            
            # Validate target block exists
            if edge.target_block_id not in block_ids:
                errors.append(WorkflowValidationError(
                    edge_id=str(edge.id),
                    error_type="invalid_target_block",
                    message=f"Edge references non-existent target block: {edge.target_block_id}",
                    severity="error"
                ))
            
            # Validate no self-loops
            if edge.source_block_id == edge.target_block_id:
                errors.append(WorkflowValidationError(
                    edge_id=str(edge.id),
                    error_type="self_loop",
                    message="Edge creates a self-loop",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_graph_structure(self, blocks: List[AgentBlock], edges: List[AgentEdge]) -> Tuple[List[WorkflowValidationError], List[WorkflowValidationError]]:
        """
        Validate graph structure.
        
        Args:
            blocks: List of blocks
            edges: List of edges
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[WorkflowValidationError] = []
        warnings: List[WorkflowValidationError] = []
        
        if len(blocks) == 0:
            return errors, warnings
        
        # Build adjacency lists
        outgoing = {block.id: [] for block in blocks}
        incoming = {block.id: [] for block in blocks}
        
        for edge in edges:
            if edge.source_block_id in outgoing:
                outgoing[edge.source_block_id].append(edge.target_block_id)
            if edge.target_block_id in incoming:
                incoming[edge.target_block_id].append(edge.source_block_id)
        
        # Find start nodes (no incoming edges)
        start_nodes = [block_id for block_id, inc in incoming.items() if len(inc) == 0]
        
        if len(start_nodes) == 0:
            errors.append(WorkflowValidationError(
                error_type="no_start_node",
                message="Workflow has no start node (all blocks have incoming edges)",
                severity="error"
            ))
        elif len(start_nodes) > 1:
            warnings.append(WorkflowValidationError(
                error_type="multiple_start_nodes",
                message=f"Workflow has {len(start_nodes)} start nodes",
                severity="warning"
            ))
        
        # Find end nodes (no outgoing edges)
        end_nodes = [block_id for block_id, out in outgoing.items() if len(out) == 0]
        
        if len(end_nodes) == 0:
            warnings.append(WorkflowValidationError(
                error_type="no_end_node",
                message="Workflow has no end node (all blocks have outgoing edges)",
                severity="warning"
            ))
        
        return errors, warnings
    
    def _detect_cycles(self, blocks: List[AgentBlock], edges: List[AgentEdge]) -> List[WorkflowValidationError]:
        """
        Detect cycles in workflow graph using DFS.
        
        Args:
            blocks: List of blocks
            edges: List of edges
            
        Returns:
            List of errors
        """
        errors: List[WorkflowValidationError] = []
        
        if len(blocks) == 0:
            return errors
        
        # Build adjacency list
        graph = {block.id: [] for block in blocks}
        for edge in edges:
            if edge.source_block_id in graph:
                graph[edge.source_block_id].append(edge.target_block_id)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: UUID, path: List[UUID]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    
                    # Get block names for cycle
                    block_map = {block.id: block.name for block in blocks}
                    cycle_names = [block_map.get(block_id, str(block_id)) for block_id in cycle_path]
                    
                    errors.append(WorkflowValidationError(
                        error_type="cycle_detected",
                        message=f"Cycle detected in workflow: {' -> '.join(cycle_names)}",
                        severity="error"
                    ))
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for block in blocks:
            if block.id not in visited:
                if has_cycle(block.id, []):
                    break  # Stop after finding first cycle
        
        return errors
    
    def _detect_disconnected_nodes(self, blocks: List[AgentBlock], edges: List[AgentEdge]) -> List[WorkflowValidationError]:
        """
        Detect disconnected nodes in workflow graph.
        
        Args:
            blocks: List of blocks
            edges: List of edges
            
        Returns:
            List of warnings
        """
        warnings: List[WorkflowValidationError] = []
        
        if len(blocks) == 0:
            return warnings
        
        # Build adjacency list (undirected for connectivity check)
        graph = {block.id: set() for block in blocks}
        for edge in edges:
            if edge.source_block_id in graph and edge.target_block_id in graph:
                graph[edge.source_block_id].add(edge.target_block_id)
                graph[edge.target_block_id].add(edge.source_block_id)
        
        # BFS to find connected components
        visited = set()
        
        def bfs(start: UUID) -> Set[UUID]:
            component = set()
            queue = [start]
            
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                
                visited.add(node)
                component.add(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            return component
        
        # Find all connected components
        components = []
        for block in blocks:
            if block.id not in visited:
                component = bfs(block.id)
                components.append(component)
        
        # Report disconnected nodes
        if len(components) > 1:
            block_map = {block.id: block.name for block in blocks}
            
            for i, component in enumerate(components):
                if len(component) == 1:
                    block_id = list(component)[0]
                    block_name = block_map.get(block_id, str(block_id))
                    warnings.append(WorkflowValidationError(
                        block_id=str(block_id),
                        error_type="disconnected_node",
                        message=f"Block '{block_name}' is not connected to the workflow",
                        severity="warning"
                    ))
        
        return warnings
    
    def validate_block_inputs(self, block: AgentBlock) -> Tuple[bool, List[str]]:
        """
        Validate block inputs.
        
        Args:
            block: Block to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not block.inputs:
            return True, errors
        
        for input_name, input_config in block.inputs.items():
            if input_config.get('required', False):
                if input_name not in block.sub_blocks or not block.sub_blocks[input_name]:
                    errors.append(f"Missing required input: {input_name}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
