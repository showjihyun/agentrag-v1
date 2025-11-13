"""
Workflow Generator Service
AI-powered workflow generation from natural language descriptions
"""

from typing import Dict, Any, List, Optional
import json
from backend.services.llm_manager import LLMManager
from backend.config import settings
import uuid


class WorkflowGenerator:
    """Generate workflows from natural language descriptions using LLM"""
    
    def __init__(self):
        # Use default LLM from settings
        self.llm_manager = LLMManager()
        self.timeout = 60  # Increase timeout for workflow generation
        
        # Available node types and their descriptions
        self.node_types = {
            "start": "Entry point of the workflow",
            "end": "Exit point of the workflow",
            "agent": "AI agent that processes data using LLM",
            "block": "Reusable block/function",
            "condition": "Conditional branching (if/else)",
            "switch": "Multi-way branching based on value",
            "loop": "Iterate over items",
            "parallel": "Execute multiple paths simultaneously",
            "delay": "Wait for specified duration",
            "merge": "Combine multiple paths",
            "http_request": "Make HTTP API calls",
            "code": "Execute custom Python/JavaScript code",
            "slack": "Send Slack messages",
            "discord": "Send Discord messages",
            "email": "Send emails",
            "google_drive": "Google Drive operations",
            "s3": "AWS S3 operations",
            "database": "Database queries",
            "memory": "Store/retrieve data from memory",
            "human_approval": "Request human approval",
            "consensus": "Multi-agent consensus",
            "manager_agent": "Hierarchical agent management",
            "webhook_trigger": "Trigger via webhook",
            "schedule_trigger": "Trigger on schedule",
            "webhook_response": "Send webhook response",
        }
    
    async def generate_workflow(
        self,
        description: str,
        user_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate workflow from natural language description
        
        Args:
            description: Natural language description of desired workflow
            user_id: User ID for tracking
            additional_context: Additional context (existing workflows, preferences)
        
        Returns:
            Workflow definition with nodes and edges
        """
        
        # Build prompt for LLM
        prompt = self._build_generation_prompt(description, additional_context)
        
        # Call LLM with messages format and increased timeout
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Use a simpler, more direct approach for faster generation
        try:
            response = await self.llm_manager.generate(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=1500,  # Reduced for faster generation
            )
        except Exception as e:
            # If LLM fails, return a basic workflow structure
            logger.warning(f"LLM generation failed: {str(e)}, returning basic workflow")
            return self._create_basic_workflow(description)
        
        # Parse LLM response
        workflow_def = self._parse_llm_response(response)
        
        # Validate and enhance workflow
        workflow_def = self._validate_and_enhance(workflow_def, description)
        
        # Add metadata
        workflow_def["metadata"] = {
            "generated_from": description,
            "user_id": user_id,
            "generator_version": "1.0.0",
        }
        
        return workflow_def
    
    def _build_generation_prompt(
        self,
        description: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for workflow generation"""
        
        node_types_desc = "\n".join([
            f"- {name}: {desc}" for name, desc in self.node_types.items()
        ])
        
        examples = self._get_example_workflows()
        
        prompt = f"""Create a workflow from this description: "{description}"

Available nodes: start, end, agent, slack, email, webhook_trigger, http_request, condition, database

Output JSON format:
{{
  "name": "Workflow Name",
  "description": "Brief description",
  "nodes": [
    {{"id": "1", "type": "start", "data": {{"label": "Start"}}}},
    {{"id": "2", "type": "agent", "data": {{"label": "Process"}}}},
    {{"id": "3", "type": "end", "data": {{"label": "End"}}}}
  ],
  "edges": [
    {{"source": "1", "target": "2"}},
    {{"source": "2", "target": "3"}}
  ]
}}

Generate workflow JSON:"""
        
        return prompt
    
    def _create_basic_workflow(self, description: str) -> Dict[str, Any]:
        """
        Create a basic workflow when LLM generation fails
        """
        import uuid
        
        # Analyze description for keywords
        desc_lower = description.lower()
        
        nodes = [
            {
                "id": str(uuid.uuid4()),
                "type": "start",
                "position": {"x": 150, "y": 100},
                "data": {"label": "Start"}
            }
        ]
        
        edges = []
        last_node_id = nodes[0]["id"]
        y_position = 300
        
        # Add nodes based on keywords
        if "slack" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "type": "slack",
                "position": {"x": 150, "y": y_position},
                "data": {"label": "Send Slack Message", "channel": "#general"}
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source": last_node_id,
                "target": node_id,
                "type": "custom"
            })
            last_node_id = node_id
            y_position += 200
            
        elif "email" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "type": "email",
                "position": {"x": 150, "y": y_position},
                "data": {"label": "Send Email"}
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source": last_node_id,
                "target": node_id,
                "type": "custom"
            })
            last_node_id = node_id
            y_position += 200
            
        elif "webhook" in desc_lower or "trigger" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "type": "webhook_trigger",
                "position": {"x": 150, "y": y_position},
                "data": {"label": "Webhook Trigger"}
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source": last_node_id,
                "target": node_id,
                "type": "custom"
            })
            last_node_id = node_id
            y_position += 200
        else:
            # Default: add an agent node
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "type": "agent",
                "position": {"x": 150, "y": y_position},
                "data": {"label": "Process with AI"}
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source": last_node_id,
                "target": node_id,
                "type": "custom"
            })
            last_node_id = node_id
            y_position += 200
        
        # Add end node
        end_node_id = str(uuid.uuid4())
        nodes.append({
            "id": end_node_id,
            "type": "end",
            "position": {"x": 150, "y": y_position},
            "data": {"label": "End"}
        })
        edges.append({
            "id": str(uuid.uuid4()),
            "source": last_node_id,
            "target": end_node_id,
            "type": "custom"
        })
        
        return {
            "name": "Generated Workflow",
            "description": description,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "generated_from": description,
                "fallback": True,
                "note": "Basic workflow created due to LLM timeout"
            }
        }
    
    def _get_example_workflows(self) -> str:
        """Get example workflows for few-shot learning"""
        
        examples = [
            {
                "description": "Send a Slack notification when a customer submits feedback",
                "workflow": {
                    "name": "Customer Feedback Notification",
                    "nodes": [
                        {"id": "start", "type": "start", "data": {"label": "Start"}},
                        {"id": "webhook", "type": "webhook_trigger", "data": {"label": "Receive Feedback"}},
                        {"id": "slack", "type": "slack", "data": {"label": "Notify Team", "channel": "#feedback"}},
                        {"id": "end", "type": "end", "data": {"label": "End"}},
                    ],
                    "edges": [
                        {"source": "start", "target": "webhook"},
                        {"source": "webhook", "target": "slack"},
                        {"source": "slack", "target": "end"},
                    ]
                }
            },
            {
                "description": "Analyze sentiment and route to appropriate team",
                "workflow": {
                    "name": "Sentiment-Based Routing",
                    "nodes": [
                        {"id": "start", "type": "start", "data": {"label": "Start"}},
                        {"id": "agent", "type": "agent", "data": {"label": "Analyze Sentiment"}},
                        {"id": "switch", "type": "switch", "data": {"label": "Route by Sentiment"}},
                        {"id": "positive", "type": "slack", "data": {"label": "Positive Team"}},
                        {"id": "negative", "type": "human_approval", "data": {"label": "Escalate"}},
                        {"id": "end", "type": "end", "data": {"label": "End"}},
                    ],
                    "edges": [
                        {"source": "start", "target": "agent"},
                        {"source": "agent", "target": "switch"},
                        {"source": "switch", "target": "positive"},
                        {"source": "switch", "target": "negative"},
                        {"source": "positive", "target": "end"},
                        {"source": "negative", "target": "end"},
                    ]
                }
            }
        ]
        
        return json.dumps(examples, indent=2)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract workflow definition"""
        
        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            workflow_def = json.loads(json_str)
            return workflow_def
            
        except json.JSONDecodeError as e:
            # Fallback: create a simple workflow
            return {
                "name": "Generated Workflow",
                "description": "Auto-generated workflow",
                "nodes": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start"}
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "end",
                        "position": {"x": 100, "y": 300},
                        "data": {"label": "End"}
                    }
                ],
                "edges": [],
                "error": f"Failed to parse LLM response: {str(e)}"
            }
    
    def _validate_and_enhance(
        self,
        workflow_def: Dict[str, Any],
        original_description: str
    ) -> Dict[str, Any]:
        """Validate and enhance the generated workflow"""
        
        # Ensure required fields
        if "name" not in workflow_def:
            workflow_def["name"] = "Generated Workflow"
        
        if "description" not in workflow_def:
            workflow_def["description"] = original_description
        
        if "nodes" not in workflow_def:
            workflow_def["nodes"] = []
        
        if "edges" not in workflow_def:
            workflow_def["edges"] = []
        
        # Ensure all nodes have IDs
        for node in workflow_def["nodes"]:
            if "id" not in node:
                node["id"] = str(uuid.uuid4())
        
        # Ensure all edges have IDs
        for edge in workflow_def["edges"]:
            if "id" not in edge:
                edge["id"] = str(uuid.uuid4())
            if "type" not in edge:
                edge["type"] = "custom"
        
        # Auto-layout nodes if positions are missing
        workflow_def = self._auto_layout_nodes(workflow_def)
        
        # Validate node types
        valid_types = set(self.node_types.keys())
        for node in workflow_def["nodes"]:
            if node.get("type") not in valid_types:
                node["type"] = "block"  # Default to block
        
        return workflow_def
    
    def _auto_layout_nodes(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-layout nodes in a vertical flow"""
        
        nodes = workflow_def["nodes"]
        edges = workflow_def["edges"]
        
        # Build adjacency list
        graph = {node["id"]: [] for node in nodes}
        for edge in edges:
            if edge["source"] in graph:
                graph[edge["source"]].append(edge["target"])
        
        # Find start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            start_nodes = [nodes[0]] if nodes else []
        
        # BFS to assign levels
        levels = {}
        if start_nodes:
            queue = [(start_nodes[0]["id"], 0)]
            visited = set()
            
            while queue:
                node_id, level = queue.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)
                levels[node_id] = level
                
                for neighbor in graph.get(node_id, []):
                    if neighbor not in visited:
                        queue.append((neighbor, level + 1))
        
        # Assign positions
        level_counts = {}
        for node in nodes:
            node_id = node["id"]
            level = levels.get(node_id, 0)
            
            if level not in level_counts:
                level_counts[level] = 0
            
            x = 150 + level_counts[level] * 300
            y = 100 + level * 200
            
            node["position"] = {"x": x, "y": y}
            level_counts[level] += 1
        
        return workflow_def
    
    async def suggest_improvements(
        self,
        workflow_def: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest improvements for an existing workflow"""
        
        suggestions = []
        
        # Check for missing error handling
        has_error_handling = any(
            node.get("type") in ["condition", "try_catch"]
            for node in workflow_def.get("nodes", [])
        )
        
        if not has_error_handling:
            suggestions.append({
                "type": "error_handling",
                "severity": "medium",
                "message": "Consider adding error handling with condition or try-catch nodes",
                "action": "Add error handling node"
            })
        
        # Check for missing human approval in critical paths
        has_external_actions = any(
            node.get("type") in ["email", "slack", "discord", "database"]
            for node in workflow_def.get("nodes", [])
        )
        
        has_approval = any(
            node.get("type") == "human_approval"
            for node in workflow_def.get("nodes", [])
        )
        
        if has_external_actions and not has_approval:
            suggestions.append({
                "type": "approval",
                "severity": "low",
                "message": "Consider adding human approval before external actions",
                "action": "Add human approval node"
            })
        
        # Check for parallel execution opportunities
        nodes = workflow_def.get("nodes", [])
        edges = workflow_def.get("edges", [])
        
        # Find nodes that could be parallelized
        # (nodes with same source but no dependencies on each other)
        
        return suggestions
    
    async def optimize_workflow(
        self,
        workflow_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize workflow for performance and cost"""
        
        optimized = workflow_def.copy()
        
        # Identify parallel execution opportunities
        # Merge redundant nodes
        # Optimize LLM calls (batching, caching)
        
        return optimized
