/**
 * Agent Plugin WebSocket 훅
 * 실시간 플러그인 상태 업데이트를 위한 WebSocket 연결 관리
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
  
  // Zustand 스토어 액션들
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
        
        // Ping 시작
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
        
        // 자동 재연결
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
    }, 30000); // 30초마다 ping
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
        // 초기 상태 처리
        if (message.data?.plugins) {
          // 플러그인 목록 업데이트는 스토어에서 처리
        }
        if (message.data?.system_health) {
          setSystemHealth(message.data.system_health);
        }
        break;
        
      case 'plugin_status_update':
        // 플러그인 상태 업데이트
        if (message.data?.plugin_id && message.data?.status) {
          updatePluginStatus(message.data.plugin_id, message.data.status);
        }
        break;
        
      case 'plugin_execution_started':
        // 플러그인 실행 시작
        console.log('Plugin execution started:', message.data);
        break;
        
      case 'plugin_execution_progress':
        // 플러그인 실행 진행
        console.log('Plugin execution progress:', message.data);
        break;
        
      case 'plugin_execution_completed':
        // 플러그인 실행 완료
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
        // 플러그인 실행 실패
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
        // 실시간 메트릭 업데이트
        console.log('Real-time metrics:', message.data);
        break;
        
      case 'cache_stats':
        // 캐시 통계 업데이트
        console.log('Cache stats:', message.data);
        break;
        
      case 'pong':
        // Ping-Pong 응답
        break;
        
      case 'error':
        // 에러 메시지
        console.error('WebSocket error message:', message.message);
        setError(message.message || 'WebSocket error');
        break;
        
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [updatePluginStatus, setSystemHealth, addExecutionResult, setError]);

  // 플러그인 구독
  const subscribeToPlugin = useCallback((pluginId: string) => {
    sendMessage({
      type: 'subscribe_plugin',
      plugin_id: pluginId
    });
  }, [sendMessage]);

  // 플러그인 구독 해제
  const unsubscribeFromPlugin = useCallback((pluginId: string) => {
    sendMessage({
      type: 'unsubscribe_plugin',
      plugin_id: pluginId
    });
  }, [sendMessage]);

  // 실시간 메트릭 요청
  const requestRealTimeMetrics = useCallback(() => {
    sendMessage({
      type: 'get_real_time_metrics'
    });
  }, [sendMessage]);

  // 캐시 통계 요청
  const requestCacheStats = useCallback(() => {
    sendMessage({
      type: 'get_cache_stats'
    });
  }, [sendMessage]);

  // 컴포넌트 마운트/언마운트 시 연결 관리
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // 페이지 가시성 변경 시 연결 관리
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 페이지가 숨겨졌을 때 ping 중지
        stopPing();
      } else {
        // 페이지가 다시 보일 때 연결 확인 및 ping 재시작
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