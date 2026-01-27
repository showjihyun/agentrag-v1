// Flows API Client (Agentflow & Chatflow)

import { apiClient } from '../api-client';
import {
  Agentflow,
  Chatflow,
  CreateAgentflowRequest,
  CreateChatflowRequest,
  UpdateFlowRequest,
  FlowListResponse,
  FlowFilters,
  FlowExecution,
} from '../types/flows';

// Chat-related types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  workflow_id?: string;
  config?: {
    provider?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
    memory_type?: string;
    memory_config?: any;
  };
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

export interface ChatHistoryResponse {
  messages: Array<{
    id: string;
    role: string;
    content: string;
    created_at: string;
    message_metadata?: any;
  }>;
  message_count: number;
}

export class FlowsAPI {
  /**
   * Create a new Agentflow
   */
  async createAgentflow(data: CreateAgentflowRequest): Promise<Agentflow> {
    return apiClient['request']('/api/agent-builder/agentflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Get list of Agentflows
   */
  async getAgentflows(filters?: FlowFilters): Promise<FlowListResponse> {
    const params = this.buildFilterParams(filters);
    return apiClient['request'](`/api/agent-builder/agentflows?${params.toString()}`);
  }

  /**
   * Add agent to agentflow
   */
  async addAgentToAgentflow(
    agentflowId: string,
    agentData: {
      agent_id: string;
      role: string;
      name?: string;
      description?: string;
      capabilities?: string[];
      priority?: number;
      max_retries?: number;
      timeout_seconds?: number;
      dependencies?: string[];
    }
  ): Promise<any> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/agents`, {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  /**
   * Remove agent from agentflow
   */
  async removeAgentFromAgentflow(
    agentflowId: string,
    agentflowAgentId: string
  ): Promise<void> {
    return apiClient['request'](
      `/api/agent-builder/agentflows/${agentflowId}/agents/${agentflowAgentId}`,
      {
        method: 'DELETE',
      }
    );
  }

  /**
   * Get agentflow execution plan
   */
  async getAgentflowExecutionPlan(agentflowId: string): Promise<any> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/execution-plan`);
  }

