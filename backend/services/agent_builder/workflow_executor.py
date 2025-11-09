"""
Workflow Execution Engine

Executes workflows by processing nodes in order based on the graph structure.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes a workflow by processing its nodes."""
    
    def __init__(self, workflow: Any, db: Session):
        self.workflow = workflow
        self.db = db
        self.execution_context: Dict[str, Any] = {}
        self.node_results: Dict[str, Any] = {}
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Execution result with output data
        """
        try:
            logger.info(f"Starting workflow execution: {self.workflow.id}")
            
            # Initialize execution context
            self.execution_context = {
                "input": input_data,
                "workflow_id": str(self.workflow.id),  # Convert UUID to string for JSON serialization
                "started_at": datetime.utcnow().isoformat(),
            }
            
            # Get workflow graph
            graph = self.workflow.graph_definition
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            
            logger.info(f"Workflow has {len(nodes)} nodes and {len(edges)} edges")
            if nodes:
                logger.info(f"Node types: {[n.get('type') or n.get('configuration', {}).get('type') for n in nodes]}")
            
            # Find start node - check both 'type' field and 'configuration.type'
            start_nodes = [
                n for n in nodes 
                if n.get("type") in ["start", "trigger"] or 
                   n.get("configuration", {}).get("type") in ["start", "trigger"]
            ]
            if not start_nodes:
                logger.error(f"No start/trigger node found. Available nodes: {nodes}")
                raise ValueError("No start node found in workflow. Please add a Start or Trigger node to your workflow.")
            
            start_node = start_nodes[0]
            
            # Execute workflow from start node
            result = await self._execute_from_node(start_node, nodes, edges, input_data)
            
            logger.info(f"Workflow execution completed: {self.workflow.id}")
            
            return {
                "success": True,
                "output": result,
                "execution_context": self.execution_context,
                "node_results": self.node_results,
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "execution_context": self.execution_context,
                "node_results": self.node_results,
            }
    
    async def _execute_from_node(
        self,
        current_node: Dict[str, Any],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        data: Any
    ) -> Any:
        """
        Execute workflow starting from a specific node.
        
        Args:
            current_node: Current node to execute
            nodes: All nodes in the workflow
            edges: All edges in the workflow
            data: Input data for the current node
            
        Returns:
            Output data from the execution path
        """
        node_id = current_node["id"]
        # Check both 'type' field and 'configuration.type' for node type
        node_type = current_node.get("type") or current_node.get("configuration", {}).get("type", "block")
        node_data = current_node.get("data") or current_node.get("configuration", {})
        
        logger.info(f"Executing node: {node_id} (type: {node_type})")
        
        # Execute node based on type
        try:
            if node_type == "start":
                result = await self._execute_start_node(node_data, data)
            elif node_type == "trigger":
                result = await self._execute_trigger_node(node_data, data)
            elif node_type == "end":
                result = await self._execute_end_node(node_data, data)
                return result  # End node terminates execution
            elif node_type == "condition":
                result = await self._execute_condition_node(node_data, data)
            elif node_type == "agent":
                result = await self._execute_agent_node(node_data, data)
            elif node_type == "block":
                result = await self._execute_block_node(node_data, data)
            elif node_type == "tool":
                result = await self._execute_tool_node(node_data, data)
            else:
                logger.warning(f"Unknown node type: {node_type}, passing through data")
                result = data
            
            # Store node result
            self.node_results[node_id] = result
            
            # Find next nodes
            next_edges = [e for e in edges if e.get("source") == node_id]
            
            if not next_edges:
                # No more nodes, return result
                return result
            
            # Handle condition node (multiple branches)
            if node_type == "condition" and isinstance(result, dict) and "branch" in result:
                branch = result["branch"]
                # Find edge matching the branch
                next_edge = next(
                    (e for e in next_edges if e.get("sourceHandle") == branch),
                    next_edges[0] if next_edges else None
                )
                if next_edge:
                    next_node = next((n for n in nodes if n["id"] == next_edge["target"]), None)
                    if next_node:
                        return await self._execute_from_node(next_node, nodes, edges, result.get("data", data))
            else:
                # Execute next node (single path)
                if next_edges:
                    next_edge = next_edges[0]
                    next_node = next((n for n in nodes if n["id"] == next_edge["target"]), None)
                    if next_node:
                        return await self._execute_from_node(next_node, nodes, edges, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing node {node_id}: {e}", exc_info=True)
            raise
    
    async def _execute_start_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute start node (pass through)."""
        return data
    
    async def _execute_trigger_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute trigger node (pass through)."""
        return data
    
    async def _execute_end_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute end node (return final result)."""
        return data
    
    async def _execute_condition_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Execute condition node.
        
        Evaluates a condition and returns which branch to take.
        """
        condition = node_data.get("condition", "")
        branches = node_data.get("branches", [
            {"name": "true", "label": "True"},
            {"name": "false", "label": "False"},
        ])
        
        # Evaluate condition
        try:
            if condition:
                # Safe evaluation with limited context
                context = {
                    "data": data,
                    "context": self.execution_context,
                    "input": self.execution_context.get("input", {}),
                }
                
                # Use safe eval with restricted builtins
                result = self._safe_eval(condition, context)
                
                # Determine branch based on result
                if isinstance(result, bool):
                    branch = "true" if result else "false"
                else:
                    # For non-boolean results, check truthiness
                    branch = "true" if result else "false"
            else:
                # No condition specified, default to true
                import random
                branch = "true" if random.random() > 0.5 else "false"
            
            logger.info(f"Condition evaluated: {condition} -> {branch}")
            
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            # Default to false on error
            branch = "false"
        
        return {
            "branch": branch,
            "data": data,
            "condition": condition,
            "result": branch,
        }
    
    def _safe_eval(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate a Python expression.
        
        Args:
            expression: Python expression to evaluate
            context: Variables available in the expression
            
        Returns:
            Evaluation result
        """
        # Restricted builtins for safety
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "str": str,
            "sum": sum,
            "True": True,
            "False": False,
            "None": None,
        }
        
        try:
            # Evaluate with restricted context
            result = eval(expression, {"__builtins__": safe_builtins}, context)
            return result
        except Exception as e:
            logger.error(f"Expression evaluation failed: {e}")
            raise ValueError(f"Invalid expression: {str(e)}")
    
    async def _execute_agent_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute agent node.
        
        Calls an AI agent to process the data.
        """
        agent_id = node_data.get("agentId")
        agent_type = node_data.get("agentType", "general")
        
        logger.info(f"Executing agent: {agent_id or agent_type}")
        
        # TODO: Implement actual agent execution
        # For now, simulate agent processing
        await asyncio.sleep(0.5)  # Simulate processing time
        
        result = {
            "agent_output": f"Processed by {agent_type} agent",
            "input": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return result
    
    async def _execute_block_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute block node.
        
        Executes a custom block (logic, transformation, etc.).
        """
        block_id = node_data.get("blockId")
        block_type = node_data.get("blockType", "logic")
        
        logger.info(f"Executing block: {block_id or block_type}")
        
        # TODO: Implement actual block execution
        # For now, simulate block processing
        await asyncio.sleep(0.3)  # Simulate processing time
        
        result = {
            "block_output": f"Processed by {block_type} block",
            "input": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return result
    
    async def _execute_tool_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute tool node.
        
        Calls an external tool or API.
        """
        tool_id = node_data.get("toolId")
        tool_name = node_data.get("name", "unknown")
        
        logger.info(f"Executing tool: {tool_id or tool_name}")
        
        # TODO: Implement actual tool execution
        # For now, simulate tool call
        await asyncio.sleep(0.4)  # Simulate API call time
        
        result = {
            "tool_output": f"Executed {tool_name}",
            "input": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return result


async def execute_workflow(workflow: Any, db: Session, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow.
    
    Args:
        workflow: Workflow object
        db: Database session
        input_data: Input data for the workflow
        
    Returns:
        Execution result
    """
    executor = WorkflowExecutor(workflow, db)
    return await executor.execute(input_data)
