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
  is_public?: boolean;
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

export interface AgentflowAgent {
  id: string;
  agent_id: string;
  block_id?: string;
  name: string;
  role: string;
  description?: string;
  capabilities: string[];
  priority: number;
  max_retries: number;
  timeout_seconds: number;
  dependencies: string[];
  input_mapping?: Record<string, any>;
  output_mapping?: Record<string, any>;
  conditional_logic?: Record<string, any>;
  parallel_group?: string;
  position_x: number;
  position_y: number;
}

export interface AgentflowEdge {
  id: string;
  source_agent_id: string;
  target_agent_id: string;
  edge_type: 'data_flow' | 'control_flow' | 'conditional';
  condition?: Record<string, any>;
  data_mapping?: Record<string, any>;
  label?: string;
  style?: Record<string, any>;
}

export interface Agentflow {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  orchestration_type: string;
  supervisor_config: Record<string, any>;
  graph_definition: Record<string, any>;
  tags: string[];
  category?: string;
  is_public: boolean;
  is_active: boolean;
  execution_count: number;
  last_execution_status?: string;
  last_execution_at?: string;
  created_at: string;
  updated_at: string;
  agents?: AgentflowAgent[];
  edges?: AgentflowEdge[];
}

export interface AgentflowCreate {
  name: string;
  description?: string;
  orchestration_type: string;
  supervisor_config?: Record<string, any>;
  graph_definition?: Record<string, any>;
  tags?: string[];
  category?: string;
  agents_config?: Array<{
    agent_id: string;
    name: string;
    role: string;
    description?: string;
    capabilities?: string[];
    priority?: number;
    max_retries?: number;
    timeout_seconds?: number;
    dependencies?: string[];
    create_block?: boolean;
    block_id?: string;
    position_x?: number;
    position_y?: number;
  }>;
  edges_config?: Array<{
    source: string;
    target: string;
    edge_type?: string;
    condition?: Record<string, any>;
    data_mapping?: Record<string, any>;
    label?: string;
  }>;
}

export interface ExecutionPlan {
  agentflow_id: string;
  orchestration_type: string;
  execution_plan: any;
  supervisor_config: Record<string, any>;
  total_agents: number;
  total_edges: number;
}

export interface ValidationReport {
  agentflow_id: string;
  validation_status: 'valid' | 'invalid';
  issues: string[];
  recommendations: string[];
  agent_count: number;
  edge_count: number;
  orchestration_type: string;
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
  kg_enabled?: boolean;
  kb_type?: string;
  search_strategy?: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgebaseCreate {
  name: string;
  description?: string;
  embedding_model?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  kg_enabled?: boolean;
}

export interface KnowledgebaseUpdate {
  name?: string;
  description?: string;
  embedding_model?: string;
  kg_enabled?: boolean;
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
  scope?: 'global' | 'workspace' | 'user' | 'agent';
  scope_id?: string;
  value_type?: 'string' | 'number' | 'boolean' | 'json';
  value?: string;
  is_secret?: boolean;
}

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

export interface AuditLogFilters {
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogResponse {
  logs: AuditLog[];
  total: number;
  total_pages: number;
  current_page: number;
  page_size: number;
}

// Enhanced interfaces for optimization features
export interface OptimizationSuggestion {
  type: 'performance' | 'cost' | 'reliability' | 'resource';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  priority: 'low' | 'medium' | 'high';
  action?: string;
  estimated_improvement?: number;
  implementation_effort?: string;
  confidence_score?: number;
}

export interface WorkflowAnalysis {
  workflow_id: string;
  analysis_timestamp: string;
  execution_count: number;
  success_rate: number;
  average_duration_ms: number;
  optimization_score: number;
  bottlenecks: Array<{
    agent_id: string;
    agent_name: string;
    bottleneck_type: string;
    severity: number;
    frequency: number;
    impact_on_total_time: number;
    suggested_fixes: string[];
  }>;
  resource_usage: {
    avg_tokens_per_execution: number;
    avg_memory_mb_per_execution: number;
    avg_cpu_seconds_per_execution: number;
    total_tokens: number;
    resource_efficiency_score: number;
  };
  cost_analysis: {
    total_cost: number;
    avg_cost_per_execution: number;
    avg_daily_cost: number;
    cost_trend: string;
    cost_efficiency_score: number;
  };
  suggestions: OptimizationSuggestion[];
}

export interface PerformancePrediction {
  estimated_duration_ms: number;
  estimated_cost: number;
  estimated_tokens: number;
  success_probability: number;
  recommended_concurrency: number;
  confidence_score: number;
  bottleneck_warnings: string[];
}

export interface ErrorRecoveryStats {
  total_errors: number;
  successful_recoveries: number;
  failed_recoveries: number;
  recovery_success_rate: number;
  recent_errors: number;
  recovery_strategies_used: Record<string, number>;
  circuit_breaker_states: Record<string, string>;
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

