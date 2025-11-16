/**
 * Server-Sent Events (SSE) hook for real-time updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface SSEOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  withCredentials?: boolean;
}

export interface SSEState<T = any> {
  data: T | null;
  error: Error | null;
  isConnected: boolean;
  isConnecting: boolean;
  reconnectCount: number;
}

export function useSSE<T = any>(
  url: string | null,
  options: SSEOptions = {}
) {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    withCredentials = false,
  } = options;

  const [state, setState] = useState<SSEState<T>>({
    data: null,
    error: null,
    isConnected: false,
    isConnecting: false,
    reconnectCount: 0,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!url) return;

    cleanup();

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const eventSource = new EventSource(url, { withCredentials });
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
        }));
        reconnectCountRef.current = 0;
        onOpen?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setState(prev => ({ ...prev, data: parsedData }));
          onMessage?.(parsedData);
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
        }
      };

      eventSource.onerror = (event) => {
        const error = new Error('SSE connection error');
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error,
        }));

        onError?.(event);
        cleanup();

        // Attempt reconnection only if enabled and not manually disconnected
        if (reconnect && reconnectCountRef.current < maxReconnectAttempts && url) {
          reconnectCountRef.current++;
          
          setState(prev => ({
            ...prev,
            reconnectCount: reconnectCountRef.current,
          }));

          // Exponential backoff with jitter to prevent thundering herd
          const baseDelay = reconnectInterval * Math.pow(2, reconnectCountRef.current - 1);
          const jitter = Math.random() * 1000; // Add up to 1s random jitter
          const delay = Math.min(baseDelay + jitter, 30000); // Cap at 30s
          
          console.log(`🔄 Reconnecting SSE in ${Math.round(delay)}ms (attempt ${reconnectCountRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (url) { // Double-check URL still exists
              connect();
            }
          }, delay);
        } else if (reconnectCountRef.current >= maxReconnectAttempts) {
          console.error('❌ Max reconnection attempts reached. Giving up.');
          onClose?.();
        }
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create EventSource');
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error,
      }));
    }
  }, [url, withCredentials, onOpen, onMessage, onError, onClose, reconnect, reconnectInterval, maxReconnectAttempts, cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
    onClose?.();
  }, [cleanup, onClose]);

  const reset = useCallback(() => {
    disconnect();
    reconnectCountRef.current = 0;
    setState({
      data: null,
      error: null,
      isConnected: false,
      isConnecting: false,
      reconnectCount: 0,
    });
  }, [disconnect]);

  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [url, connect, cleanup]);

  return {
    ...state,
    connect,
    disconnect,
    reset,
  };
}

/**
 * Hook for agent execution with SSE
 */
export function useAgentExecution(agentId: string | null) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  const { isConnected, error, connect, disconnect } = useSSE(
    agentId ? `/api/agent-builder/executions/agents/${agentId}/stream` : null,
    {
      onMessage: (data) => {
        if (data.type === 'step') {
          setMessages(prev => [...prev, data]);
        } else if (data.type === 'result') {
          setExecutionResult(data);
          setIsExecuting(false);
        } else if (data.type === 'error') {
          setIsExecuting(false);
        }
      },
      onOpen: () => {
        setIsExecuting(true);
        setMessages([]);
        setExecutionResult(null);
      },
      onClose: () => {
        setIsExecuting(false);
      },
      reconnect: false, // Don't reconnect for executions
    }
  );

  const execute = useCallback((input: any) => {
    setMessages([]);
    setExecutionResult(null);
    connect();
  }, [connect]);

  const cancel = useCallback(() => {
    disconnect();
    setIsExecuting(false);
  }, [disconnect]);

  return {
    messages,
    isExecuting,
    executionResult,
    error,
    isConnected,
    execute,
    cancel,
  };
}
