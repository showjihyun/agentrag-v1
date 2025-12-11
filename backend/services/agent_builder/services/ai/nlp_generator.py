"""
NLP-based Workflow Generator

Converts natural language descriptions into executable workflows.
Uses LLM to understand intent and generate appropriate workflow structures.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkflowIntent(BaseModel):
    """Parsed workflow intent from natural language"""
    
    workflow_type: str = Field(..., description="chatflow or agentflow")
    name: str = Field(..., description="Generated workflow name")
    description: str = Field(..., description="Workflow description")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Generated nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Generated edges")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow variables")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")


class NLPWorkflowGenerator:
    """Generate workflows from natural language descriptions"""
    
    def __init__(self, llm_manager=None):
        self.llm_manager = llm_manager
        self.node_templates = self._init_node_templates()
        
    def _init_node_templates(self) -> Dict[str, Dict]:
        """Initialize node templates for common patterns"""
        return {
            "start": {
                "type": "start",
                "data": {"label": "Start"}
            },
            "end": {
                "type": "end",
                "data": {"label": "End"}
            },
            "llm": {
                "type": "llm",
                "data": {
                    "label": "LLM",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "systemPrompt": "",
                    "userPrompt": ""
                }
            },
            "http": {
                "type": "http",
                "data": {
                    "label": "HTTP Request",
                    "method": "GET",
                    "url": "",
                    "headers": {}
                }
            },
            "condition": {
                "type": "condition",
                "data": {
                    "label": "Condition",
                    "condition": ""
                }
            },
            "code": {
                "type": "code",
                "data": {
                    "label": "Code",
                    "language": "python",
                    "code": ""
                }
            },
            "tool": {
                "type": "tool",
                "data": {
                    "label": "Tool",
                    "toolName": "",
                    "parameters": {}
                }
            }
        }
    
    async def generate_from_text(
        self,
        description: str,
        user_id: int,
        context: Optional[Dict] = None
    ) -> WorkflowIntent:
        """
        Generate workflow from natural language description
        
        Args:
            description: Natural language workflow description
            user_id: User ID for personalization
            context: Additional context (existing workflows, preferences)
            
        Returns:
            WorkflowIntent with generated workflow structure
        """
        try:
            # Parse intent using LLM
            intent = await self._parse_intent(description, context)
            
            # Generate workflow structure
            workflow = await self._generate_workflow_structure(intent)
            
            # Validate and optimize
            workflow = self._validate_workflow(workflow)
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to generate workflow from text: {e}")
            raise
    
    async def _parse_intent(
        self,
        description: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Parse natural language to extract workflow intent"""
        
        system_prompt = """You are a workflow generation expert. Analyze the user's description and extract:
1. Workflow type (chatflow for conversational, agentflow for task automation)
2. Required nodes and their types
3. Data flow between nodes
4. Variables and parameters needed

Respond in JSON format with:
{
    "workflow_type": "chatflow|agentflow",
    "name": "workflow name",
    "description": "clear description",
    "steps": [
        {
            "type": "node_type",
            "purpose": "what this step does",
            "inputs": ["input1"],
            "outputs": ["output1"]
        }
    ],
    "confidence": 0.0-1.0
}"""
        
        user_prompt = f"""Generate a workflow for this description:

{description}

{f"Context: {json.dumps(context, indent=2)}" if context else ""}

Analyze and provide the workflow structure."""
        
        if self.llm_manager:
            response = await self.llm_manager.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response)
        else:
            # Fallback: simple pattern matching
            return self._simple_intent_parsing(description)
    
    def _simple_intent_parsing(self, description: str) -> Dict:
        """Simple rule-based intent parsing as fallback"""
        
        description_lower = description.lower()
        
        # Detect workflow type
        if any(word in description_lower for word in ["chat", "conversation", "talk", "ask"]):
            workflow_type = "chatflow"
        else:
            workflow_type = "agentflow"
        
        # Detect required nodes
        steps = []
        
        if any(word in description_lower for word in ["api", "http", "request", "fetch"]):
            steps.append({
                "type": "http",
                "purpose": "Make HTTP request",
                "inputs": ["url"],
                "outputs": ["response"]
            })
        
        if any(word in description_lower for word in ["llm", "ai", "generate", "answer"]):
            steps.append({
                "type": "llm",
                "purpose": "Generate AI response",
                "inputs": ["prompt"],
                "outputs": ["response"]
            })
        
        if any(word in description_lower for word in ["if", "condition", "check", "when"]):
            steps.append({
                "type": "condition",
                "purpose": "Check condition",
                "inputs": ["value"],
                "outputs": ["true_branch", "false_branch"]
            })
        
        if any(word in description_lower for word in ["code", "script", "calculate", "process"]):
            steps.append({
                "type": "code",
                "purpose": "Execute code",
                "inputs": ["data"],
                "outputs": ["result"]
            })
        
        # If no specific nodes detected, default to simple LLM flow
        if not steps:
            steps.append({
                "type": "llm",
                "purpose": "Process request",
                "inputs": ["input"],
                "outputs": ["output"]
            })
        
        return {
            "workflow_type": workflow_type,
            "name": description[:50],
            "description": description,
            "steps": steps,
            "confidence": 0.6
        }
    
    async def _generate_workflow_structure(self, intent: Dict) -> WorkflowIntent:
        """Generate complete workflow structure from intent"""
        
        nodes = []
        edges = []
        node_id_counter = 0
        
        # Add start node
        start_node = {
            "id": f"node_{node_id_counter}",
            **self.node_templates["start"],
            "position": {"x": 100, "y": 100}
        }
        nodes.append(start_node)
        prev_node_id = start_node["id"]
        node_id_counter += 1
        
        # Generate nodes from steps
        y_position = 200
        for step in intent.get("steps", []):
            node_type = step["type"]
            
            if node_type in self.node_templates:
                node = {
                    "id": f"node_{node_id_counter}",
                    **self.node_templates[node_type],
                    "position": {"x": 100, "y": y_position}
                }
                
                # Customize node data based on purpose
                node["data"]["label"] = step.get("purpose", node_type.title())
                
                nodes.append(node)
                
                # Add edge from previous node
                edges.append({
                    "id": f"edge_{len(edges)}",
                    "source": prev_node_id,
                    "target": node["id"],
                    "type": "default"
                })
                
                prev_node_id = node["id"]
                node_id_counter += 1
                y_position += 150
        
        # Add end node
        end_node = {
            "id": f"node_{node_id_counter}",
            **self.node_templates["end"],
            "position": {"x": 100, "y": y_position}
        }
        nodes.append(end_node)
        
        # Connect last node to end
        edges.append({
            "id": f"edge_{len(edges)}",
            "source": prev_node_id,
            "target": end_node["id"],
            "type": "default"
        })
        
        return WorkflowIntent(
            workflow_type=intent["workflow_type"],
            name=intent["name"],
            description=intent["description"],
            nodes=nodes,
            edges=edges,
            confidence=intent.get("confidence", 0.7)
        )
    
    def _validate_workflow(self, workflow: WorkflowIntent) -> WorkflowIntent:
        """Validate and optimize generated workflow"""
        
        # Ensure start and end nodes exist
        has_start = any(n["type"] == "start" for n in workflow.nodes)
        has_end = any(n["type"] == "end" for n in workflow.nodes)
        
        if not has_start or not has_end:
            logger.warning("Generated workflow missing start or end node")
            workflow.confidence *= 0.8
        
        # Check for disconnected nodes
        node_ids = {n["id"] for n in workflow.nodes}
        connected_nodes = set()
        
        for edge in workflow.edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])
        
        disconnected = node_ids - connected_nodes
        if disconnected:
            logger.warning(f"Disconnected nodes found: {disconnected}")
            workflow.confidence *= 0.9
        
        return workflow
    
    async def suggest_improvements(
        self,
        workflow: Dict,
        execution_history: Optional[List[Dict]] = None
    ) -> List[str]:
        """Suggest improvements for existing workflow"""
        
        suggestions = []
        
        # Check for missing error handling
        has_error_handling = any(
            n.get("type") == "condition" and "error" in str(n.get("data", {})).lower()
            for n in workflow.get("nodes", [])
        )
        
        if not has_error_handling:
            suggestions.append("Add error handling nodes to improve reliability")
        
        # Check for optimization opportunities
        llm_nodes = [n for n in workflow.get("nodes", []) if n.get("type") == "llm"]
        if len(llm_nodes) > 3:
            suggestions.append("Consider combining multiple LLM calls to reduce latency")
        
        # Analyze execution history
        if execution_history:
            avg_duration = sum(h.get("duration", 0) for h in execution_history) / len(execution_history)
            if avg_duration > 10:
                suggestions.append("Workflow execution is slow, consider adding caching")
        
        return suggestions
    
    def generate_examples(self) -> List[Dict]:
        """Generate example prompts and workflows"""
        
        return [
            {
                "prompt": "Create a chatbot that answers questions about our products",
                "workflow_type": "chatflow",
                "description": "Simple Q&A chatbot with product knowledge"
            },
            {
                "prompt": "Build a workflow that fetches data from an API and sends a Slack notification",
                "workflow_type": "agentflow",
                "description": "API integration with Slack notifications"
            },
            {
                "prompt": "Make an agent that summarizes long documents",
                "workflow_type": "agentflow",
                "description": "Document summarization agent"
            },
            {
                "prompt": "Create a customer support bot that can check order status",
                "workflow_type": "chatflow",
                "description": "Customer support with order lookup"
            }
        ]
