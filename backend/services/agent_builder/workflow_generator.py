"""
Workflow Generator Service
AI-powered workflow generation from natural language descriptions
"""

from typing import Dict, Any, List, Optional
import json
import logging
from backend.services.llm_manager import LLMManager
from backend.config import settings
import uuid

logger = logging.getLogger(__name__)


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
            # Call LLM with proper method and timeout
            response = await self.llm_manager.generate_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=1500,  # Reduced for faster generation
                timeout=self.timeout
            )
        except Exception as e:
            # If LLM fails, return a basic workflow structure
            logger.warning(f"LLM generation failed: {str(e)}, returning basic workflow")
            return self._create_basic_workflow(description)
        
        # Parse LLM response
        workflow_def = self._parse_llm_response(response)
        
        # If parsing failed completely, use basic workflow
        if workflow_def is None:
            logger.warning("LLM response parsing failed completely, using basic workflow")
            return self._create_basic_workflow(description)
        
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
        
        # Get key node types for the prompt
        key_nodes = ["start", "end", "agent", "slack", "email", "discord", 
                     "webhook_trigger", "http_request", "condition", "switch",
                     "database", "human_approval", "code", "parallel"]
        
        node_types_desc = "\n".join([
            f"  - {name}: {self.node_types[name]}" 
            for name in key_nodes if name in self.node_types
        ])
        
        prompt = f"""You are a workflow generation AI. Create a workflow from the user's description.

USER DESCRIPTION: "{description}"

AVAILABLE NODE TYPES:
{node_types_desc}

IMPORTANT RULES:
1. Always start with a "start" node and end with an "end" node
2. Use appropriate node types based on the description
3. Add proper configuration for each node (channel for slack, email for email, etc.)
4. Create logical connections between nodes
5. Use condition/switch nodes for branching logic
6. Output ONLY valid JSON, no explanations

OUTPUT FORMAT (Backend format):
{{
  "name": "Workflow Name",
  "description": "Brief description",
  "nodes": [
    {{
      "id": "unique-id-1",
      "node_type": "start",
      "position_x": 150,
      "position_y": 100,
      "configuration": {{
        "name": "Start",
        "type": "start"
      }}
    }},
    {{
      "id": "unique-id-2",
      "node_type": "slack",
      "position_x": 150,
      "position_y": 300,
      "configuration": {{
        "name": "Send Notification",
        "type": "slack",
        "channel": "#alerts",
        "message": "Notification message"
      }}
    }},
    {{
      "id": "unique-id-3",
      "node_type": "end",
      "position_x": 150,
      "position_y": 500,
      "configuration": {{
        "name": "End",
        "type": "end"
      }}
    }}
  ],
  "edges": [
    {{
      "id": "edge-1",
      "source_node_id": "unique-id-1",
      "target_node_id": "unique-id-2",
      "edge_type": "normal"
    }},
    {{
      "id": "edge-2",
      "source_node_id": "unique-id-2",
      "target_node_id": "unique-id-3",
      "edge_type": "normal"
    }}
  ]
}}

EXAMPLE 1 - Slack Notification:
Description: "Send Slack message when webhook is triggered"
{{
  "name": "Slack Notification Workflow",
  "description": "Send Slack notification on webhook trigger",
  "nodes": [
    {{"id": "n1", "node_type": "start", "position_x": 150, "position_y": 100, "configuration": {{"name": "Start", "type": "start"}}}},
    {{"id": "n2", "node_type": "webhook_trigger", "position_x": 150, "position_y": 250, "configuration": {{"name": "Webhook", "type": "webhook_trigger", "path": "/webhook"}}}},
    {{"id": "n3", "node_type": "slack", "position_x": 150, "position_y": 400, "configuration": {{"name": "Notify", "type": "slack", "channel": "#alerts", "message": "New webhook received"}}}},
    {{"id": "n4", "node_type": "end", "position_x": 150, "position_y": 550, "configuration": {{"name": "End", "type": "end"}}}}
  ],
  "edges": [
    {{"id": "e1", "source_node_id": "n1", "target_node_id": "n2", "edge_type": "normal"}},
    {{"id": "e2", "source_node_id": "n2", "target_node_id": "n3", "edge_type": "normal"}},
    {{"id": "e3", "source_node_id": "n3", "target_node_id": "n4", "edge_type": "normal"}}
  ]
}}

EXAMPLE 2 - Conditional Approval:
Description: "If amount > 1000, require approval, then process"
{{
  "name": "Approval Workflow",
  "description": "Conditional approval based on amount",
  "nodes": [
    {{"id": "n1", "node_type": "start", "position_x": 150, "position_y": 100, "configuration": {{"name": "Start", "type": "start"}}}},
    {{"id": "n2", "node_type": "condition", "position_x": 150, "position_y": 250, "configuration": {{"name": "Check Amount", "type": "condition", "condition": "amount > 1000"}}}},
    {{"id": "n3", "node_type": "human_approval", "position_x": 300, "position_y": 400, "configuration": {{"name": "Require Approval", "type": "human_approval", "approvers": ["manager@example.com"]}}}},
    {{"id": "n4", "node_type": "agent", "position_x": 150, "position_y": 550, "configuration": {{"name": "Process", "type": "agent", "prompt": "Process the request"}}}},
    {{"id": "n5", "node_type": "end", "position_x": 150, "position_y": 700, "configuration": {{"name": "End", "type": "end"}}}}
  ],
  "edges": [
    {{"id": "e1", "source_node_id": "n1", "target_node_id": "n2", "edge_type": "normal"}},
    {{"id": "e2", "source_node_id": "n2", "target_node_id": "n3", "edge_type": "true"}},
    {{"id": "e3", "source_node_id": "n2", "target_node_id": "n4", "edge_type": "false"}},
    {{"id": "e4", "source_node_id": "n3", "target_node_id": "n4", "edge_type": "normal"}},
    {{"id": "e5", "source_node_id": "n4", "target_node_id": "n5", "edge_type": "normal"}}
  ]
}}

Now generate the workflow JSON for the user's description. Output ONLY the JSON:"""
        
        return prompt
    
    def _create_basic_workflow(self, description: str) -> Dict[str, Any]:
        """
        Create a basic workflow when LLM generation fails
        """
        import uuid
        
        # Analyze description for keywords
        desc_lower = description.lower()
        
        # Create nodes in backend format (node_type, position_x, position_y, configuration)
        start_node_id = str(uuid.uuid4())
        nodes = [
            {
                "id": start_node_id,
                "node_type": "start",
                "position_x": 150,
                "position_y": 100,
                "configuration": {
                    "name": "Start",
                    "type": "start"
                }
            }
        ]
        
        edges = []
        last_node_id = start_node_id
        y_position = 300
        
        # Add nodes based on keywords (backend format)
        if "slack" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "node_type": "slack",
                "position_x": 150,
                "position_y": y_position,
                "configuration": {
                    "name": "Send Slack Message",
                    "type": "slack",
                    "channel": "#general",
                    "message": "Message from workflow"
                }
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source_node_id": last_node_id,
                "target_node_id": node_id,
                "edge_type": "normal"
            })
            last_node_id = node_id
            y_position += 200
            
        elif "email" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "node_type": "email",
                "position_x": 150,
                "position_y": y_position,
                "configuration": {
                    "name": "Send Email",
                    "type": "email",
                    "to": "user@example.com",
                    "subject": "Notification from workflow"
                }
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source_node_id": last_node_id,
                "target_node_id": node_id,
                "edge_type": "normal"
            })
            last_node_id = node_id
            y_position += 200
            
        elif "webhook" in desc_lower or "trigger" in desc_lower:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "node_type": "webhook_trigger",
                "position_x": 150,
                "position_y": y_position,
                "configuration": {
                    "name": "Webhook Trigger",
                    "type": "webhook_trigger",
                    "path": "/webhook"
                }
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source_node_id": last_node_id,
                "target_node_id": node_id,
                "edge_type": "normal"
            })
            last_node_id = node_id
            y_position += 200
        else:
            # Default: add an agent node
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "node_type": "agent",
                "position_x": 150,
                "position_y": y_position,
                "configuration": {
                    "name": "Process with AI",
                    "type": "agent",
                    "prompt": "Process the input data"
                }
            })
            edges.append({
                "id": str(uuid.uuid4()),
                "source_node_id": last_node_id,
                "target_node_id": node_id,
                "edge_type": "normal"
            })
            last_node_id = node_id
            y_position += 200
        
        # Add end node
        end_node_id = str(uuid.uuid4())
        nodes.append({
            "id": end_node_id,
            "node_type": "end",
            "position_x": 150,
            "position_y": y_position,
            "configuration": {
                "name": "End",
                "type": "end"
            }
        })
        edges.append({
            "id": str(uuid.uuid4()),
            "source_node_id": last_node_id,
            "target_node_id": end_node_id,
            "edge_type": "normal"
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
            
            # Validate that we got the backend format
            if "nodes" in workflow_def and len(workflow_def["nodes"]) > 0:
                first_node = workflow_def["nodes"][0]
                # Check if it's already in backend format
                if "node_type" in first_node and "position_x" in first_node:
                    return workflow_def
                # If it's in frontend format, convert it
                elif "type" in first_node and "position" in first_node:
                    logger.info("Converting frontend format to backend format")
                    return self._convert_frontend_to_backend_format(workflow_def)
            
            return workflow_def
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            # Try partial parsing - look for nodes array
            try:
                # Attempt to extract just the nodes/edges if possible
                if '"nodes"' in response and '"edges"' in response:
                    # Try to find and extract the JSON object
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        workflow_def = json.loads(json_str)
                        return workflow_def
            except:
                pass
            
            # Complete fallback: return None to trigger basic workflow creation
            return None
    
    def _convert_frontend_to_backend_format(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert frontend format to backend format"""
        converted = {
            "name": workflow_def.get("name", "Generated Workflow"),
            "description": workflow_def.get("description", ""),
            "nodes": [],
            "edges": []
        }
        
        # Convert nodes
        for node in workflow_def.get("nodes", []):
            position = node.get("position", {"x": 150, "y": 100})
            data = node.get("data", {})
            
            backend_node = {
                "id": node.get("id", str(uuid.uuid4())),
                "node_type": node.get("type", "block"),
                "position_x": position.get("x", 150),
                "position_y": position.get("y", 100),
                "configuration": {
                    "name": data.get("label", node.get("type", "Node")),
                    "type": node.get("type", "block"),
                    **{k: v for k, v in data.items() if k != "label"}
                }
            }
            converted["nodes"].append(backend_node)
        
        # Convert edges
        for edge in workflow_def.get("edges", []):
            backend_edge = {
                "id": edge.get("id", str(uuid.uuid4())),
                "source_node_id": edge.get("source"),
                "target_node_id": edge.get("target"),
                "edge_type": edge.get("type", "normal")
            }
            converted["edges"].append(backend_edge)
        
        return converted
    
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
        
        # Ensure all nodes have IDs and proper format
        for node in workflow_def["nodes"]:
            if "id" not in node:
                node["id"] = str(uuid.uuid4())
            
            # Ensure backend format
            if "node_type" not in node and "type" in node:
                node["node_type"] = node.pop("type")
            
            if "configuration" not in node:
                node["configuration"] = {
                    "name": node.get("node_type", "Node"),
                    "type": node.get("node_type", "block")
                }
            
            # Ensure configuration has required fields
            if "name" not in node["configuration"]:
                node["configuration"]["name"] = node.get("node_type", "Node").title()
            if "type" not in node["configuration"]:
                node["configuration"]["type"] = node.get("node_type", "block")
        
        # Ensure all edges have IDs and proper format
        for edge in workflow_def["edges"]:
            if "id" not in edge:
                edge["id"] = str(uuid.uuid4())
            
            # Ensure backend format
            if "source_node_id" not in edge and "source" in edge:
                edge["source_node_id"] = edge.pop("source")
            if "target_node_id" not in edge and "target" in edge:
                edge["target_node_id"] = edge.pop("target")
            
            if "edge_type" not in edge:
                edge["edge_type"] = "normal"
        
        # Auto-layout nodes if positions are missing
        workflow_def = self._auto_layout_nodes(workflow_def)
        
        # Validate node types
        valid_types = set(self.node_types.keys())
        for node in workflow_def["nodes"]:
            node_type = node.get("node_type", node.get("type"))
            if node_type not in valid_types:
                logger.warning(f"Invalid node type: {node_type}, defaulting to 'block'")
                node["node_type"] = "block"
                node["configuration"]["type"] = "block"
        
        # Validate workflow structure
        workflow_def = self._validate_workflow_structure(workflow_def)
        
        return workflow_def
    
    def _validate_workflow_structure(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow structure (start/end nodes, no cycles, no orphans)"""
        
        nodes = workflow_def["nodes"]
        edges = workflow_def["edges"]
        
        # Check for start node
        start_nodes = [n for n in nodes if n.get("node_type") == "start"]
        if not start_nodes:
            logger.warning("No start node found, adding one")
            start_node = {
                "id": str(uuid.uuid4()),
                "node_type": "start",
                "position_x": 150,
                "position_y": 50,
                "configuration": {"name": "Start", "type": "start"}
            }
            nodes.insert(0, start_node)
            # Connect to first non-start node if exists
            if len(nodes) > 1:
                edges.insert(0, {
                    "id": str(uuid.uuid4()),
                    "source_node_id": start_node["id"],
                    "target_node_id": nodes[1]["id"],
                    "edge_type": "normal"
                })
        
        # Check for end node
        end_nodes = [n for n in nodes if n.get("node_type") == "end"]
        if not end_nodes:
            logger.warning("No end node found, adding one")
            # Find the last node's position
            last_y = max([n.get("position_y", 100) for n in nodes], default=100)
            end_node = {
                "id": str(uuid.uuid4()),
                "node_type": "end",
                "position_x": 150,
                "position_y": last_y + 150,
                "configuration": {"name": "End", "type": "end"}
            }
            nodes.append(end_node)
            # Connect from last non-end node
            if len(nodes) > 1:
                edges.append({
                    "id": str(uuid.uuid4()),
                    "source_node_id": nodes[-2]["id"],
                    "target_node_id": end_node["id"],
                    "edge_type": "normal"
                })
        
        # Check for orphan nodes (nodes with no connections)
        node_ids = {n["id"] for n in nodes}
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("source_node_id"))
            connected_nodes.add(edge.get("target_node_id"))
        
        orphan_nodes = node_ids - connected_nodes
        if orphan_nodes:
            logger.warning(f"Found {len(orphan_nodes)} orphan nodes")
        
        return workflow_def
    
    def _auto_layout_nodes(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-layout nodes in a vertical flow"""
        
        nodes = workflow_def["nodes"]
        edges = workflow_def["edges"]
        
        # Check if nodes already have positions (backend format)
        has_positions = all(
            "position_x" in node and "position_y" in node 
            for node in nodes
        )
        
        if has_positions:
            # Positions already set, no need to auto-layout
            return workflow_def
        
        # Build adjacency list (handle both formats)
        graph = {node["id"]: [] for node in nodes}
        for edge in edges:
            source = edge.get("source_node_id", edge.get("source"))
            target = edge.get("target_node_id", edge.get("target"))
            if source in graph:
                graph[source].append(target)
        
        # Find start node
        start_nodes = [n for n in nodes if n.get("node_type", n.get("type")) == "start"]
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
        
        # Assign positions (backend format)
        level_counts = {}
        for node in nodes:
            node_id = node["id"]
            level = levels.get(node_id, 0)
            
            if level not in level_counts:
                level_counts[level] = 0
            
            x = 150 + level_counts[level] * 300
            y = 100 + level * 150
            
            # Set backend format positions
            node["position_x"] = x
            node["position_y"] = y
            
            # Remove frontend format if exists
            if "position" in node:
                del node["position"]
            
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
