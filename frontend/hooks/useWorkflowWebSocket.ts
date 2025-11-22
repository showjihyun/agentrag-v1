import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';

export interface WorkflowStatus {
  workflow_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  current_node_id?: string;
  progress_percent: number;
  completed_nodes: number;
  total_nodes: number;
  start_time?: string;
  end_time?: string;
  error?: string;
}

interface UseWorkflowWebSocketOptions {
  onStatusChange?: (status: WorkflowStatus) => void;
  onError?: (error: Error) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * WebSocket hook for real-time workflow status updates
 */
export function useWorkflowWebSocket(
  workflowId: string,
  options: UseWorkflowWebSocketOptions = {}
) {
  const {
    onStatusChange,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [status, setStatus] = useState<WorkflowStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }

      // Determine WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/workflow/${workflowId}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        toast.success('Connected to workflow updates');
      };

      ws.onmessage = (event) => {
        try {
          const data: WorkflowStatus = JSON.parse(event.data);
          setStatus(data);
          onStatusChange?.(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        const wsError = new Error('WebSocket connection error');
        setError(wsError);
        onError?.(wsError);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // Attempt to reconnect if not a normal closure
        if (
          event.code !== 1000 &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++;
          console.log(
            `Reconnecting... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          toast.error('Failed to connect to workflow updates');
        }
      };
    } catch (err) {
      const connectError =
        err instanceof Error ? err : new Error('Failed to connect');
      setError(connectError);
      onError?.(connectError);
    }
  }, [workflowId, onStatusChange, onError, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    isConnected,
    error,
    connect,
    disconnect,
    send,
  };
}
