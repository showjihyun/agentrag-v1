// API client for Agent Builder endpoints

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  agent_type: string;
  template_id?: string;
  llm_provider: string;
  llm_model: string;
  prompt_template_id?: string;
  configuration?: Record<string, any>;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  tools?: Tool[];
}

export interface Tool {
  id: string;
  name: string;
  description?: string;
  category: string;
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  implementation_type: string;
  requires_auth: boolean;
  is_builtin: boolean;
}

export interface ToolConfiguration {
  tool_id: string;
  configuration: Record<string, any>;
  order: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  agent_type: string;
  llm_provider: string;
  llm_model: string;
  prompt_template?: string;
  configuration?: Record<string, any>;
  tool_ids?: string[];
  tools?: ToolConfiguration[];
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  llm_provider?: string;
  llm_model?: string;
  prompt_template?: string;
  configuration?: Record<string, any>;
  tool_ids?: string[];
  tools?: ToolConfiguration[];
}

export interface AgentFilters {
  agent_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface Block {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  block_type: 'llm' | 'tool' | 'logic' | 'composite';
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  configuration?: Record<string, any>;
  implementation?: string;
  is_public: boolean;
  version?: string;
  created_at: string;
  updated_at: string;
}

export interface BlockCreate {
  name: string;
  description?: string;
  block_type: 'llm' | 'tool' | 'logic' | 'composite';
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  configuration?: Record<string, any>;
  implementation?: string;
}

export interface BlockUpdate {
  name?: string;
  description?: string;
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  configuration?: Record<string, any>;
  implementation?: string;
}

export interface BlockTestInput {
  input_data: Record<string, any>;
}

export interface BlockTestResult {
  output: Record<string, any>;
  duration_ms: number;
  success: boolean;
  error?: string;
}

export interface Knowledgebase {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  milvus_collection_name: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  document_count?: number;
  total_size?: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgebaseCreate {
  name: string;
  description?: string;
  embedding_model?: string;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface KnowledgebaseUpdate {
  name?: string;
  description?: string;
  embedding_model?: string;
}

export interface EmbeddingModel {
  model_id: string;
  name: string;
  provider: string;
  dimension: number;
  max_tokens: number;
  installed: boolean;
  size_mb: number;
  description: string;
  requires_api_key?: boolean;
}

export interface ModelInstallResult {
  model_id: string;
  success: boolean;
  message: string;
  download_size_mb: number;
  install_time_seconds: number;
}

export interface KnowledgebaseSearchResult {
  chunk_id: string;
  document_id: string;
  text: string;
  content?: string; // Alias for text (backward compatibility)
  score: number;
  metadata?: {
    filename?: string;
    document_name?: string;
    chunk_index?: number;
    file_type?: string;
    upload_date?: number;
    page_number?: number;
    line_number?: number;
    [key: string]: any;
  };
}

export interface DocumentUploadProgress {
  document_id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
}

export interface Execution {
  id: string;
  agent_id: string;
  agent_name?: string;
  user_id: string;
  session_id?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  execution_context?: Record<string, any>;
  status: 'running' | 'completed' | 'failed' | 'timeout';
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface ExecutionStep {
  id: string;
  execution_id: string;
  step_number: number;
  step_type: string;
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface ExecutionMetrics {
  id: string;
  execution_id: string;
  llm_call_count: number;
  llm_total_tokens: number;
  llm_prompt_tokens: number;
  llm_completion_tokens: number;
  tool_call_count: number;
  tool_total_duration_ms: number;
  cache_hit_count: number;
  cache_miss_count: number;
}

export interface ExecutionFilters {
  status?: string;
  agent_id?: string;
  time_range?: string;
  page?: number;
  page_size?: number;
}

export interface ExecutionStats {
  active: number;
  total: number;
  successRate: number;
  avgDuration: number;
}

export interface Variable {
  id: string;
  name: string;
  scope: 'global' | 'workspace' | 'user' | 'agent';
  scope_id?: string;
  value_type: 'string' | 'number' | 'boolean' | 'json';
  value: string;
  is_secret: boolean;
  created_at: string;
  updated_at: string;
}

export interface VariableCreate {
  name: string;
  scope: 'global' | 'workspace' | 'user' | 'agent';
  scope_id?: string;
  value_type: 'string' | 'number' | 'boolean' | 'json';
  value: string;
  is_secret: boolean;
}

export interface VariableUpdate {
  name?: string;
  value?: string;
  value_type?: 'string' | 'number' | 'boolean' | 'json';
}

class AgentBuilderAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Import getAccessToken from auth module
    const { getAccessToken } = await import('@/lib/auth');
    const token = getAccessToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: 'Request failed',
          code: 'UNKNOWN_ERROR'
        }));
        