  async listTools(): Promise<Tool[]> {
    return this.getTools();
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

  async getMemories(agentId: string, params?: { type?: string; limit?: number }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append('type', params.type);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
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

  async getMemoryTimeline(agentId: string, params?: { limit?: number }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
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

  // Audit Log APIs
  async getAuditLogs(params?: AuditLogFilters): Promise<AuditLogResponse> {
    const queryParams = new URLSearchParams();
    if (params?.user_id) queryParams.append('user_id', params.user_id);
    if (params?.action) queryParams.append('action', params.action);
    if (params?.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const query = queryParams.toString();
    return this.request(`/api/agent-builder/admin/audit-logs${query ? `?${query}` : ''}`);
  }

  async exportAuditLogs(format: 'csv' | 'json', params?: Omit<AuditLogFilters, 'page' | 'page_size'>): Promise<Blob> {
    const queryParams = new URLSearchParams({ format });
    if (params?.user_id) queryParams.append('user_id', params.user_id);
    if (params?.action) queryParams.append('action', params.action);
    if (params?.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE_URL}/api/agent-builder/admin/audit-logs/export?${queryParams}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) throw new Error('Failed to export audit logs');
    return response.blob();
  }

  // Optimization methods for agentflows
  async getOptimizationAnalysis(
    workflowId: string,
    daysBack: number = 30
  ): Promise<{ success: boolean; analysis: WorkflowAnalysis }> {
    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/optimization-analysis?days_back=${daysBack}`
    );
  }

  // Agentflow endpoints
  async getAgentflow(agentflowId: string): Promise<Agentflow> {
    return this.request(`/api/agent-builder/agentflows/${agentflowId}`);
  }

  async createAgentflow(data: AgentflowCreate): Promise<Agentflow> {
    return this.request('/api/agent-builder/agentflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAgentflow(agentflowId: string, data: Partial<AgentflowCreate>): Promise<Agentflow> {
    return this.request(`/api/agent-builder/agentflows/${agentflowId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAgentflow(agentflowId: string): Promise<void> {
    return this.request(`/api/agent-builder/agentflows/${agentflowId}`, {
      method: 'DELETE',
    });
  }

  async executeAgentflow(
    agentflowId: string,
    input_data: Record<string, any> = {},
    variables: Record<string, any> = {}
  ): Promise<any> {
    return this.request(`/api/agent-builder/agentflows/${agentflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ input_data, variables }),
    });
  }

  async getAgentflows(filters?: { search?: string; category?: string; tags?: string[]; is_active?: boolean; page?: number; page_size?: number }): Promise<{ agentflows: Agentflow[]; total: number; page: number; page_size: number }> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.tags) filters.tags.forEach(tag => params.append('tags', tag));
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());

    const query = params.toString();
    return this.request(`/api/agent-builder/agentflows${query ? `?${query}` : ''}`);
  }

  async getOptimizationRecommendations(
    workflowId: string,
    limit: number = 5
  ): Promise<{ success: boolean; recommendations: OptimizationSuggestion[] }> {
    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/optimization-recommendations?limit=${limit}`
    );
  }

  async getErrorRecoveryStats(
    workflowId: string
  ): Promise<{ success: boolean; error_recovery_stats: ErrorRecoveryStats }> {
    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/error-recovery-stats`
    );
  }

  async applyOptimizations(
    workflowId: string,
    suggestionIds: string[],
    autoApply: boolean = false
  ): Promise<{
    success: boolean;
    message: string;
    applied_suggestions: string[];
    auto_applied: boolean;
    next_steps: string[];
  }> {
    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/apply-optimizations`,
      {
        method: 'POST',
        body: JSON.stringify({
          suggestion_ids: suggestionIds,
          auto_apply: autoApply,
        }),
      }
    );
  }

  async getPerformancePrediction(
    workflowId: string,
    inputData?: Record<string, any>
  ): Promise<{
    success: boolean;
    prediction: PerformancePrediction;
    based_on_executions: number;
    analysis_date: string;
  }> {
    const params = inputData ? `?input_data=${encodeURIComponent(JSON.stringify(inputData))}` : '';
    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/performance-prediction${params}`
    );
  }

  async executeOptimizedAgentflow(
    workflowId: string,
    input_data: Record<string, any> = {},
    variables: Record<string, any> = {},
    enablePredictions: boolean = true,
    enableRecovery: boolean = true
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append('enable_predictions', enablePredictions.toString());
    params.append('enable_recovery', enableRecovery.toString());

    return this.request(
      `/api/agent-builder/agentflows/${workflowId}/execute-optimized?${params}`,
      {
        method: 'POST',
        body: JSON.stringify({ input_data, variables }),
      }
    );
  }

  // Utility methods for optimization insights
  async getWorkflowHealthScore(workflowId: string): Promise<{
    overall_score: number;
    performance_score: number;
    reliability_score: number;
    cost_efficiency_score: number;
    recommendations_count: number;
  }> {
    const analysis = await this.getOptimizationAnalysis(workflowId);
    const recommendations = await this.getOptimizationRecommendations(workflowId);

    const performanceScore = analysis.analysis.optimization_score;
    const reliabilityScore = analysis.analysis.success_rate;
    const costEfficiencyScore = analysis.analysis.cost_analysis.cost_efficiency_score;
    
    const overallScore = (performanceScore + reliabilityScore + costEfficiencyScore) / 3;

    return {
      overall_score: overallScore,
      performance_score: performanceScore,
      reliability_score: reliabilityScore,
      cost_efficiency_score: costEfficiencyScore,
      recommendations_count: recommendations.recommendations.length,
    };
  }

  async getOptimizationInsights(workflowId: string): Promise<{
    critical_issues: OptimizationSuggestion[];
    quick_wins: OptimizationSuggestion[];
    long_term_improvements: OptimizationSuggestion[];
    cost_savings_potential: number;
    performance_improvement_potential: number;
  }> {
    const recommendations = await this.getOptimizationRecommendations(workflowId, 20);
    const suggestions = recommendations.recommendations;

    const criticalIssues = suggestions.filter(
      s => s.priority === 'high' && s.impact === 'high'
    );
    
    const quickWins = suggestions.filter(
      s => s.implementation_effort === 'low' && s.impact !== 'low'
    );
    
    const longTermImprovements = suggestions.filter(
      s => s.implementation_effort === 'high' && s.impact === 'high'
    );

    const costSavingsPotential = suggestions
      .filter(s => s.type === 'cost')
      .reduce((sum, s) => sum + (s.estimated_improvement || 0), 0);

    const performanceImprovementPotential = suggestions
      .filter(s => s.type === 'performance')
      .reduce((sum, s) => sum + (s.estimated_improvement || 0), 0);

    return {
      critical_issues: criticalIssues,
      quick_wins: quickWins,
      long_term_improvements: longTermImprovements,
      cost_savings_potential: costSavingsPotential,
      performance_improvement_potential: performanceImprovementPotential,
    };
  }

  // Trending and recommendation methods
  async getTrendingAgents(timeRange: string = '7d', limit: number = 5): Promise<Agent[]> {
    const params = new URLSearchParams({ time_range: timeRange, limit: limit.toString() });
    const response = await this.request<{ trending_agents: Agent[] }>(`/api/agent-builder/agents/trending?${params}`);
    return response.trending_agents || [];
  }

  async getPersonalizedRecommendations(userId?: string, limit: number = 5): Promise<Agent[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (userId) params.append('user_id', userId);
    const response = await this.request<{ recommendations: Agent[] }>(`/api/agent-builder/agents/personalized-recommendations?${params}`);
    return response.recommendations || [];
  }

  async validateAgentflowIntegrity(agentflowId: string): Promise<any> {
    // Placeholder method - implement actual validation logic
    return this.request(`/api/agent-builder/agentflows/${agentflowId}/validate`);
  }

  async getAgentflowExecutionPlan(agentflowId: string): Promise<any> {
    // Placeholder method - implement actual execution plan logic
    return this.request(`/api/agent-builder/agentflows/${agentflowId}/execution-plan`);
  }

  async getAgentSharing(agentId: string): Promise<any> {
    // Placeholder method - implement actual agent sharing logic
    return this.request(`/api/agent-builder/agents/${agentId}/sharing`);
  }

  async searchUsers(query: string): Promise<any> {
    // Placeholder method - implement actual user search logic
    return this.request(`/api/users/search?q=${encodeURIComponent(query)}`);
  }

  async shareAgent(agentId: string, data: { email: string; permission: string; message?: string }): Promise<any> {
    // Placeholder method - implement actual agent sharing logic
    return this.request(`/api/agent-builder/agents/${agentId}/share`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAgentPermission(agentId: string, userId: string, permission: string): Promise<any> {
    // Placeholder method - implement actual permission update logic
    return this.request(`/api/agent-builder/agents/${agentId}/permissions/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ permission }),
    });
  }

