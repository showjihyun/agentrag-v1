/**
 * React hooks for WebSocket integration
 * Provides easy-to-use hooks for real-time features
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { getWebSocketClient } from '../websocket/client';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(getWebSocketClient());

  useEffect(() => {
    const ws = wsRef.current;

    const unsubConnect = ws.onConnect(() => {
      setIsConnected(true);
    });

    const unsubDisconnect = ws.onDisconnect(() => {
      setIsConnected(false);
    });

    ws.connect();

    return () => {
      unsubConnect();
      unsubDisconnect();
    };
  }, []);

  const send = useCallback((type: string, data: any) => {
    wsRef.current.send(type, data);
  }, []);

  const subscribe = useCallback((type: string, handler: (data: any) => void) => {
    return wsRef.current.on(type, handler);
  }, []);

  return {
    isConnected,
    send,
    subscribe,
  };
}

// Hook for real-time message updates
export function useRealtimeMessages(sessionId: string | null) {
  const { subscribe } = useWebSocket();
  const [newMessage, setNewMessage] = useState<any>(null);

  useEffect(() => {
    if (!sessionId) return;

    const unsubscribe = subscribe('message', (data) => {
      if (data.sessionId === sessionId) {
        setNewMessage(data);
      }
    });

    return unsubscribe;
  }, [sessionId, subscribe]);

  return newMessage;
}

// Hook for typing indicators
export function useTypingIndicator(sessionId: string | null) {
  const { send, subscribe } = useWebSocket();
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const unsubscribe = subscribe('typing', (data) => {
      if (data.sessionId === sessionId) {
        setIsTyping(data.isTyping);
      }
    });

    return unsubscribe;
  }, [sessionId, subscribe]);

  const sendTyping = useCallback(
    (typing: boolean) => {
      if (!sessionId) return;

      send('typing', { sessionId, isTyping: typing });

      if (typing) {
        if (typingTimeoutRef.current) {
          clearTimeout(typingTimeoutRef.current);
        }
        typingTimeoutRef.current = setTimeout(() => {
          send('typing', { sessionId, isTyping: false });
        }, 3000);
      }
    },
    [sessionId, send]
  );

  return {
    isTyping,
    sendTyping,
  };
}

// Hook for presence (online users)
export function usePresence() {
  const { subscribe } = useWebSocket();
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);

  useEffect(() => {
    const unsubscribe = subscribe('presence', (data) => {
      setOnlineUsers(data.users || []);
    });

    return unsubscribe;
  }, [subscribe]);

  return onlineUsers;
}

// Hook for notifications
export function useNotifications() {
  const { subscribe } = useWebSocket();
  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    const unsubscribe = subscribe('notification', (data) => {
      setNotifications((prev) => [...prev, data]);
    });

    return unsubscribe;
  }, [subscribe]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    clearNotifications,
  };
}
