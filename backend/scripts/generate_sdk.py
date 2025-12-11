#!/usr/bin/env python3
"""
SDK Generator Script

Generates client SDKs from OpenAPI specification.
Supports Python and TypeScript SDK generation.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_openapi_spec():
    """Get OpenAPI specification from FastAPI app."""
    from backend.main import app
    return app.openapi()


def save_openapi_spec(output_path: str = "openapi.json"):
    """Save OpenAPI spec to file."""
    spec = get_openapi_spec()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenAPI spec saved to {output_path}")
    return output_path


def generate_python_sdk(spec_path: str, output_dir: str = "sdk/python"):
    """Generate Python SDK using openapi-python-client."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🐍 Generating Python SDK...")
    
    # Check if openapi-python-client is installed
    try:
        subprocess.run(
            ["openapi-python-client", "--version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  openapi-python-client not found. Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "openapi-python-client"],
            check=True,
        )
    
    # Generate SDK
    try:
        # Remove existing SDK if present
        sdk_dir = output_path / "agenticrag-client"
        if sdk_dir.exists():
            import shutil
            shutil.rmtree(sdk_dir)
        
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path", spec_path,
                "--output-path", str(output_path),
                "--config", str(Path(__file__).parent / "sdk_config.yaml"),
            ],
            check=True,
            cwd=str(output_path.parent),
        )
        print(f"✅ Python SDK generated at {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate Python SDK: {e}")
        # Fallback: generate minimal SDK manually
        generate_minimal_python_sdk(spec_path, output_dir)


def generate_minimal_python_sdk(spec_path: str, output_dir: str):
    """Generate a minimal Python SDK manually."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(spec_path, "r") as f:
        spec = json.load(f)
    
    # Generate client code
    client_code = '''"""
AgenticRAG Python SDK