  async removeAgentPermission(agentId: string, userId: string): Promise<any> {
    // Placeholder method - implement actual permission removal logic
    return this.request(`/api/agent-builder/agents/${agentId}/permissions/${userId}`, {
      method: 'DELETE',
    });
  }

  // Analytics methods
  async getAnalyticsOverview(agentId: string, timeRange?: string): Promise<any> {
    // Placeholder method - implement actual analytics overview logic
    const params = timeRange ? `?time_range=${timeRange}` : '';
    return this.request(`/api/agent-builder/agents/${agentId}/analytics/overview${params}`);
  }

  async getUsageAnalytics(agentId: string, timeRange?: string): Promise<any> {
    // Placeholder method - implement actual usage analytics logic
    const params = timeRange ? `?time_range=${timeRange}` : '';
    return this.request(`/api/agent-builder/agents/${agentId}/analytics/usage${params}`);
  }

  async getQualityAnalytics(agentId: string, timeRange?: string): Promise<any> {
    // Placeholder method - implement actual quality analytics logic
    const params = timeRange ? `?time_range=${timeRange}` : '';
    return this.request(`/api/agent-builder/agents/${agentId}/analytics/quality${params}`);
  }

  async getPerformanceAnalytics(agentId: string, timeRange?: string): Promise<any> {
    // Placeholder method - implement actual performance analytics logic
    const params = timeRange ? `?time_range=${timeRange}` : '';
    return this.request(`/api/agent-builder/agents/${agentId}/analytics/performance${params}`);
  }

  // Budget management methods
  async updateBudgetSettings(agentId: string, settings: any): Promise<any> {
    // Placeholder method - implement actual budget settings update logic
    return this.request(`/api/agent-builder/agents/${agentId}/budget`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }
}

export const agentBuilderAPI = new AgentBuilderAPI();