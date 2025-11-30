/**
 * Workflow API Client
 * 
 * Handles all workflow-related API calls with proper typing and error handling.
 */

import { getAccessToken } from '../auth';
import { APIError, NetworkError } from '../error-handler';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
  data?: Record<string, any>;
}

export interface Workflow {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    settings?: Record<string, any>;
  };
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'waiting_approval';
  started_at?: string;
  completed_at?: string;
  duration?: number;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  node_executions?: NodeExecution[];
}

export interface NodeExecution {
  node_id: string;
  node_name: string;
  node_type: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input?: any;
  output?: any;
  error?: string;
}

export interface WorkflowListResponse {
  workflows: Workflow[];
  total: number;
  offset: number;
  limit: number;
}

export interface WorkflowCreateRequest {
  name: string;
  description?: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  is_public?: boolean;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  graph_definition?: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    settings?: Record<string, any>;
  };
  is_public?: boolean;
}

export interface ExecuteWorkflowRequest {
  input_data?: Record<string, any>;
}

export interface ExecuteWorkflowResponse {
  execution_id: string;
  status: string;
  message: string;
  output?: any;
  approval_id?: string;
  approval_url?: string;
}

class WorkflowApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
      ...this.getAuthHeaders(),
    };

    try {
      const response = await fetch(url, { ...options, headers });

      if (!response.ok) {
        throw await APIError.fromResponse(response);
      }

      if (response.status === 204) {
        return undefined as T;
      }

      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return response.json();
      }

      return {} as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Network connection failed');
      }
      throw error;
    }
  }

  // Workflow CRUD

  async listWorkflows(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    include_public?: boolean;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<WorkflowListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set('skip', params.skip.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.include_public !== undefined) searchParams.set('include_public', params.include_public.toString());
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.sort_order) searchParams.set('sort_order', params.sort_order);

    return this.request<WorkflowListResponse>(
      `/api/agent-builder/workflows?${searchParams.toString()}`
    );
  }

  async getWorkflow(workflowId: string): Promise<Workflow> {
    return this.request<Workflow>(`/api/agent-builder/workflows/${workflowId}`);
  }

  async createWorkflow(data: WorkflowCreateRequest): Promise<Workflow> {
    return this.request<Workflow>('/api/agent-builder/workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWorkflow(workflowId: string, data: WorkflowUpdateRequest): Promise<Workflow> {
    return this.request<Workflow>(`/api/agent-builder/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteWorkflow(workflowId: string): Promise<void> {
    return this.request<void>(`/api/agent-builder/workflows/${workflowId}`, {
      method: 'DELETE',
    });
  }

  async duplicateWorkflow(workflowId: string): Promise<Workflow> {
    return this.request<Workflow>(`/api/agent-builder/workflows/${workflowId}/duplicate`, {
      method: 'POST',
    });
  }

  // Workflow Execution

  async executeWorkflow(workflowId: string, data?: ExecuteWorkflowRequest): Promise<ExecuteWorkflowResponse> {
    return this.request<ExecuteWorkflowResponse>(`/api/agent-builder/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(data?.input_data || {}),
    });
  }

  async getExecutions(workflowId: string, params?: {
    limit?: number;
    offset?: number;
    status_filter?: string;
  }): Promise<{ executions: WorkflowExecution[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.status_filter) searchParams.set('status_filter', params.status_filter);

    return this.request(`/api/agent-builder/workflows/${workflowId}/executions?${searchParams.toString()}`);
  }

  async getExecution(workflowId: string, executionId: string): Promise<WorkflowExecution> {
    return this.request<WorkflowExecution>(
      `/api/agent-builder/workflows/${workflowId}/executions/${executionId}`
    );
  }

  // Execution Streaming (SSE)
  streamExecution(workflowId: string, executionId: string): EventSource {
    const token = getAccessToken();
    const url = new URL(`${this.baseUrl}/api/agent-builder/workflows/${workflowId}/executions/${executionId}/stream`);
    if (token) {
      url.searchParams.append('token', token);
    }
    return new EventSource(url.toString());
  }

  // Validation
  async validateWorkflow(workflowId: string): Promise<{
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    return this.request(`/api/agent-builder/workflows/${workflowId}/validate`, {
      method: 'POST',
    });
  }
}

export const workflowApi = new WorkflowApiClient();
export default workflowApi;