Auto-generated client for AgenticRAG API.
"""

import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout: float = 30.0


class AgenticRAGClient:
    """AgenticRAG API Client."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
        
        # Initialize sub-clients
        self.workflows = WorkflowsClient(self)
        self.chatflows = ChatflowsClient(self)
        self.agents = AgentsClient(self)
        self.executions = ExecutionsClient(self)
        self.cost_tracking = CostTrackingClient(self)
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        response = self._client.request(
            method=method,
            url=path,
            params=params,
            json=json_data,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()
    
    def close(self):
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class WorkflowsClient:
    """Workflows API client."""
    
    def __init__(self, client: AgenticRAGClient):
        self._client = client
    
    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List workflows."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        return self._client._request("GET", "/api/agent-builder/workflows", params=params)
    
    def get(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID."""
        return self._client._request("GET", f"/api/agent-builder/workflows/{workflow_id}")
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        return self._client._request("POST", "/api/agent-builder/workflows", json_data=data)
    
    def update(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a workflow."""
        return self._client._request("PUT", f"/api/agent-builder/workflows/{workflow_id}", json_data=data)
    
    def delete(self, workflow_id: str) -> None:
        """Delete a workflow."""
        self._client._request("DELETE", f"/api/agent-builder/workflows/{workflow_id}")
    
    def execute(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a workflow."""
        return self._client._request(
            "POST",
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json_data=input_data or {},
        )
    
    def get_executions(self, workflow_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get workflow execution history."""
        return self._client._request(
            "GET",
            f"/api/agent-builder/workflows/{workflow_id}/executions",
            params={"limit": limit},
        )


class ChatflowsClient:
    """Chatflows API client."""
    
    def __init__(self, client: AgenticRAGClient):
        self._client = client
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Send a chat message."""
        data = {
            "message": message,
            "session_id": session_id,
            "workflow_id": workflow_id,
            "config": config or {},
        }
        return self._client._request("POST", "/api/agent-builder/chatflow/chat", json_data=data)
    
    def get_history(self, session_id: str) -> Dict[str, Any]:
        """Get chat history for a session."""
        return self._client._request("GET", f"/api/agent-builder/chatflow/sessions/{session_id}/history")
    
    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session."""
        return self._client._request("DELETE", f"/api/agent-builder/chatflow/sessions/{session_id}")


class AgentsClient:
    """Agents API client."""
    
    def __init__(self, client: AgenticRAGClient):
        self._client = client
    
    def list(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List agents."""
        return self._client._request(
            "GET",
            "/api/agent-builder/agents",
            params={"skip": skip, "limit": limit},
        )
    
    def get(self, agent_id: str) -> Dict[str, Any]:
        """Get agent by ID."""
        return self._client._request("GET", f"/api/agent-builder/agents/{agent_id}")
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        return self._client._request("POST", "/api/agent-builder/agents", json_data=data)
    
    def update(self, agent_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an agent."""
        return self._client._request("PUT", f"/api/agent-builder/agents/{agent_id}", json_data=data)
    
    def delete(self, agent_id: str) -> None:
        """Delete an agent."""
        self._client._request("DELETE", f"/api/agent-builder/agents/{agent_id}")


class ExecutionsClient:
    """Executions API client."""
    
    def __init__(self, client: AgenticRAGClient):
        self._client = client
    
    def list(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List executions."""
        params = {"limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status_filter"] = status
        return self._client._request("GET", "/api/agent-builder/executions", params=params)
    
    def get(self, execution_id: str) -> Dict[str, Any]:
        """Get execution by ID."""
        return self._client._request("GET", f"/api/agent-builder/executions/{execution_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self._client._request("GET", "/api/agent-builder/executions/stats")


class CostTrackingClient:
    """Cost tracking API client."""
    
    def __init__(self, client: AgenticRAGClient):
        self._client = client
    
    def get_dashboard(self, days: int = 30, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost tracking dashboard."""
        params = {"days": days}
        if workflow_id:
            params["workflow_id"] = workflow_id
        return self._client._request("GET", "/api/agent-builder/cost-tracking/dashboard", params=params)
    
    def get_pricing(self) -> Dict[str, Any]:
        """Get model pricing information."""
        return self._client._request("GET", "/api/agent-builder/cost-tracking/pricing")
    
    def estimate_cost(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, Any]:
        """Estimate cost for a given model and token count."""
        return self._client._request(
            "GET",
            "/api/agent-builder/cost-tracking/estimate",
            params={
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )


# Async client
class AsyncAgenticRAGClient:
    """Async AgenticRAG API Client."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        response = await self._client.request(
            method=method,
            url=path,
            params=params,
            json=json_data,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # Workflow methods
    async def list_workflows(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        return await self._request("GET", "/api/agent-builder/workflows", params={"skip": skip, "limit": limit})
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/agent-builder/workflows/{workflow_id}")
    
    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._request("POST", f"/api/agent-builder/workflows/{workflow_id}/execute", json_data=input_data or {})
    
    # Chat methods
    async def chat(self, message: str, session_id: Optional[str] = None, config: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._request("POST", "/api/agent-builder/chatflow/chat", json_data={
            "message": message,
            "session_id": session_id,
            "config": config or {},
        })
'''
    
    # Write client file
    client_file = output_path / "agenticrag_client.py"
    with open(client_file, "w", encoding="utf-8") as f:
        f.write(client_code)
    
    # Write __init__.py
    init_file = output_path / "__init__.py"
    with open(init_file, "w", encoding="utf-8") as f:
        f.write('"""AgenticRAG Python SDK."""\n')
        f.write('from .agenticrag_client import AgenticRAGClient, AsyncAgenticRAGClient, APIConfig\n')
        f.write('\n__all__ = ["AgenticRAGClient", "AsyncAgenticRAGClient", "APIConfig"]\n')
        f.write(f'__version__ = "1.0.0"\n')
    
    # Write setup.py
    setup_file = output_path / "setup.py"
    with open(setup_file, "w", encoding="utf-8") as f:
        f.write('''from setuptools import setup, find_packages

setup(
    name="agenticrag-client",
    version="1.0.0",
    description="Python SDK for AgenticRAG API",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
    ],
    python_requires=">=3.8",
)
''')
    
    # Write README
    readme_file = output_path / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write('''# AgenticRAG Python SDK

Python client for the AgenticRAG API.

## Installation

```bash
pip install -e .
```

## Usage

```python
from agenticrag_client import AgenticRAGClient, APIConfig

# Initialize client
config = APIConfig(
    base_url="http://localhost:8000",
    api_key="your-api-key",
)
client = AgenticRAGClient(config)

# List workflows
workflows = client.workflows.list()

# Execute a workflow
result = client.workflows.execute("workflow-id", {"input": "data"})

# Chat
response = client.chatflows.chat("Hello, how can you help?")

# Close client
client.close()
```

## Async Usage

```python
import asyncio
from agenticrag_client import AsyncAgenticRAGClient, APIConfig

async def main():
    config = APIConfig(base_url="http://localhost:8000")
    async with AsyncAgenticRAGClient(config) as client:
        workflows = await client.list_workflows()
        print(workflows)

asyncio.run(main())
```
''')
    
    print(f"✅ Minimal Python SDK generated at {output_path}")


def generate_typescript_sdk(spec_path: str, output_dir: str = "sdk/typescript"):
    """Generate TypeScript SDK."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📘 Generating TypeScript SDK...")
    
    with open(spec_path, "r") as f:
        spec = json.load(f)
    
    # Generate TypeScript client
    ts_code = '''/**
 * AgenticRAG TypeScript SDK
 * 
 * Auto-generated client for AgenticRAG API.
 */

export interface APIConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface WorkflowResponse {
  id: string;
  name: string;
  description?: string;
  graph_definition: Record<string, any>;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExecutionResponse {
  execution_id: string;
  status: string;
  message?: string;
  output?: Record<string, any>;
}

export interface ChatResponse {
  success: boolean;
  response?: string;
  error?: string;
  session_id: string;
  message_count: number;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
}

export class AgenticRAGClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(config: APIConfig) {
    this.baseUrl = config.baseUrl || 'http://localhost:8000';
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
  }

  private async request<T>(
    method: string,
    path: string,
    options?: {
      params?: Record<string, any>;
      body?: Record<string, any>;
    }
  ): Promise<T> {
    const url = new URL(path, this.baseUrl);
    
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url.toString(), {
      method,
      headers,
      body: options?.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Workflows
  workflows = {
    list: (params?: { skip?: number; limit?: number; search?: string }) =>
      this.request<{ workflows: WorkflowResponse[]; total: number }>(
        'GET',
        '/api/agent-builder/workflows',
        { params }
      ),

    get: (workflowId: string) =>
      this.request<WorkflowResponse>('GET', `/api/agent-builder/workflows/${workflowId}`),

    create: (data: { name: string; description?: string; graph_definition: Record<string, any> }) =>
      this.request<WorkflowResponse>('POST', '/api/agent-builder/workflows', { body: data }),

    update: (workflowId: string, data: Partial<{ name: string; description: string; graph_definition: Record<string, any> }>) =>
      this.request<WorkflowResponse>('PUT', `/api/agent-builder/workflows/${workflowId}`, { body: data }),

    delete: (workflowId: string) =>
      this.request<void>('DELETE', `/api/agent-builder/workflows/${workflowId}`),

    execute: (workflowId: string, inputData?: Record<string, any>) =>
      this.request<ExecutionResponse>('POST', `/api/agent-builder/workflows/${workflowId}/execute`, {
        body: inputData || {},
      }),

    getExecutions: (workflowId: string, params?: { limit?: number }) =>
      this.request<{ executions: any[]; total: number }>(
        'GET',
        `/api/agent-builder/workflows/${workflowId}/executions`,
        { params }
      ),
  };

  // Chatflows
  chatflows = {
    chat: (data: {
      message: string;
      session_id?: string;
      workflow_id?: string;
      config?: Record<string, any>;
    }) =>
      this.request<ChatResponse>('POST', '/api/agent-builder/chatflow/chat', { body: data }),

    getHistory: (sessionId: string) =>
      this.request<{ session_id: string; messages: any[]; message_count: number }>(
        'GET',
        `/api/agent-builder/chatflow/sessions/${sessionId}/history`
      ),

    clearSession: (sessionId: string) =>
      this.request<{ session_id: string; cleared: boolean }>(
        'DELETE',
        `/api/agent-builder/chatflow/sessions/${sessionId}`
      ),
  };

  // Executions
  executions = {
    list: (params?: { agent_id?: string; status_filter?: string; limit?: number }) =>
      this.request<{ executions: any[]; total: number }>(
        'GET',
        '/api/agent-builder/executions',
        { params }
      ),

    get: (executionId: string) =>
      this.request<any>('GET', `/api/agent-builder/executions/${executionId}`),

    getStats: () =>
      this.request<any>('GET', '/api/agent-builder/executions/stats'),
  };

  // Cost Tracking
  costTracking = {
    getDashboard: (params?: { days?: number; workflow_id?: string }) =>
      this.request<any>('GET', '/api/agent-builder/cost-tracking/dashboard', { params }),

    getPricing: () =>
      this.request<any>('GET', '/api/agent-builder/cost-tracking/pricing'),

    estimateCost: (params: {
      model: string;
      provider: string;
      input_tokens: number;
      output_tokens: number;
    }) =>
      this.request<any>('GET', '/api/agent-builder/cost-tracking/estimate', { params }),
  };

  // Metrics
  metrics = {
    getSummary: () =>
      this.request<any>('GET', '/api/agent-builder/metrics/summary'),

    getJson: () =>
      this.request<any>('GET', '/api/agent-builder/metrics/json'),
  };
}

export default AgenticRAGClient;
'''
    
    # Write client file
    client_file = output_path / "index.ts"
    with open(client_file, "w", encoding="utf-8") as f:
        f.write(ts_code)
    
    # Write package.json
    package_json = output_path / "package.json"
    with open(package_json, "w", encoding="utf-8") as f:
        json.dump({
            "name": "agenticrag-client",
            "version": "1.0.0",
            "description": "TypeScript SDK for AgenticRAG API",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "prepublishOnly": "npm run build"
            },
            "devDependencies": {
                "typescript": "^5.0.0"
            },
            "files": ["dist"],
            "license": "MIT"
        }, f, indent=2)
    
    # Write tsconfig.json
    tsconfig = output_path / "tsconfig.json"
    with open(tsconfig, "w", encoding="utf-8") as f:
        json.dump({
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "declaration": True,
                "outDir": "./dist",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True
            },
            "include": ["*.ts"],
            "exclude": ["node_modules", "dist"]
        }, f, indent=2)
    
    # Write README
    readme = output_path / "README.md"
    with open(readme, "w", encoding="utf-8") as f:
        f.write('''# AgenticRAG TypeScript SDK

TypeScript client for the AgenticRAG API.

## Installation

```bash
npm install agenticrag-client
```

## Usage

```typescript
import { AgenticRAGClient } from 'agenticrag-client';

const client = new AgenticRAGClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
});

// List workflows
const { workflows } = await client.workflows.list();

// Execute a workflow
const result = await client.workflows.execute('workflow-id', { input: 'data' });

// Chat
const response = await client.chatflows.chat({
  message: 'Hello, how can you help?',
});
```
''')
    
    print(f"✅ TypeScript SDK generated at {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate SDKs from OpenAPI spec")
    parser.add_argument(
        "--output-dir",
        default="sdk",
        help="Output directory for SDKs",
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help="Generate Python SDK",
    )
    parser.add_argument(
        "--typescript",
        action="store_true",
        help="Generate TypeScript SDK",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all SDKs",
    )
    
    args = parser.parse_args()
    
    # Default to all if no specific SDK requested
    if not args.python and not args.typescript:
        args.all = True
    
    # Save OpenAPI spec
    spec_path = save_openapi_spec(os.path.join(args.output_dir, "openapi.json"))
    
    # Generate SDKs
    if args.all or args.python:
        generate_minimal_python_sdk(spec_path, os.path.join(args.output_dir, "python"))
    
    if args.all or args.typescript:
        generate_typescript_sdk(spec_path, os.path.join(args.output_dir, "typescript"))
    
    print("\n🎉 SDK generation complete!")


if __name__ == "__main__":
    main()
