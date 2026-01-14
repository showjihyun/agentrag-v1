/**
 * Agent Plugin WebSocket Hook
 * WebSocket connection management for real-time plugin status updates
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { usePluginStore } from '@/lib/stores/plugin-store';

interface WebSocketMessage {
  type: string;
  data?: any;
  plugin_id?: string;
  message?: string;
  timestamp?: string;
}

interface UsePluginWebSocketOptions {
  userId: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const usePluginWebSocket = ({
  userId,
  autoReconnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5
}: UsePluginWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  // Zustand store actions
  const {
    updatePluginStatus,
    setSystemHealth,
    addExecutionResult,
    setError
  } = usePluginStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/agent-plugins/ws/${userId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Plugin WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
        
        // Start ping
        startPing();
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('Plugin WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        stopPing();
        
        // Auto reconnect
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect();
        }
      };
      
      ws.onerror = (error) => {
        console.error('Plugin WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to create WebSocket connection');
    }
  }, [userId, autoReconnect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopPing();
    setIsConnected(false);
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    reconnectAttemptsRef.current += 1;
    console.log(`Scheduling reconnect attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, reconnectInterval);
  }, [connect, reconnectInterval, maxReconnectAttempts]);

  const startPing = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }
    }, 30000); // Ping every 30 seconds
  }, []);

  const stopPing = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'initial_state':
        // Handle initial state
        if (message.data?.plugins) {
          // Plugin list update is handled in store
        }
        if (message.data?.system_health) {
          setSystemHealth(message.data.system_health);
        }
        break;
        
      case 'plugin_status_update':
        // Plugin status update
        if (message.data?.plugin_id && message.data?.status) {
          updatePluginStatus(message.data.plugin_id, message.data.status);
        }
        break;
        
      case 'plugin_execution_started':
        // Plugin execution started
        console.log('Plugin execution started:', message.data);
        break;
        
      case 'plugin_execution_progress':
        // Plugin execution progress
        console.log('Plugin execution progress:', message.data);
        break;
        
      case 'plugin_execution_completed':
        // Plugin execution completed
        if (message.data?.plugin_id) {
          addExecutionResult(message.data.plugin_id, {
            success: true,
            result: message.data.result,
            duration: message.data.duration,
            timestamp: message.data.timestamp
          });
        }
        break;
        
      case 'plugin_execution_failed':
        // Plugin execution failed
        if (message.data?.plugin_id) {
          addExecutionResult(message.data.plugin_id, {
            success: false,
            error: message.data.error,
            duration: message.data.duration,
            timestamp: message.data.timestamp
          });
        }
        break;
        
      case 'real_time_metrics':
        // Real-time metrics update
        console.log('Real-time metrics:', message.data);
        break;
        
      case 'cache_stats':
        // Cache stats update
        console.log('Cache stats:', message.data);
        break;
        
      case 'pong':
        // Ping-Pong response
        break;
        
      case 'error':
        // Error message
        console.error('WebSocket error message:', message.message);
        setError(message.message || 'WebSocket error');
        break;
        
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [updatePluginStatus, setSystemHealth, addExecutionResult, setError]);

  // Subscribe to plugin
  const subscribeToPlugin = useCallback((pluginId: string) => {
    sendMessage({
      type: 'subscribe_plugin',
      plugin_id: pluginId
    });
  }, [sendMessage]);

  // Unsubscribe from plugin
  const unsubscribeFromPlugin = useCallback((pluginId: string) => {
    sendMessage({
      type: 'unsubscribe_plugin',
      plugin_id: pluginId
    });
  }, [sendMessage]);

  // Request real-time metrics
  const requestRealTimeMetrics = useCallback(() => {
    sendMessage({
      type: 'get_real_time_metrics'
    });
  }, [sendMessage]);

  // Request cache stats
  const requestCacheStats = useCallback(() => {
    sendMessage({
      type: 'get_cache_stats'
    });
  }, [sendMessage]);

  // Manage connection on component mount/unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Manage connection on page visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Stop ping when page is hidden
        stopPing();
      } else {
        // Check connection and restart ping when page is visible again
        if (isConnected) {
          startPing();
        } else {
          connect();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, connect, startPing, stopPing]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribeToPlugin,
    unsubscribeFromPlugin,
    requestRealTimeMetrics,
    requestCacheStats,
    reconnectAttempts: reconnectAttemptsRef.current
  };
};