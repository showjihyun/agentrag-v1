/**
 * useAIAgentChat Hook
 * 
 * WebSocket-based real-time chat with AI agents.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface AIAgentConfig {
  provider: string;
  model: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  enable_memory?: boolean;
  memory_type?: string;
  credentials?: Record<string, string>;
}

interface UseAIAgentChatOptions {
  sessionId: string;
  nodeId: string;
  config: AIAgentConfig;
  onMessage?: (message: ChatMessage) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;
}

interface UseAIAgentChatReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  clearMessages: () => void;
  isConnected: boolean;
  isProcessing: boolean;
  error: string | null;
  reconnect: () => void;
}

export function useAIAgentChat({
  sessionId,
  nodeId,
  config,
  onMessage,
  onError,
  onStatusChange,
}: UseAIAgentChatOptions): UseAIAgentChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('⚠️ WebSocket already connected');
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/agent-builder/ai-agent-chat/ws?session_id=${sessionId}&node_id=${nodeId}`;
      
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      onStatusChange?.('connecting');
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onStatusChange?.('connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data);

          if (data.type === 'message') {
            const message: ChatMessage = {
              role: data.role || 'assistant',
              content: data.content,
              timestamp: new Date(data.timestamp),
              metadata: data.metadata,
            };
            
            setMessages((prev) => [...prev, message]);
            onMessage?.(message);
            setIsProcessing(false);
          } else if (data.type === 'error') {
            const errorMsg = data.content || 'Unknown error';
            console.error('❌ AI Agent error:', errorMsg);
            
            const errorMessage: ChatMessage = {
              role: 'assistant',
              content: `❌ Error: ${errorMsg}`,
              timestamp: new Date(data.timestamp),
            };
            
            setMessages((prev) => [...prev, errorMessage]);
            setError(errorMsg);
            onError?.(errorMsg);
            setIsProcessing(false);
          } else if (data.type === 'status') {
            console.log('📊 Status:', data.content);
            if (data.content === 'processing') {
              setIsProcessing(true);
            } else if (data.content === 'cleared') {
              setMessages([]);
              setIsProcessing(false);
            }
          } else if (data.type === 'pong') {
            // Heartbeat response
            console.log('💓 Pong received');
          }
        } catch (err) {
          console.error('❌ Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        setError('WebSocket connection error');
        onStatusChange?.('error');
        onError?.('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setIsProcessing(false);
        onStatusChange?.('disconnected');
        
        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          console.error('❌ Max reconnection attempts reached');
          setError('Connection lost. Please refresh the page.');
        }
      };
    } catch (err) {
      console.error('❌ Failed to create WebSocket:', err);
      setError('Failed to establish connection');
      onError?.('Failed to establish connection');
    }
  }, [sessionId, nodeId, onMessage, onError, onStatusChange]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsProcessing(false);
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket not connected');
      setError('Not connected to server');
      return;
    }

    if (!content.trim()) {
      console.warn('⚠️ Empty message, skipping');
      return;
    }

    try {
      // Add user message to UI immediately
      const userMessage: ChatMessage = {
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsProcessing(true);
      setError(null);

      // Send to server
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: content.trim(),
        config: config,
      }));

      console.log('📤 Message sent:', content.substring(0, 50) + '...');
    } catch (err) {
      console.error('❌ Failed to send message:', err);
      setError('Failed to send message');
      setIsProcessing(false);
    }
  }, [config]);

  const clearMessages = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'clear',
      }));
    }
    setMessages([]);
    setError(null);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect, disconnect]);

  // Connect on mount
  useEffect(() => {
    connect();
    
    // Heartbeat to keep connection alive
    const heartbeatInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Every 30 seconds

    return () => {
      clearInterval(heartbeatInterval);
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    messages,
    sendMessage,
    clearMessages,
    isConnected,
    isProcessing,
    error,
    reconnect,
  };
}
