import { useEffect, useRef, useState, useCallback } from 'react';
import { logger } from '@/lib/logger';

export interface NodeExecutionStatus {
  nodeId: string;
  nodeName: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'waiting';
  startTime?: number;
  endTime?: number;
  error?: string;
  output?: any;
  input?: any;
  timestamp?: number;
}

interface ExecutionStreamEvent {
  type: 'connected' | 'node_status' | 'completed' | 'error' | 'timeout' | 'close';
  node_id?: string;
  node_name?: string;
  status?: string;
  start_time?: number;
  end_time?: number;
  error?: string;
  output?: any;
  timestamp?: number;
  execution_id?: string;
  message?: string;
}

interface UseWorkflowExecutionStreamOptions {
  workflowId: string;
  executionId?: string;
  enabled?: boolean;
  onComplete?: (status: string) => void;
  onError?: (error: string) => void;
}

export function useWorkflowExecutionStream({
  workflowId,
  executionId,
  enabled = true,
  onComplete,
  onError,
}: UseWorkflowExecutionStreamOptions) {
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, NodeExecutionStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const maxRetries = 3;
  const retryDelayRef = useRef(1000); // Start with 1 second
  const isManualDisconnectRef = useRef(false); // Track manual disconnection
  
  // Use refs for callbacks to avoid dependency issues
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  const connect = useCallback(() => {
    if (!enabled || !workflowId) return;

    // Reset manual disconnect flag
    isManualDisconnectRef.current = false;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Build URL
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    let url: string;
    
    if (executionId) {
      url = `${baseUrl}/api/agent-builder/workflows/${workflowId}/executions/${executionId}/stream`;
    } else {
      url = `${baseUrl}/api/agent-builder/workflows/${workflowId}/stream`;
    }

    logger.log('🔌 Connecting to execution stream:', url);

    // Create EventSource
    const eventSource = new EventSource(url, {
      withCredentials: true,
    });

    eventSource.onopen = () => {
      logger.log('✅ SSE connection opened');
      setIsConnected(true);
      // Reset retry count on successful connection
      retryCountRef.current = 0;
      retryDelayRef.current = 1000;
      setRetryCount(0);
    };

    eventSource.onmessage = (event) => {
      try {
        const data: ExecutionStreamEvent = JSON.parse(event.data);
        logger.log('📨 SSE event received:', data);

        switch (data.type) {
          case 'connected':
            logger.log('🔗 Connected to execution:', data.execution_id);
            break;

          case 'node_status':
            if (data.node_id) {
              setNodeStatuses((prev) => ({
                ...prev,
                [data.node_id!]: {
                  nodeId: data.node_id!,
                  nodeName: data.node_name || 'Unknown',
                  status: (data.status as any) || 'pending',
                  startTime: data.start_time,
                  endTime: data.end_time,
                  error: data.error,
                  output: data.output,
                  timestamp: data.timestamp,
                },
              }));
            }
            break;

          case 'completed':
            logger.log('✅ Execution completed:', data.status);
            setIsComplete(true);
            setExecutionStatus(data.status || 'completed');
            setIsConnected(false);
            onCompleteRef.current?.(data.status || 'completed');
            eventSource.close();
            break;

          case 'error':
            logger.error('❌ Execution error:', data.message);
            setIsConnected(false);
            onErrorRef.current?.(data.message || 'Unknown error');
            eventSource.close();
            break;

          case 'timeout':
            logger.warn('⏱️ Execution timeout:', data.message);
            setIsComplete(true);
            setExecutionStatus('timeout');
            setIsConnected(false);
            onErrorRef.current?.(data.message || 'Execution timeout');
            eventSource.close();
            break;

          case 'close':
            logger.log('🔌 Connection closed');
            setIsConnected(false);
            eventSource.close();
            break;
        }
      } catch (error) {
        logger.error('Failed to parse SSE event:', error);
      }
    };

    eventSource.onerror = (error) => {
      logger.error('❌ SSE connection error:', error);
      setIsConnected(false);
      eventSource.close();
      
      // Don't retry if manually disconnected or execution is complete
      if (isManualDisconnectRef.current || isComplete) {
        logger.log('🛑 Not retrying: manual disconnect or execution complete');
        return;
      }
      
      // Implement exponential backoff retry
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current += 1;
        setRetryCount(retryCountRef.current);
        const delay = retryDelayRef.current;
        
        logger.log(`🔄 Retrying connection in ${delay}ms (attempt ${retryCountRef.current}/${maxRetries})`);
        
        setTimeout(() => {
          if (enabled && workflowId && !isManualDisconnectRef.current) {
            connect();
          }
        }, delay);
        
        // Exponential backoff: 1s, 2s, 4s
        retryDelayRef.current = Math.min(delay * 2, 10000);
      } else {
        logger.error('❌ Max retries reached, giving up');
        setRetryCount(0);
        onErrorRef.current?.('Connection failed after multiple retries. Please check if the backend server is running.');
      }
    };

    eventSourceRef.current = eventSource;
  }, [workflowId, executionId, enabled]); // Removed onComplete and onError from dependencies

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      logger.log('🔌 Disconnecting from execution stream');
      isManualDisconnectRef.current = true; // Mark as manual disconnect
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setRetryCount(0);
    }
  }, []);

  const reset = useCallback(() => {
    setNodeStatuses({});
    setIsComplete(false);
    setExecutionStatus(null);
    retryCountRef.current = 0;
    retryDelayRef.current = 1000;
    setRetryCount(0);
    isManualDisconnectRef.current = false;
  }, []);

  // Auto-connect when enabled
  useEffect(() => {
    if (enabled && workflowId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, workflowId, executionId]); // Removed connect and disconnect from dependencies

  return {
    nodeStatuses,
    isConnected,
    isComplete,
    executionStatus,
    retryCount,
    maxRetries,
    connect,
    disconnect,
    reset,
  };
}
