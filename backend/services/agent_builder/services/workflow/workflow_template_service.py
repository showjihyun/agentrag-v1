"""Workflow Template Service for managing workflow templates."""

import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from backend.db.models.agent_builder import Workflow, AgentBlock, AgentEdge

logger = logging.getLogger(__name__)


class WorkflowTemplate:
    """Workflow template data structure."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: str,
        blocks: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        variables: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.blocks = blocks
        self.edges = edges
        self.variables = variables
        self.metadata = metadata
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "blocks": self.blocks,
            "edges": self.edges,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkflowTemplateService:
    """Service for managing workflow templates."""
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Template Service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in workflow templates."""
        # Simple RAG Workflow
        self._templates["simple-rag"] = WorkflowTemplate(
            id="simple-rag",
            name="Simple RAG Workflow",
            description="Basic RAG workflow with knowledge base search and LLM response",
            category="rag",
            blocks=[
                {
                    "type": "knowledge_base",
                    "name": "Search Knowledge Base",
                    "position_x": 100,
                    "position_y": 100,
                    "config": {},
                    "sub_blocks": {
                        "query": "${user_query}",
                        "top_k": 5
                    }
                },
                {
                    "type": "openai",
                    "name": "Generate Response",
                    "position_x": 400,
                    "position_y": 100,
                    "config": {},
                    "sub_blocks": {
                        "model": "gpt-4",
                        "prompt": "Based on the following context, answer the question:\n\nContext: ${search_results}\n\nQuestion: ${user_query}",
                        "temperature": 0.7
                    }
                }
            ],
            edges=[
                {
                    "source_block": 0,
                    "target_block": 1,
                    "source_handle": "results",
                    "target_handle": "search_results"
                }
            ],
            variables=[
                {"name": "user_query", "type": "string", "required": True}
            ],
            metadata={
                "use_cases": ["Q&A", "Document Search", "Knowledge Retrieval"],
                "difficulty": "beginner"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Multi-Step Research Workflow
        self._templates["multi-step-research"] = WorkflowTemplate(
            id="multi-step-research",
            name="Multi-Step Research Workflow",
            description="Advanced research workflow with web search, knowledge base, and synthesis",
            category="research",
            blocks=[
                {
                    "type": "http",
                    "name": "Web Search",
                    "position_x": 100,
                    "position_y": 100,
                    "config": {},
                    "sub_blocks": {
                        "url": "https://api.tavily.com/search",
                        "method": "POST",
                        "body": {"query": "${research_topic}", "max_results": 5}
                    }
                },
                {
                    "type": "knowledge_base",
                    "name": "Search Internal Docs",
                    "position_x": 100,
                    "position_y": 250,
                    "config": {},
                    "sub_blocks": {
                        "query": "${research_topic}",
                        "top_k": 5
                    }
                },
                {
                    "type": "openai",
                    "name": "Synthesize Findings",
                    "position_x": 400,
                    "position_y": 175,
                    "config": {},
                    "sub_blocks": {
                        "model": "gpt-4",
                        "prompt": "Synthesize the following research findings:\n\nWeb Results: ${web_results}\n\nInternal Docs: ${kb_results}\n\nTopic: ${research_topic}",
                        "temperature": 0.5
                    }
                }
            ],
            edges=[
                {
                    "source_block": 0,
                    "target_block": 2,
                    "source_handle": "results",
                    "target_handle": "web_results"
                },
                {
                    "source_block": 1,
                    "target_block": 2,
                    "source_handle": "results",
                    "target_handle": "kb_results"
                }
            ],
            variables=[
                {"name": "research_topic", "type": "string", "required": True}
            ],
            metadata={
                "use_cases": ["Research", "Analysis", "Information Gathering"],
                "difficulty": "intermediate"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Conditional Routing Workflow
        self._templates["conditional-routing"] = WorkflowTemplate(
            id="conditional-routing",
            name="Conditional Routing Workflow",
            description="Workflow with conditional branching based on input classification",
            category="routing",
            blocks=[
                {
                    "type": "openai",
                    "name": "Classify Intent",
                    "position_x": 100,
                    "position_y": 100,
                    "config": {},
                    "sub_blocks": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Classify the following query into one of: question, command, feedback\n\nQuery: ${user_input}",
                        "temperature": 0.1
                    }
                },
                {
                    "type": "condition",
                    "name": "Route by Intent",
                    "position_x": 400,
                    "position_y": 100,
                    "config": {},
                    "sub_blocks": {
                        "condition": "${intent} == 'question'"
                    }
                },
                {
                    "type": "knowledge_base",
                    "name": "Answer Question",
                    "position_x": 700,
                    "position_y": 50,
                    "config": {},
                    "sub_blocks": {
                        "query": "${user_input}",
                        "top_k": 3
                    }
                },
                {
                    "type": "http",
                    "name": "Execute Command",
                    "position_x": 700,
                    "position_y": 150,
                    "config": {},
                    "sub_blocks": {
                        "url": "${command_api_url}",
                        "method": "POST",
                        "body": {"command": "${user_input}"}
                    }
                }
            ],
            edges=[
                {
                    "source_block": 0,
                    "target_block": 1,
                    "source_handle": "intent",
                    "target_handle": "intent"
                },
                {
                    "source_block": 1,
                    "target_block": 2,
                    "source_handle": "true",
                    "target_handle": "input"
                },
                {
                    "source_block": 1,
                    "target_block": 3,
                    "source_handle": "false",
                    "target_handle": "input"
                }
            ],
            variables=[
                {"name": "user_input", "type": "string", "required": True},
                {"name": "command_api_url", "type": "string", "required": True}
            ],
            metadata={
                "use_cases": ["Intent Classification", "Routing", "Multi-Path Workflows"],
                "difficulty": "intermediate"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        logger.info(f"Loaded {len(self._templates)} built-in workflow templates")
    
    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """
        List available workflow templates.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of workflow templates
        """
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get a specific workflow template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Workflow template or None
        """
        return self._templates.get(template_id)
    
    def create_workflow_from_template(
        self,
        template_id: str,
        user_id: UUID,
        workflow_name: Optional[str] = None,
        variable_values: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Create a new workflow from a template.
        
        Args:
            template_id: Template ID
            user_id: User ID
            workflow_name: Custom workflow name (optional)
            variable_values: Variable values to substitute (optional)
            
        Returns:
            Created Workflow model
            
        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Create workflow
        workflow = Workflow(
            id=uuid4(),
            user_id=user_id,
            name=workflow_name or template.name,
            description=template.description,
            graph_definition={"template_id": template_id},
            is_public=False,
        )
        
        self.db.add(workflow)
        self.db.flush()
        
        # Create blocks
        block_id_map = {}  # Map template block index to created block ID
        
        for i, block_data in enumerate(template.blocks):
            # Substitute variables in sub_blocks
            sub_blocks = block_data.get("sub_blocks", {})
            if variable_values:
                sub_blocks = self._substitute_variables(sub_blocks, variable_values)
            
            block = AgentBlock(
                id=uuid4(),
                workflow_id=workflow.id,
                type=block_data["type"],
                name=block_data["name"],
                position_x=block_data["position_x"],
                position_y=block_data["position_y"],
                config=block_data.get("config", {}),
                sub_blocks=sub_blocks,
                inputs=block_data.get("inputs", {}),
                outputs=block_data.get("outputs", {}),
                enabled=True,
            )
            
            self.db.add(block)
            self.db.flush()
            
            block_id_map[i] = block.id
        
        # Create edges
        for edge_data in template.edges:
            source_idx = edge_data["source_block"]
            target_idx = edge_data["target_block"]
            
            if source_idx in block_id_map and target_idx in block_id_map:
                edge = AgentEdge(
                    id=uuid4(),
                    workflow_id=workflow.id,
                    source_block_id=block_id_map[source_idx],
                    target_block_id=block_id_map[target_idx],
                    source_handle=edge_data.get("source_handle"),
                    target_handle=edge_data.get("target_handle"),
                )
                
                self.db.add(edge)
        
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Created workflow from template '{template_id}': {workflow.id}")
        
        return workflow
    
    def save_workflow_as_template(
        self,
        workflow_id: UUID,
        template_name: str,
        template_description: str,
        category: str
    ) -> WorkflowTemplate:
        """
        Save an existing workflow as a template.
        
        Args:
            workflow_id: Workflow ID
            template_name: Template name
            template_description: Template description
            category: Template category
            
        Returns:
            Created WorkflowTemplate
            
        Raises:
            ValueError: If workflow not found
        """
        # Load workflow
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Load blocks and edges
        blocks = self.db.query(AgentBlock).filter(
            AgentBlock.workflow_id == workflow_id
        ).all()
        
        edges = self.db.query(AgentEdge).filter(
            AgentEdge.workflow_id == workflow_id
        ).all()
        
        # Create block ID to index map
        block_id_to_idx = {block.id: i for i, block in enumerate(blocks)}
        
        # Convert blocks to template format
        template_blocks = []
        for block in blocks:
            template_blocks.append({
                "type": block.type,
                "name": block.name,
                "position_x": block.position_x,
                "position_y": block.position_y,
                "config": block.config,
                "sub_blocks": block.sub_blocks,
                "inputs": block.inputs,
                "outputs": block.outputs,
            })
        
        # Convert edges to template format
        template_edges = []
        for edge in edges:
            if edge.source_block_id in block_id_to_idx and edge.target_block_id in block_id_to_idx:
                template_edges.append({
                    "source_block": block_id_to_idx[edge.source_block_id],
                    "target_block": block_id_to_idx[edge.target_block_id],
                    "source_handle": edge.source_handle,
                    "target_handle": edge.target_handle,
                })
        
        # Extract variables from sub_blocks
        variables = self._extract_variables(template_blocks)
        
        # Create template
        template_id = f"custom-{uuid4().hex[:8]}"
        template = WorkflowTemplate(
            id=template_id,
            name=template_name,
            description=template_description,
            category=category,
            blocks=template_blocks,
            edges=template_edges,
            variables=variables,
            metadata={
                "source_workflow_id": str(workflow_id),
                "created_from": "user_workflow"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Store template
        self._templates[template_id] = template
        
        logger.info(f"Saved workflow {workflow_id} as template '{template_id}'")
        
        return template
    
    def _substitute_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """
        Substitute variables in data structure.
        
        Args:
            data: Data to substitute variables in
            variables: Variable values
            
        Returns:
            Data with substituted variables
        """
        if isinstance(data, str):
            # Replace ${variable_name} with value
            for var_name, var_value in variables.items():
                data = data.replace(f"${{{var_name}}}", str(var_value))
            return data
        elif isinstance(data, dict):
            return {k: self._substitute_variables(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        else:
            return data
    
    def _extract_variables(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract variables from blocks.
        
        Args:
            blocks: List of block data
            
        Returns:
            List of variable definitions
        """
        import re
        
        variables = set()
        pattern = r'\$\{([^}]+)\}'
        
        def find_variables(data: Any):
            if isinstance(data, str):
                matches = re.findall(pattern, data)
                variables.update(matches)
            elif isinstance(data, dict):
                for value in data.values():
                    find_variables(value)
            elif isinstance(data, list):
                for item in data:
                    find_variables(item)
        
        for block in blocks:
            find_variables(block.get("sub_blocks", {}))
        
        return [
            {"name": var, "type": "string", "required": True}
            for var in sorted(variables)
        ]
