"""
Advanced Export API

Provides endpoints for exporting agents, workflows, and blocks
in multiple formats (JSON, YAML, Python, TypeScript).
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import json
import yaml
import io
from backend.core.dependencies import get_db
from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/export", tags=["Export"])


class ExportRequest(BaseModel):
    format: str  # json, yaml, python, typescript
    include_metadata: bool = True
    include_history: bool = False
    include_metrics: bool = False


def generate_python_code(resource: dict, resource_type: str) -> str:
    """Generate Python code from resource"""
    code = f'''"""
{resource.get('name', 'Untitled')}
{resource.get('description', '')}

Auto-generated from Agent Builder
Generated: {datetime.utcnow().isoformat()}
"""

from langchain.agents import Agent
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate


class {resource.get('name', 'Agent').replace(' ', '')}:
    """
    {resource.get('description', 'Auto-generated agent')}
    """
    
    def __init__(self, model: str = "{resource.get('llm_model', 'gpt-3.5-turbo')}"):
        self.model = model
        self.llm = OpenAI(model=model)
        self.prompt_template = """
{resource.get('prompt_template', 'You are a helpful assistant.')}
"""
    
    def execute(self, input_text: str) -> str:
        """
        Execute the agent with the given input
        """
        prompt = self.prompt_template.format(input=input_text)
        response = self.llm(prompt)
        return response


# Usage example
if __name__ == "__main__":
    agent = {resource.get('name', 'Agent').replace(' ', '')}()
    result = agent.execute("Your input here")
    print(result)
'''
    return code


def generate_typescript_code(resource: dict, resource_type: str) -> str:
    """Generate TypeScript code from resource"""
    code = f'''/**
 * {resource.get('name', 'Untitled')}
 * {resource.get('description', '')}
 * 
 * Auto-generated from Agent Builder
 * Generated: {datetime.utcnow().isoformat()}
 */

import {{ OpenAI }} from 'openai';

interface AgentConfig {{
  model: string;
  temperature?: number;
  maxTokens?: number;
}}

export class {resource.get('name', 'Agent').replace(' ', '')} {{
  private client: OpenAI;
  private config: AgentConfig;
  private promptTemplate: string;

  constructor(config: AgentConfig = {{ model: '{resource.get('llm_model', 'gpt-3.5-turbo')}' }}) {{
    this.client = new OpenAI({{
      apiKey: process.env.OPENAI_API_KEY,
    }});
    this.config = config;
    this.promptTemplate = `
{resource.get('prompt_template', 'You are a helpful assistant.')}
`;
  }}

  async execute(input: string): Promise<string> {{
    const prompt = this.promptTemplate.replace('{{input}}', input);
    
    const response = await this.client.chat.completions.create({{
      model: this.config.model,
      messages: [
        {{ role: 'system', content: prompt }},
        {{ role: 'user', content: input }},
      ],
      temperature: this.config.temperature || 0.7,
      max_tokens: this.config.maxTokens || 1000,
    }});

    return response.choices[0]?.message?.content || '';
  }}
}}

// Usage example
async function main() {{
  const agent = new {resource.get('name', 'Agent').replace(' ', '')}();
  const result = await agent.execute('Your input here');
  console.log(result);
}}

// Uncomment to run
// main();
'''
    return code


@router.post("/agents/{agent_id}")
async def export_agent(
    agent_id: str,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export an agent in the specified format
    """
    try:
        # Get agent data (mock for now)
        agent_data = {
            "id": agent_id,
            "name": "Customer Support Agent",
            "description": "Handles customer support queries",
            "llm_model": "gpt-3.5-turbo",
            "llm_provider": "openai",
            "prompt_template": "You are a helpful customer support agent. Answer the following question: {input}",
            "configuration": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        if request.include_metadata:
            agent_data["metadata"] = {
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-02-20T14:30:00Z",
                "author": "user@example.com",
                "version": "1.0.0"
            }
        
        if request.include_metrics:
            agent_data["metrics"] = {
                "total_executions": 1250,
                "success_rate": 94.5,
                "avg_response_time": 2.34
            }
        
        # Generate content based on format
        if request.format == "json":
            content = json.dumps(agent_data, indent=2)
            media_type = "application/json"
            filename = f"{agent_data['name'].replace(' ', '_')}.json"
            
        elif request.format == "yaml":
            content = yaml.dump(agent_data, default_flow_style=False, sort_keys=False)
            media_type = "application/x-yaml"
            filename = f"{agent_data['name'].replace(' ', '_')}.yaml"
            
        elif request.format == "python":
            content = generate_python_code(agent_data, "agent")
            media_type = "text/x-python"
            filename = f"{agent_data['name'].replace(' ', '_')}.py"
            
        elif request.format == "typescript":
            content = generate_typescript_code(agent_data, "agent")
            media_type = "text/typescript"
            filename = f"{agent_data['name'].replace(' ', '_')}.ts"
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        # Return as downloadable file
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}")
async def export_workflow(
    workflow_id: str,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export a workflow in the specified format
    """
    try:
        # Get workflow data (mock for now)
        workflow_data = {
            "id": workflow_id,
            "name": "Data Analysis Workflow",
            "description": "Complete data analysis pipeline",
            "graph_definition": {
                "nodes": [
                    {"id": "node-1", "type": "input", "data": {"label": "Input"}},
                    {"id": "node-2", "type": "process", "data": {"label": "Process"}},
                    {"id": "node-3", "type": "output", "data": {"label": "Output"}}
                ],
                "edges": [
                    {"id": "edge-1", "source": "node-1", "target": "node-2"},
                    {"id": "edge-2", "source": "node-2", "target": "node-3"}
                ]
            }
        }
        
        if request.include_metadata:
            workflow_data["metadata"] = {
                "created_at": "2024-02-01T14:30:00Z",
                "updated_at": "2024-02-20T16:45:00Z",
                "author": "user@example.com",
                "version": "1.0.0"
            }
        
        # Generate content based on format
        if request.format == "json":
            content = json.dumps(workflow_data, indent=2)
            media_type = "application/json"
            filename = f"{workflow_data['name'].replace(' ', '_')}.json"
            
        elif request.format == "yaml":
            content = yaml.dump(workflow_data, default_flow_style=False, sort_keys=False)
            media_type = "application/x-yaml"
            filename = f"{workflow_data['name'].replace(' ', '_')}.yaml"
            
        else:
            raise HTTPException(status_code=400, detail="Code export not supported for workflows")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blocks/{block_id}")
async def export_block(
    block_id: str,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export a block in the specified format
    """
    try:
        # Similar implementation to export_agent
        # ... (implementation details)
        
        return {"message": "Block export not yet implemented"}
        
    except Exception as e:
        logger.error(f"Failed to export block: {e}")
        raise HTTPException(status_code=500, detail=str(e))
