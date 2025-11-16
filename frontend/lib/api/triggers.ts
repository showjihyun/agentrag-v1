/**
 * Triggers API client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Trigger {
  id: string;
  workflow_id: string;
  workflow_name: string;
  name: string;
  description?: string;
  trigger_type: 'webhook' | 'schedule' | 'api' | 'chat' | 'manual';
  is_active: boolean;
  config: Record<string, any>;
  last_triggered_at?: string;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

export interface TriggerExecution {
  id: string;
  workflow_id: string;
  trigger_type: string;
  trigger_id?: string;
  trigger_name?: string;
  status: 'success' | 'failed' | 'running' | 'cancelled';
  error_message?: string;
  duration_ms?: number;
  triggered_at: string;
  completed_at?: string;
}

export interface TriggerStats {
  total_triggers: number;
  active_triggers: number;
  inactive_triggers: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  by_type: Record<string, number>;
}

export interface CreateTriggerRequest {
  workflow_id: string;
  name: string;
  description?: string;
  trigger_type: string;
  is_active?: boolean;
  config: Record<string, any>;
}

export interface UpdateTriggerRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  config?: Record<string, any>;
}

export interface ManualExecutionRequest {
  input_data?: Record<string, any>;
}

export const triggersAPI = {
  /**
   * List all triggers
   */
  async listTriggers(params?: {
    workflow_id?: string;
    trigger_type?: string;
    is_active?: boolean;
  }): Promise<Trigger[]> {
    const queryParams = new URLSearchParams();
    if (params?.workflow_id) queryParams.append('workflow_id', params.workflow_id);
    if (params?.trigger_type) queryParams.append('trigger_type', params.trigger_type);
    if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
    
    const url = `${API_BASE_URL}/api/agent-builder/triggers${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to list triggers: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Get trigger details
   */
  async getTrigger(triggerId: string, triggerType: string): Promise<Trigger> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Create a new trigger
   */
  async createTrigger(data: CreateTriggerRequest): Promise<Trigger> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Update trigger
   */
  async updateTrigger(
    triggerId: string,
    triggerType: string,
    data: UpdateTriggerRequest
  ): Promise<{ success: boolean; message: string }> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Delete trigger
   */
  async deleteTrigger(
    triggerId: string,
    triggerType: string
  ): Promise<{ success: boolean; message: string }> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Activate trigger
   */
  async activateTrigger(
    triggerId: string,
    triggerType: string
  ): Promise<{ success: boolean; message: string }> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}/activate?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to activate trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Deactivate trigger
   */
  async deactivateTrigger(
    triggerId: string,
    triggerType: string
  ): Promise<{ success: boolean; message: string }> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}/deactivate?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to deactivate trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Execute trigger manually
   */
  async executeTrigger(
    triggerId: string,
    triggerType: string,
    data?: ManualExecutionRequest
  ): Promise<{
    success: boolean;
    execution_id?: string;
    trigger_execution_id?: string;
    error?: string;
  }> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}/execute?trigger_type=${triggerType}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data || {}),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to execute trigger: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Get trigger execution history
   */
  async getTriggerHistory(
    triggerId: string,
    triggerType: string,
    limit: number = 50
  ): Promise<TriggerExecution[]> {
    const url = `${API_BASE_URL}/api/agent-builder/triggers/${triggerId}/history?trigger_type=${triggerType}&limit=${limit}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get trigger history: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Get trigger statistics
   */
  async getTriggerStats(workflowId?: string): Promise<TriggerStats> {
    const queryParams = workflowId ? `?workflow_id=${workflowId}` : '';
    const url = `${API_BASE_URL}/api/agent-builder/triggers/stats/summary${queryParams}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get trigger stats: ${response.statusText}`);
    }
    
    return response.json();
  },
};