  /**
   * Execute agentflow
   */
  async executeAgentflow(agentflowId: string, inputData: Record<string, any>): Promise<any> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(inputData),
    });
  }

  /**
   * Create a new Chatflow
   */
  async createChatflow(data: CreateChatflowRequest): Promise<Chatflow> {
    return apiClient['request']('/api/agent-builder/chatflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Get list of Chatflows
   */
  async getChatflows(filters?: FlowFilters): Promise<FlowListResponse> {
    const params = this.buildFilterParams(filters);
    return apiClient['request'](`/api/agent-builder/chatflows?${params.toString()}`);
  }

  /**
   * Get all flows (both Agentflow and Chatflow)
   */
  async getFlows(filters?: FlowFilters): Promise<FlowListResponse> {
    const params = this.buildFilterParams(filters);
    return apiClient['request'](`/api/agent-builder/flows?${params.toString()}`);
  }

  /**
   * Get a specific flow by ID
   */
  async getFlow(id: string): Promise<Agentflow | Chatflow> {
    return apiClient['request'](`/api/agent-builder/flows/${id}`);
  }

  /**
   * Update a flow
   */
  async updateFlow(id: string, data: UpdateFlowRequest): Promise<Agentflow | Chatflow> {
    return apiClient['request'](`/api/agent-builder/flows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a flow
   */
  async deleteFlow(id: string): Promise<void> {
    return apiClient['request'](`/api/agent-builder/flows/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Execute a flow
   */
  async executeFlow(id: string, inputData: Record<string, any>): Promise<FlowExecution> {
    return apiClient['request'](`/api/agent-builder/flows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ input_data: inputData }),
    });
  }

  /**
   * Get execution history for a flow
   */
  async getExecutions(flowId: string, limit: number = 20, offset: number = 0): Promise<{
    executions: FlowExecution[];
    total: number;
  }> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    return apiClient['request'](
      `/api/agent-builder/flows/${flowId}/executions?${params.toString()}`
    );
  }

  /**
   * Get a specific execution
   */
  async getExecution(executionId: string): Promise<FlowExecution> {
    return apiClient['request'](`/api/agent-builder/executions/${executionId}`);
  }

  /**
   * Cancel a running execution
   */
  async cancelExecution(executionId: string): Promise<void> {
    return apiClient['request'](`/api/agent-builder/executions/${executionId}/cancel`, {
      method: 'POST',
    });
  }

  /**
   * Get available agents for AgentFlow
   */
  async getAvailableAgents(filters?: {
    search?: string;
    agent_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    agents: Array<{
      id: string;
      name: string;
      description: string;
      agent_type: string;
      llm_provider: string;
      llm_model: string;
      configuration: any;
      tools: Array<{ tool_id: string; configuration: any }>;
      capabilities: string[];
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.agent_type) params.append('agent_type', filters.agent_type);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());

    return apiClient['request'](`/api/agent-builder/agentflows/available-agents?${params.toString()}`);
  }

  /**
   * Add agent to AgentFlow
   */
  async addAgentToAgentflow(agentflowId: string, agentData: {
    agent_id: string;
    name: string;
    role: string;
    description?: string;
    capabilities?: string[];
    priority?: number;
    max_retries?: number;
    timeout_seconds?: number;
    dependencies?: string[];
  }): Promise<{
    id: string;
    agent_id: string;
    name: string;
    role: string;
    description: string;
    capabilities: string[];
    priority: number;
    max_retries: number;
    timeout_seconds: number;
    dependencies: string[];
    created_at: string;
    agent_details: {
      name: string;
      description: string;
      llm_provider: string;
      llm_model: string;
      agent_type: string;
    };
  }> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/agents`, {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  /**
   * Update agent in AgentFlow
   */
  async updateAgentflowAgent(agentflowId: string, agentAssociationId: string, agentData: {
    agent_id: string;
    name: string;
    role: string;
    description?: string;
    capabilities?: string[];
    priority?: number;
    max_retries?: number;
    timeout_seconds?: number;
    dependencies?: string[];
  }): Promise<{
    id: string;
    agent_id: string;
    name: string;
    role: string;
    description: string;
    capabilities: string[];
    priority: number;
    max_retries: number;
    timeout_seconds: number;
    dependencies: string[];
    created_at: string;
  }> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/agents/${agentAssociationId}`, {
      method: 'PUT',
      body: JSON.stringify(agentData),
    });
  }

  /**
   * Remove agent from AgentFlow
   */
  async removeAgentFromAgentflow(agentflowId: string, agentAssociationId: string): Promise<void> {
    return apiClient['request'](`/api/agent-builder/agentflows/${agentflowId}/agents/${agentAssociationId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Build filter parameters for API requests
   */
  private buildFilterParams(filters?: FlowFilters): URLSearchParams {
    const params = new URLSearchParams();
    
    if (filters?.flow_type) params.append('flow_type', filters.flow_type);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.tags) filters.tags.forEach(tag => params.append('tags', tag));
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());
    if (filters?.sort_by) params.append('sort_by', filters.sort_by);
    if (filters?.sort_order) params.append('sort_order', filters.sort_order);
    
    return params;
  }

  // ============================================================================
  // CHATFLOW CHAT METHODS
  // ============================================================================

  /**
   * Send a chat message to a chatflow
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient['request']('/api/agent-builder/chatflow/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Send a chat message to a specific workflow
   */
  async sendWorkflowChatMessage(workflowId: string, request: Omit<ChatRequest, 'workflow_id'>): Promise<ChatResponse> {
    return apiClient['request'](`/api/agent-builder/chatflow/workflows/${workflowId}/chat`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get chat history for a session
   */
  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}/history`);
  }

  /**
   * Clear chat session
   */
  async clearChatSession(sessionId: string): Promise<void> {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Create a streaming chat connection
   */
  createChatStream(request: ChatRequest): EventSource {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const params = new URLSearchParams({
      message: request.message,
      ...(request.session_id && { session_id: request.session_id }),
      ...(request.workflow_id && { workflow_id: request.workflow_id }),
      ...(request.config && { config: JSON.stringify(request.config) }),
      ...(token && { token: token }),
    });

    return new EventSource(`${apiClient.baseURL}/api/agent-builder/chatflow/chat/stream?${params.toString()}`);
  }

  /**
   * Create a streaming chat connection for a specific workflow
   */
  createWorkflowChatStream(workflowId: string, request: Omit<ChatRequest, 'workflow_id'>): EventSource {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const isDevelopment = process.env.NODE_ENV === 'development';
    
    console.log('Token from localStorage:', token ? 'Present' : 'Missing');
    console.log('Environment:', isDevelopment ? 'Development' : 'Production');
    
    const params = new URLSearchParams({
      message: request.message,
      ...(request.session_id && { session_id: request.session_id }),
      ...(request.config && { config: JSON.stringify(request.config) }),
    });

    // Add token to URL params since EventSource doesn't support custom headers
    if (token) {
      // Use the actual token (real or fake)
      params.append('token', token);
      console.log('Token added to URL params');
    } else if (isDevelopment) {
      // In development mode, use dummy token if no token exists at all
      console.log('🔧 Development mode: Using dummy token for EventSource');
      params.append('token', 'dev-dummy-token');
    } else {
      console.warn('No token available for EventSource authentication');
    }

    const url = `${apiClient.baseURL}/api/agent-builder/chatflow/workflows/${workflowId}/chat/stream?${params.toString()}`;
    console.log('Creating EventSource with URL:', url.replace(/token=[^&]+/, 'token=***'));
    
    return new EventSource(url);
  }
}

export const flowsAPI = new FlowsAPI();

// Session management API methods
export const sessionAPI = {
  // List user sessions
  async listSessions(params?: {
    chatflow_id?: string;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.chatflow_id) searchParams.append('chatflow_id', params.chatflow_id);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    return apiClient['request'](`/api/agent-builder/chatflow/sessions?${searchParams}`);
  },

  // Get session details with messages
  async getSession(sessionId: string) {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}`);
  },

  // Delete session
  async deleteSession(sessionId: string) {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  // Export session data
  async exportSession(sessionId: string) {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}/export`);
  },

  // Clear session messages
  async clearSession(sessionId: string) {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}/clear`, {
      method: 'POST',
    });
  },

  // Get available memory strategies
  async getMemoryStrategies() {
    return apiClient['request']('/api/agent-builder/chatflow/memory/strategies');
  },

  // Update session memory configuration
  async updateSessionMemory(sessionId: string, memoryConfig: {
    strategy?: string;
    max_messages?: number;
    summary_threshold?: number;
    similarity_threshold?: number;
    buffer_weight?: number;
    summary_weight?: number;
    vector_weight?: number;
  }) {
    return apiClient['request'](`/api/agent-builder/chatflow/sessions/${sessionId}/memory`, {
      method: 'PUT',
      body: JSON.stringify(memoryConfig),
    });
  },
};