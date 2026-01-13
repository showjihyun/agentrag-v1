/**
 * Workflow Execution Hook
 * Comprehensive hook for executing and managing workflows
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

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
  data?: Record<string, any>;
}

export interface WorkflowDefinition {
  id?: string;
  name?: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata?: Record<string, any>;
}

export interface ExecutionResult {
  success: boolean;
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  started_at: string;
  completed_at?: string;
  results?: Record<string, any>;
  node_results?: Record<string, any>;
  error?: string;
  metrics?: Record<string, any>;
}

export interface ExecutionUpdate {
  execution_id: string;
  timestamp: string;
  update_type: 'workflow_start' | 'node_start' | 'node_complete' | 'node_error' | 'workflow_complete' | 'workflow_error';
  data: Record<string, any>;
}

export interface ExecutionStatistics {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_execution_time: number;
  node_execution_counts: Record<string, number>;
  timeout_manager_stats: Record<string, any>;
  circuit_breaker_stats: Record<string, any>;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface UseWorkflowExecutionOptions {
  onExecutionStart?: (executionId: string) => void;
  onExecutionComplete?: (result: ExecutionResult) => void;
  onExecutionError?: (error: Error) => void;
  onStreamingUpdate?: (update: ExecutionUpdate) => void;
  enableAutoRetry?: boolean;
  maxRetries?: number;
}

export interface UseWorkflowExecutionReturn {
  // Execution state
  isExecuting: boolean;
  currentExecution: ExecutionResult | null;
  executionHistory: ExecutionResult[];
  streamingUpdates: ExecutionUpdate[];
  
  // Execution methods
  executeWorkflow: (
    workflow: WorkflowDefinition,
    inputData?: Record<string, any>,
    options?: {
      mode?: 'sync' | 'async' | 'streaming';
      timeout?: number;
    }
  ) => Promise<ExecutionResult | void>;
  
  executeWorkflowAsync: (
    workflow: WorkflowDefinition,
    inputData?: Record<string, any>,
    timeout?: number
  ) => Promise<{ execution_id: string; status_endpoint: string }>;
  
  executeWorkflowStreaming: (
    workflow: WorkflowDefinition,
    inputData?: Record<string, any>,
    timeout?: number
  ) => Promise<void>;
  
  // Execution management
  cancelExecution: (executionId: string) => Promise<boolean>;
  getExecutionStatus: (executionId: string) => Promise<ExecutionResult | null>;
  
  // Validation
  validateWorkflow: (workflow: WorkflowDefinition) => Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
    suggestions: string[];
    security?: {
      risk_level: string;
      warnings: string[];
    };
    performance?: {
      estimated_execution_time: number;
      performance_level: string;
      resource_usage: string;
      optimization_suggestions: string[];
    };
  }>;
  
  // Templates and statistics
  getWorkflowTemplates: () => Promise<WorkflowTemplate[]>;
  getExecutionStatistics: () => Promise<ExecutionStatistics>;
  
  // Utility methods
  clearExecutionHistory: () => void;
  clearStreamingUpdates: () => void;
}

export function useWorkflowExecution(
  options: UseWorkflowExecutionOptions = {}
): UseWorkflowExecutionReturn {
  const {
    onExecutionStart,
    onExecutionComplete,
    onExecutionError,
    onStreamingUpdate,
    enableAutoRetry = false,
    maxRetries = 3
  } = options;

  // State
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<ExecutionResult | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionResult[]>([]);
  const [streamingUpdates, setStreamingUpdates] = useState<ExecutionUpdate[]>([]);

  // Refs
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef<number>(0);

  // Execute workflow with different modes
  const executeWorkflow = useCallback(async (
    workflow: WorkflowDefinition,
    inputData: Record<string, any> = {},
    options: {
      mode?: 'sync' | 'async' | 'streaming';
      timeout?: number;
    } = {}
  ): Promise<ExecutionResult | void> => {
    const { mode = 'async', timeout } = options;

    try {
      setIsExecuting(true);
      retryCountRef.current = 0;

      const requestBody = {
        workflow_data: workflow,
        input_data: inputData,
        execution_mode: mode,
        timeout_seconds: timeout
      };

      if (mode === 'streaming') {
        await executeWorkflowStreaming(workflow, inputData, timeout);
        return;
      }

      const response = await apiClient.post('/api/agent-builder/workflow-execution/execute', requestBody);
      
      if (response.data.success) {
        const result: ExecutionResult = response.data.result;
        setCurrentExecution(result);
        
        // Add to history
        setExecutionHistory(prev => [result, ...prev.slice(0, 9)]); // Keep last 10
        
        if (onExecutionStart) {
          onExecutionStart(result.execution_id);
        }
        
        if (result.status === 'completed' && onExecutionComplete) {
          onExecutionComplete(result);
        }
        
        return result;
      } else {
        throw new Error(response.data.message || 'Execution failed');
      }

    } catch (error) {
      console.error('Workflow execution error:', error);
      
      // Auto-retry logic
      if (enableAutoRetry && retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        console.log(`Retrying execution (attempt ${retryCountRef.current}/${maxRetries})`);
        
        // Exponential backoff
        const delay = Math.pow(2, retryCountRef.current - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return executeWorkflow(workflow, inputData, options);
      }
      
      if (onExecutionError) {
        onExecutionError(error as Error);
      }
      
      throw error;
    } finally {
      setIsExecuting(false);
    }
  }, [onExecutionStart, onExecutionComplete, onExecutionError, enableAutoRetry, maxRetries]);

  // Execute workflow asynchronously
  const executeWorkflowAsync = useCallback(async (
    workflow: WorkflowDefinition,
    inputData: Record<string, any> = {},
    timeout?: number
  ): Promise<{ execution_id: string; status_endpoint: string }> => {
    try {
      const response = await apiClient.post('/api/agent-builder/workflow-execution/execute-async', {
        workflow_data: workflow,
        input_data: inputData,
        timeout_seconds: timeout
      });

      if (response.data.success) {
        const { execution_id, status_endpoint } = response.data;
        
        if (onExecutionStart) {
          onExecutionStart(execution_id);
        }
        
        return { execution_id, status_endpoint };
      } else {
        throw new Error(response.data.message || 'Async execution failed');
      }
    } catch (error) {
      if (onExecutionError) {
        onExecutionError(error as Error);
      }
      throw error;
    }
  }, [onExecutionStart, onExecutionError]);

  // Execute workflow with streaming
  const executeWorkflowStreaming = useCallback(async (
    workflow: WorkflowDefinition,
    inputData: Record<string, any> = {},
    timeout?: number
  ): Promise<void> => {
    try {
      setIsExecuting(true);
      setStreamingUpdates([]);

      // Close existing EventSource
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create request body
      const requestBody = {
        workflow_data: workflow,
        input_data: inputData,
        execution_mode: 'streaming',
        timeout_seconds: timeout
      };

      // Start streaming execution
      const response = await fetch('/api/agent-builder/workflow-execution/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                const update: ExecutionUpdate = data;
                
                setStreamingUpdates(prev => [...prev, update]);
                
                if (onStreamingUpdate) {
                  onStreamingUpdate(update);
                }

                // Handle workflow completion
                if (update.update_type === 'workflow_complete') {
                  const result: ExecutionResult = {
                    success: true,
                    execution_id: update.execution_id,
                    status: 'completed',
                    started_at: update.timestamp,
                    completed_at: update.timestamp,
                    results: update.data.results,
                    node_results: update.data.node_results,
                    metrics: {
                      execution_time_seconds: update.data.execution_time_seconds
                    }
                  };
                  
                  setCurrentExecution(result);
                  setExecutionHistory(prev => [result, ...prev.slice(0, 9)]);
                  
                  if (onExecutionComplete) {
                    onExecutionComplete(result);
                  }
                }

                // Handle workflow error
                if (update.update_type === 'workflow_error') {
                  const result: ExecutionResult = {
                    success: false,
                    execution_id: update.execution_id,
                    status: 'failed',
                    started_at: update.timestamp,
                    completed_at: update.timestamp,
                    error: update.data.error
                  };
                  
                  setCurrentExecution(result);
                  setExecutionHistory(prev => [result, ...prev.slice(0, 9)]);
                  
                  if (onExecutionError) {
                    onExecutionError(new Error(update.data.error));
                  }
                }

              } catch (parseError) {
                console.error('Error parsing streaming data:', parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('Streaming execution error:', error);
      
      if (onExecutionError) {
        onExecutionError(error as Error);
      }
      
      throw error;
    } finally {
      setIsExecuting(false);
    }
  }, [onStreamingUpdate, onExecutionComplete, onExecutionError]);

  // Cancel execution
  const cancelExecution = useCallback(async (executionId: string): Promise<boolean> => {
    try {
      const response = await apiClient.post(`/api/agent-builder/workflow-execution/cancel/${executionId}`);
      
      if (response.data.success) {
        // Update current execution if it matches
        if (currentExecution?.execution_id === executionId) {
          setCurrentExecution(prev => prev ? { ...prev, status: 'cancelled' } : null);
        }
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Cancel execution error:', error);
      return false;
    }
  }, [currentExecution]);

  // Get execution status
  const getExecutionStatus = useCallback(async (executionId: string): Promise<ExecutionResult | null> => {
    try {
      const response = await apiClient.get(`/api/agent-builder/workflow-execution/status/${executionId}`);
      
      if (response.data.success) {
        return response.data.status;
      }
      
      return null;
    } catch (error) {
      console.error('Get execution status error:', error);
      return null;
    }
  }, []);

  // Validate workflow
  const validateWorkflow = useCallback(async (workflow: WorkflowDefinition) => {
    try {
      const response = await apiClient.get('/api/agent-builder/workflow-execution/validate', {
        params: { workflow_data: workflow }
      });
      
      return response.data;
    } catch (error) {
      console.error('Workflow validation error:', error);
      throw error;
    }
  }, []);

  // Get workflow templates
  const getWorkflowTemplates = useCallback(async (): Promise<WorkflowTemplate[]> => {
    try {
      const response = await apiClient.get('/api/agent-builder/workflow-execution/templates');
      
      if (response.data.success) {
        return response.data.templates;
      }
      
      return [];
    } catch (error) {
      console.error('Get templates error:', error);
      return [];
    }
  }, []);

  // Get execution statistics
  const getExecutionStatistics = useCallback(async (): Promise<ExecutionStatistics> => {
    try {
      const response = await apiClient.get('/api/agent-builder/workflow-execution/statistics');
      
      if (response.data.success) {
        return response.data.statistics;
      }
      
      throw new Error('Failed to get statistics');
    } catch (error) {
      console.error('Get statistics error:', error);
      throw error;
    }
  }, []);

  // Utility methods
  const clearExecutionHistory = useCallback(() => {
    setExecutionHistory([]);
  }, []);

  const clearStreamingUpdates = useCallback(() => {
    setStreamingUpdates([]);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    // State
    isExecuting,
    currentExecution,
    executionHistory,
    streamingUpdates,
    
    // Execution methods
    executeWorkflow,
    executeWorkflowAsync,
    executeWorkflowStreaming,
    
    // Management methods
    cancelExecution,
    getExecutionStatus,
    
    // Validation
    validateWorkflow,
    
    // Templates and statistics
    getWorkflowTemplates,
    getExecutionStatistics,
    
    // Utility methods
    clearExecutionHistory,
    clearStreamingUpdates
  };
}