        // Import error classes
        const { 
          APIError, 
          ValidationError, 
          AuthenticationError, 
          AuthorizationError, 
          NotFoundError 
        } = await import('@/lib/errors');
        
        // Throw specific error types
        switch (response.status) {
          case 400:
            throw new ValidationError(error.detail || 'Validation failed', error);
          case 401:
            throw new AuthenticationError(error.detail);
          case 403:
            throw new AuthorizationError(error.detail);
          case 404:
            throw new NotFoundError(error.resource || 'Resource');
          default:
            throw new APIError(
              response.status,
              error.code || 'API_ERROR',
              error.detail || `HTTP ${response.status}`,
              error
            );
        }
      }

      // Handle 204 No Content responses (e.g., DELETE requests)
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return undefined as T;
      }

      return response.json();
    } catch (error) {
      // Re-throw API errors
      if (error instanceof Error && error.name.includes('Error')) {
        throw error;
      }
      
      // Network errors
      const { NetworkError } = await import('@/lib/errors');
      throw new NetworkError('Network request failed');
    }
  }

  // Agent endpoints
  async getAgents(filters?: AgentFilters): Promise<{ agents: Agent[]; total: number }> {
    const params = new URLSearchParams();
    if (filters?.agent_type) params.append('agent_type', filters.agent_type);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());

    const query = params.toString();
    return this.request(`/api/agent-builder/agents${query ? `?${query}` : ''}`);
  }

  async listAgents(filters?: { is_public?: boolean }): Promise<Agent[]> {
    const params = new URLSearchParams();
    if (filters?.is_public !== undefined) params.append('is_public', filters.is_public.toString());

    const query = params.toString();
    const response = await this.request<{ agents: Agent[]; total: number }>(
      `/api/agent-builder/agents${query ? `?${query}` : ''}`
    );
    return response.agents || [];
  }

  async getAgent(agentId: string): Promise<Agent> {
    return this.request(`/api/agent-builder/agents/${agentId}`);
  }

  async createAgent(data: AgentCreate): Promise<Agent> {
    return this.request('/api/agent-builder/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAgent(agentId: string, data: AgentUpdate): Promise<Agent> {
    return this.request(`/api/agent-builder/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAgent(agentId: string): Promise<void> {
    return this.request(`/api/agent-builder/agents/${agentId}`, {
      method: 'DELETE',
    });
  }

  async cloneAgent(agentId: string): Promise<Agent> {
    return this.request(`/api/agent-builder/agents/${agentId}/clone`, {
      method: 'POST',
    });
  }

  async exportAgent(agentId: string): Promise<any> {
    return this.request(`/api/agent-builder/agents/${agentId}/export`);
  }

  async importAgent(data: any): Promise<Agent> {
    return this.request('/api/agent-builder/agents/import', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async executeAgent(agentId: string, data: { input: string; context?: any }): Promise<{
    success: boolean;
    execution_id?: string;
    output?: any;
    result?: any;
    error?: string;
  }> {
    return this.request(`/api/agent-builder/agents/${agentId}/execute`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAgentStats(agentId: string): Promise<{
    agent_id: string;
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    success_rate: number;
    avg_duration_ms: number | null;
    last_run_at: string | null;
  }> {
    return this.request(`/api/agent-builder/agents/${agentId}/stats`);
  }

  // Tool endpoints
  async getTools(): Promise<Tool[]> {
    const response = await this.request<{ tools: Tool[]; total: number; categories: string[] }>(
      '/api/agent-builder/tools'
    );
    return response.tools || [];
  }

  async getTool(toolId: string): Promise<Tool> {
    return this.request(`/api/agent-builder/tools/${toolId}`);
  }

  // Execution endpoints
  async executeAgentStream(
    agentId: string,
    input: { query: string; context?: Record<string, any> }
  ): Promise<EventSource> {
    const token = localStorage.getItem('token');
    
    if (!input.query) {
      throw new Error('Query is required');
    }
    
    const url = new URL(`${API_BASE_URL}/api/agent-builder/executions/agents/${agentId}/execute`);
    
    // For SSE, we need to use EventSource
    // Pass token even if null (backend will handle DEBUG mode)
    const eventSource = new EventSource(
      `${url.toString()}?query=${encodeURIComponent(input.query)}&token=${token || 'null'}`
    );
    
    return eventSource;
  }

  // Block endpoints
  async getBlocks(filters?: { block_type?: string; search?: string }): Promise<Block[]> {
    const params = new URLSearchParams();
    if (filters?.block_type) params.append('block_type', filters.block_type);
    if (filters?.search) params.append('search', filters.search);

    const query = params.toString();
    const response = await this.request<{ blocks: Block[]; total: number; limit: number; offset: number }>(
      `/api/agent-builder/blocks${query ? `?${query}` : ''}`
    );
    
    // Backend returns { blocks: [], total, limit, offset }
    return response.blocks || [];
  }

  async getBlock(blockId: string): Promise<Block> {
    return this.request(`/api/agent-builder/blocks/${blockId}`);
  }

  async createBlock(data: BlockCreate): Promise<Block> {
    return this.request('/api/agent-builder/blocks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateBlock(blockId: string, data: BlockUpdate): Promise<Block> {
    return this.request(`/api/agent-builder/blocks/${blockId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteBlock(blockId: string): Promise<void> {
    return this.request(`/api/agent-builder/blocks/${blockId}`, {
      method: 'DELETE',
    });
  }

  async duplicateBlock(blockId: string): Promise<Block> {
    return this.request(`/api/agent-builder/blocks/${blockId}/duplicate`, {
      method: 'POST',
    });
  }

  async testBlock(blockId: string, input: BlockTestInput): Promise<BlockTestResult> {
    return this.request(`/api/agent-builder/blocks/${blockId}/test`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async getBlockVersions(blockId: string): Promise<any[]> {
    return this.request(`/api/agent-builder/blocks/${blockId}/versions`);
  }

  // Knowledgebase endpoints
  async getKnowledgebases(): Promise<Knowledgebase[]> {
    const response = await this.request<{ knowledgebases: Knowledgebase[]; total: number; limit: number; offset: number }>('/api/agent-builder/knowledgebases');
    return response.knowledgebases || [];
  }

  async getKnowledgebase(kbId: string): Promise<Knowledgebase> {
    return this.request(`/api/agent-builder/knowledgebases/${kbId}`);
  }

  async createKnowledgebase(data: KnowledgebaseCreate): Promise<Knowledgebase> {
    return this.request('/api/agent-builder/knowledgebases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateKnowledgebase(kbId: string, data: KnowledgebaseUpdate): Promise<Knowledgebase> {
    return this.request(`/api/agent-builder/knowledgebases/${kbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteKnowledgebase(kbId: string): Promise<void> {
    return this.request(`/api/agent-builder/knowledgebases/${kbId}`, {
      method: 'DELETE',
    });
  }

  async uploadDocuments(kbId: string, files: File[]): Promise<DocumentUploadProgress[]> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const token = localStorage.getItem('token');
    const response = await fetch(
      `${API_BASE_URL}/api/agent-builder/knowledgebases/${kbId}/documents`,
      {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async searchKnowledgebase(
    kbId: string,
    query: string,
    topK: number = 10
  ): Promise<KnowledgebaseSearchResult[]> {
    const params = new URLSearchParams({
      query,
      top_k: topK.toString(),
    });

    const response = await this.request<{ results: KnowledgebaseSearchResult[]; query: string; total: number }>(
      `/api/agent-builder/knowledgebases/${kbId}/search?${params.toString()}`
    );
    
    // Extract results array from response object
    return response.results || [];
  }

  async getKnowledgebaseVersions(kbId: string): Promise<any[]> {
    return this.request(`/api/agent-builder/knowledgebases/${kbId}/versions`);
  }

  async rollbackKnowledgebase(kbId: string, versionId: string): Promise<void> {
    return this.request(`/api/agent-builder/knowledgebases/${kbId}/rollback`, {
      method: 'POST',
      body: JSON.stringify({ version_id: versionId }),
    });
  }

  // Execution endpoints
  async getExecutions(filters?: ExecutionFilters): Promise<{ executions: Execution[]; total: number }> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.agent_id) params.append('agent_id', filters.agent_id);
    if (filters?.time_range) params.append('time_range', filters.time_range);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());

    const query = params.toString();
    return this.request(`/api/agent-builder/executions${query ? `?${query}` : ''}`);
  }

  async getExecution(executionId: string): Promise<Execution> {
    // This is for AgentExecution, not WorkflowExecution
    return this.request(`/api/agent-builder/executions/${executionId}`);
  }

  async getExecutionSteps(executionId: string): Promise<ExecutionStep[]> {
    return this.request(`/api/agent-builder/executions/${executionId}/steps`);
  }

  async getExecutionMetrics(executionId: string): Promise<ExecutionMetrics> {
    return this.request(`/api/agent-builder/executions/${executionId}/metrics`);
  }

  async getExecutionStats(): Promise<ExecutionStats> {
    return this.request('/api/agent-builder/executions/stats');
  }

  async cancelExecution(executionId: string): Promise<void> {
    return this.request(`/api/agent-builder/executions/${executionId}/cancel`, {
      method: 'POST',
    });
  }

  async replayExecution(executionId: string): Promise<Execution> {
    return this.request(`/api/agent-builder/executions/${executionId}/replay`, {
      method: 'POST',
    });
  }

  // Variable endpoints
  async getVariables(scope?: string): Promise<Variable[]> {
    const params = new URLSearchParams();
    if (scope) params.append('scope', scope);

    const query = params.toString();
    return this.request(`/api/agent-builder/variables${query ? `?${query}` : ''}`);
  }

  async getVariable(variableId: string): Promise<Variable> {
    return this.request(`/api/agent-builder/variables/${variableId}`);
  }

  async createVariable(data: VariableCreate): Promise<Variable> {
    return this.request('/api/agent-builder/variables', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateVariable(variableId: string, data: VariableUpdate): Promise<Variable> {
    return this.request(`/api/agent-builder/variables/${variableId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteVariable(variableId: string): Promise<void> {
    return this.request(`/api/agent-builder/variables/${variableId}`, {
      method: 'DELETE',
    });
  }

  async revealSecret(variableId: string): Promise<{ value: string }> {
    return this.request(`/api/agent-builder/variables/${variableId}/reveal`, {
      method: 'POST',
    });
  }

  // Workflow endpoints
  async getWorkflows(filters?: { search?: string; page?: number; page_size?: number }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());
    
    const query = params.toString();
    return this.request(`/api/agent-builder/workflows${query ? `?${query}` : ''}`);
  }

  async getWorkflow(workflowId: string): Promise<any> {
    return this.request(`/api/agent-builder/workflows/${workflowId}`);
  }

  async createWorkflow(data: any): Promise<any> {
    return this.request('/api/agent-builder/workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWorkflow(workflowId: string, data: any): Promise<any> {
    return this.request(`/api/agent-builder/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteWorkflow(workflowId: string): Promise<void> {
    return this.request(`/api/agent-builder/workflows/${workflowId}`, {
      method: 'DELETE',
    });
  }

  async validateWorkflow(workflowId: string): Promise<any> {
    return this.request(`/api/agent-builder/workflows/${workflowId}/validate`, {
      method: 'POST',
    });
  }

  async executeWorkflow(workflowId: string, input: any): Promise<any> {
    return this.request(`/api/agent-builder/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async getWorkflowExecutions(
    workflowId: string, 
    filters?: { limit?: number; offset?: number; status?: string }
  ): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());
    if (filters?.status) params.append('status_filter', filters.status);
    
    const query = params.toString();
    return this.request(`/api/agent-builder/workflows/${workflowId}/executions${query ? `?${query}` : ''}`);
  }

  async getWorkflowExecution(workflowId: string, executionId: string): Promise<any> {
    return this.request(`/api/agent-builder/workflows/${workflowId}/executions/${executionId}`);
  }

  // Dashboard endpoints (with fallback for 404 errors)
  async getDashboardStats(): Promise<any> {
    try {
      return await this.request('/api/agent-builder/dashboard/stats');
    } catch (error: any) {
      if (error?.statusCode === 404 || error?.message?.includes('Not Found')) {
        return { total_agents: 0, total_workflows: 0, total_executions: 0, success_rate: 0, active_workflows: 0 };
      }
      throw error;
    }
  }

  async getRecentActivity(limit: number = 10): Promise<any> {
    try {
      return await this.request(`/api/agent-builder/dashboard/recent-activity?limit=${limit}`);
    } catch (error: any) {
      if (error?.statusCode === 404 || error?.message?.includes('Not Found')) {
        return { activities: [] };
      }
      throw error;
    }
  }

  async getFavoriteAgents(limit: number = 5): Promise<any> {
    try {
      return await this.request(`/api/agent-builder/dashboard/favorite-agents?limit=${limit}`);
    } catch (error: any) {
      if (error?.statusCode === 404 || error?.message?.includes('Not Found')) {
        return { agents: [] };
      }
      throw error;
    }
  }

  async getExecutionTrend(days: number = 7): Promise<any> {
    try {
      return await this.request(`/api/agent-builder/dashboard/execution-trend?days=${days}`);
    } catch (error: any) {
      if (error?.statusCode === 404 || error?.message?.includes('Not Found')) {
        return { trend: [] };
      }
      throw error;
    }
  }

  async getSystemStatus(): Promise<any> {
    try {
      return await this.request('/api/agent-builder/dashboard/system-status');
    } catch (error: any) {
      if (error?.statusCode === 404 || error?.message?.includes('Not Found')) {
        return { status: 'unknown', services: {}, timestamp: new Date().toISOString() };
      }
      throw error;
    }
  }

  // Memory Management APIs
  async getMemoryStats(agentId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/stats`);
    if (!response.ok) throw new Error('Failed to get memory stats');
    return response.json();
  }

  async getMemories(agentId: string, params?: { type?: string; limit?: number }) {
    const queryParams = new URLSearchParams(params as any);
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory?${queryParams}`);
    if (!response.ok) throw new Error('Failed to get memories');
    return response.json();
  }

  async deleteMemory(agentId: string, memoryId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/${memoryId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete memory');
    return response.json();
  }

  async searchMemories(agentId: string, data: { query: string; top_k: number }) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to search memories');
    return response.json();
  }

  async getMemoryTimeline(agentId: string, params?: { limit?: number }) {
    const queryParams = new URLSearchParams(params as any);
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/timeline?${queryParams}`);
    if (!response.ok) throw new Error('Failed to get memory timeline');
    return response.json();
  }

  async getMemorySettings(agentId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/settings`);
    if (!response.ok) throw new Error('Failed to get memory settings');
    return response.json();
  }

  async updateMemorySettings(agentId: string, settings: any) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update memory settings');
    return response.json();
  }

  async consolidateMemories(agentId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/agents/${agentId}/memory/consolidate`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to consolidate memories');
    return response.json();
  }

  // Cost Management APIs
  async getCostStats(agentId?: string, timeRange: string = '30d') {
    const params = new URLSearchParams({ time_range: timeRange });
    if (agentId) params.append('agent_id', agentId);
    
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/stats?${params}`);
    if (!response.ok) throw new Error('Failed to get cost stats');
    return response.json();
  }

  async getCostBreakdown(agentId?: string, timeRange: string = '30d') {
    const params = new URLSearchParams({ time_range: timeRange });
    if (agentId) params.append('agent_id', agentId);
    
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/breakdown?${params}`);
    if (!response.ok) throw new Error('Failed to get cost breakdown');
    return response.json();
  }

  async getBudgetSettings(agentId?: string) {
    const params = agentId ? `?agent_id=${agentId}` : '';
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/budget${params}`);
    if (!response.ok) throw new Error('Failed to get budget settings');
    return response.json();
  }

  async updateBudgetSettings(settings: any, agentId?: string) {
    const params = agentId ? `?agent_id=${agentId}` : '';
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/budget${params}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update budget settings');
    return response.json();
  }

  async analyzeCostOptimization(agentId?: string) {
    const params = agentId ? `?agent_id=${agentId}` : '';
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/analyze${params}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to analyze cost optimization');
    return response.json();
  }

  async applyCostOptimization(optimizationId: string, agentId?: string) {
    const params = agentId ? `?agent_id=${agentId}` : '';
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/optimize/${optimizationId}${params}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to apply cost optimization');
    return response.json();
  }

  async predictCosts(agentId?: string, days: number = 30) {
    const params = new URLSearchParams({ days: days.toString() });
    if (agentId) params.append('agent_id', agentId);
    
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/cost/predict?${params}`);
    if (!response.ok) throw new Error('Failed to predict costs');
    return response.json();
  }

  // Branch Management APIs
  async getBranches(workflowId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches`);
    if (!response.ok) throw new Error('Failed to get branches');
    return response.json();
  }

  async createBranch(workflowId: string, data: { name: string; description?: string }) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create branch');
    return response.json();
  }

  async switchBranch(workflowId: string, branchId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches/${branchId}/switch`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to switch branch');
    return response.json();
  }

  async mergeBranch(workflowId: string, branchId: string, data: { target_branch_id: string; resolve_conflicts?: string }) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches/${branchId}/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to merge branch');
    return response.json();
  }

  async deleteBranch(workflowId: string, branchId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches/${branchId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete branch');
  }

  async getBranchCommits(workflowId: string, branchId: string, limit: number = 50) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches/${branchId}/commits?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to get branch commits');
    return response.json();
  }

  async createCommit(workflowId: string, branchId: string, message: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/workflows/${workflowId}/branches/${branchId}/commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error('Failed to create commit');
    return response.json();
  }

  // Collaboration REST APIs
  async getActiveUsers(resourceType: string, resourceId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/collaboration/${resourceType}/${resourceId}/users`);
    if (!response.ok) throw new Error('Failed to get active users');
    return response.json();
  }

  async getResourceVersion(resourceType: string, resourceId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/collaboration/${resourceType}/${resourceId}/version`);
    if (!response.ok) throw new Error('Failed to get resource version');
    return response.json();
  }

  async acquireLock(resourceType: string, resourceId: string, userId: string, timeout: number = 300) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/collaboration/${resourceType}/${resourceId}/lock?user_id=${userId}&timeout=${timeout}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to acquire lock');
    return response.json();
  }

  async releaseLock(resourceType: string, resourceId: string, userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/collaboration/${resourceType}/${resourceId}/lock?user_id=${userId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to release lock');
    return response.json();
  }

  // Embedding Models APIs
  async getAvailableModels(): Promise<EmbeddingModel[]> {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/embedding-models/available`);
    if (!response.ok) throw new Error('Failed to get available models');
    return response.json();
  }

  async getInstalledModels(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/embedding-models/installed`);
    if (!response.ok) throw new Error('Failed to get installed models');
    return response.json();
  }

  async installModel(modelId: string): Promise<ModelInstallResult> {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/embedding-models/install`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId }),
    });
    if (!response.ok) throw new Error('Failed to install model');
    return response.json();
  }

  async checkModelInstalled(modelId: string): Promise<{ model_id: string; installed: boolean }> {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/embedding-models/check/${encodeURIComponent(modelId)}`);
    if (!response.ok) throw new Error('Failed to check model');
    return response.json();
  }

  async uninstallModel(modelId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/agent-builder/embedding-models/${encodeURIComponent(modelId)}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to uninstall model');
    return response.json();
  }

  // Custom Tool APIs
  async getCustomTools(): Promise<any[]> {
    const response = await this.request<{ tools: any[] }>('/api/agent-builder/custom-tools');
    return response.tools || [];
  }

  async createCustomTool(data: any): Promise<any> {
    return this.request('/api/agent-builder/custom-tools', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCustomTool(toolId: string, data: any): Promise<any> {
    return this.request(`/api/agent-builder/custom-tools/${toolId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCustomTool(toolId: string): Promise<void> {
    return this.request(`/api/agent-builder/custom-tools/${toolId}`, {
      method: 'DELETE',
    });
  }

  async testCustomTool(data: { implementation: string; implementationType: string; parameters: any }): Promise<any> {
    return this.request('/api/agent-builder/tools/test-custom', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const agentBuilderAPI = new AgentBuilderAPI();
