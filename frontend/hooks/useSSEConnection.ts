import { useEffect, useRef, useState, useCallback } from 'react';
import { SSEEventData } from '@/lib/types/monitoring';
import { handleSSEError, parseSSEData, validateSSEEventType } from '@/lib/utils/error-handling';

interface UseSSEConnectionOptions {
  url: string;
  enabled: boolean;
  onMessage?: (data: SSEEventData) => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
}

export function useSSEConnection({
  url,
  enabled,
  onMessage,
  onError,
  reconnectInterval = 5000,
}: UseSSEConnectionOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!enabled || eventSourceRef.current) return;

    try {
      eventSourceRef.current = new EventSource(url);

      eventSourceRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionAttempts(0);
        console.log('SSE connection established');
      };

      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = parseSSEData<SSEEventData>(event.data);
          
          if (!validateSSEEventType(data.type)) {
            console.warn('Unknown SSE event type:', data.type);
            return;
          }

          onMessage?.(data);
        } catch (error) {
          console.error('Failed to process SSE message:', error);
        }
      };

      eventSourceRef.current.onerror = (error) => {
        console.error('SSE connection error:', error);
        setIsConnected(false);
        onError?.(error);
        handleSSEError(error);

        // Attempt to reconnect with exponential backoff
        if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
          setConnectionAttempts(prev => prev + 1);
          const delay = Math.min(reconnectInterval * Math.pow(2, connectionAttempts), 30000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            cleanup();
            connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      setIsConnected(false);
    }
  }, [url, enabled, onMessage, onError, reconnectInterval, connectionAttempts, cleanup]);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      cleanup();
    }

    return cleanup;
  }, [enabled, connect, cleanup]);

  return {
    isConnected,
    connectionAttempts,
    reconnect: connect,
    disconnect: cleanup,
  };
}