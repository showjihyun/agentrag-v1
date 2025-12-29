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
}

export const flowsAPI = new FlowsAPI();
