/**
 * Workflow Debug API Client
 * 
 * Provides methods for interacting with workflow debugging features
 */

import { api } from './index';

export interface Breakpoint {
  node_id: string;
  enabled: boolean;
  condition?: string;
  hit_count: number;
}

export interface ExecutionState {
  node_id: string;
  timestamp: Date;
  status: 'idle' | 'running' | 'success' | 'error' | 'paused';
  input_data?: any;
  output_data?: any;
  error?: string;
  duration_ms?: number;
  memory_mb?: number;
  cpu_percent?: number;
}

export interface NodeMetrics {
  node_id: string;
  node_name: string;
  executions: number;
  avg_duration_ms: number;
  success_rate: number;
  error_rate: number;
  avg_memory_mb: number;
  avg_cpu_percent: number;
}

export interface PerformanceMetrics {
  total_duration_ms: number;
  avg_duration_ms: number;
  success_rate: number;
  error_rate: number;
  node_metrics: Record<string, NodeMetrics>;
}

export interface Bottleneck {
  node_id: string;
  node_name: string;
  percentage: number;
  avg_duration_ms: number;
  executions: number;
}

export interface Recommendation {
  type: string;
  severity: 'low' | 'medium' | 'high';
  title: string;
  description: string;
}

export interface DebugSession {
  is_debugging: boolean;
  is_paused: boolean;
  current_node_id?: string;
  breakpoints: Breakpoint[];
  execution_history: ExecutionState[];
  performance_metrics: PerformanceMetrics;
  bottlenecks: Bottleneck[];
  recommendations: Recommendation[];
}

export const workflowDebugApi = {
  /**
   * Start debug session
   */
  async startDebugSession(workflowId: string): Promise<{ message: string; is_debugging: boolean }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/start`);
    return response.data;
  },

  /**
   * Stop debug session
   */
  async stopDebugSession(workflowId: string): Promise<{ message: string; is_debugging: boolean }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/stop`);
    return response.data;
  },

  /**
   * Add breakpoint
   */
  async addBreakpoint(
    workflowId: string,
    nodeId: string,
    condition?: string
  ): Promise<Breakpoint> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/breakpoints`, {
      node_id: nodeId,
      condition,
    });
    return response.data;
  },

  /**
   * Remove breakpoint
   */
  async removeBreakpoint(workflowId: string, nodeId: string): Promise<{ message: string }> {
    const response = await api.delete(`/agent-builder/debug/${workflowId}/breakpoints/${nodeId}`);
    return response.data;
  },

  /**
   * Toggle breakpoint
   */
  async toggleBreakpoint(
    workflowId: string,
    nodeId: string
  ): Promise<{ message: string; enabled: boolean }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/breakpoints/${nodeId}/toggle`);
    return response.data;
  },

  /**
   * List all breakpoints
   */
  async listBreakpoints(workflowId: string): Promise<Breakpoint[]> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/breakpoints`);
    return response.data;
  },

  /**
   * Continue execution
   */
  async continueExecution(workflowId: string): Promise<{ message: string }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/continue`);
    return response.data;
  },

  /**
   * Step over
   */
  async stepOver(workflowId: string): Promise<{ message: string }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/step-over`);
    return response.data;
  },

  /**
   * Step into
   */
  async stepInto(workflowId: string): Promise<{ message: string }> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/step-into`);
    return response.data;
  },

  /**
   * Get execution history
   */
  async getExecutionHistory(workflowId: string): Promise<ExecutionState[]> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/history`);
    return response.data.map((state: any) => ({
      ...state,
      timestamp: new Date(state.timestamp),
    }));
  },

  /**
   * Get current execution state
   */
  async getCurrentState(workflowId: string): Promise<ExecutionState | null> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/current-state`);
    if (!response.data) return null;
    return {
      ...response.data,
      timestamp: new Date(response.data.timestamp),
    };
  },

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(workflowId: string): Promise<PerformanceMetrics> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/metrics`);
    return response.data;
  },

  /**
   * Get bottlenecks
   */
  async getBottlenecks(
    workflowId: string,
    thresholdPercent: number = 20
  ): Promise<Bottleneck[]> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/bottlenecks`, {
      params: { threshold_percent: thresholdPercent },
    });
    return response.data;
  },

  /**
   * Get optimization recommendations
   */
  async getRecommendations(workflowId: string): Promise<Recommendation[]> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/recommendations`);
    return response.data;
  },

  /**
   * Get complete debug session
   */
  async getDebugSession(workflowId: string): Promise<DebugSession> {
    const response = await api.get(`/agent-builder/debug/${workflowId}/session`);
    return {
      ...response.data,
      execution_history: response.data.execution_history.map((state: any) => ({
        ...state,
        timestamp: new Date(state.timestamp),
      })),
    };
  },

  /**
   * Time travel to specific execution
   */
  async timeTravel(workflowId: string, timestamp: Date): Promise<ExecutionState> {
    const response = await api.post(`/agent-builder/debug/${workflowId}/time-travel`, {
      timestamp: timestamp.toISOString(),
    });
    return {
      ...response.data,
      timestamp: new Date(response.data.timestamp),
    };
  },

  /**
   * Clear debug session
   */
  async clearDebugSession(workflowId: string): Promise<{ message: string }> {
    const response = await api.delete(`/agent-builder/debug/${workflowId}/session`);
    return response.data;
  },
};
