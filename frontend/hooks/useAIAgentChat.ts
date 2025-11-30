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
  enabled?: boolean;
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
  enabled = true,
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
  const hasAttemptedConnectionRef = useRef(false);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!enabled) {
      console.log('⚠️ WebSocket connection disabled');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('⚠️ WebSocket already connected');
      return;
    }

    try {
      // Use environment variable for API URL if available, otherwise use current host
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      let wsUrl: string;
      
      if (apiUrl) {
        // Convert HTTP URL to WebSocket URL
        const wsProtocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
        const wsHost = apiUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
        wsUrl = `${wsProtocol}//${wsHost}/api/agent-builder/ai-agent-chat/ws?session_id=${sessionId}&node_id=${nodeId}`;
      } else {
        // Fallback to current host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/api/agent-builder/ai-agent-chat/ws?session_id=${sessionId}&node_id=${nodeId}`;
      }
      
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      console.log('📍 API URL:', apiUrl || 'Using current host');
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
        const errorMsg = 'WebSocket connection error. Please check if the backend server is running.';
        setError(errorMsg);
        onError?.(errorMsg);
        onStatusChange?.('error');
        onError?.('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setIsProcessing(false);
        onStatusChange?.('disconnected');
        
        // Handle different close codes
        if (event.code === 1000 || event.code === 1001) {
          // Normal closure
          console.log('✅ WebSocket closed normally');
          setError(null);
        } else if (event.code === 1005) {
          // No status code received (common when server doesn't exist or endpoint not found)
          console.warn('⚠️ WebSocket closed without status code (1005) - Server may not be running');
          setError('Cannot connect to AI Agent server. Please check if the backend is running.');
          onError?.('Cannot connect to AI Agent server. Please check if the backend is running.');
        } else if (event.code === 1006) {
          // Abnormal closure (connection lost)
          console.warn('⚠️ WebSocket connection lost abnormally (1006)');
          setError('Connection lost unexpectedly. Click Reconnect to try again.');
          onError?.('Connection lost unexpectedly. Click Reconnect to try again.');
        } else {
          // Other unexpected closures
          console.warn(`⚠️ WebSocket closed unexpectedly (code: ${event.code})`);
          setError(`Connection closed (code: ${event.code}). Click Reconnect to try again.`);
          onError?.(`Connection closed (code: ${event.code}). Click Reconnect to try again.`);
        }
      };
    } catch (err) {
      console.error('❌ Failed to create WebSocket:', err);
      setError('Failed to establish connection');
      onError?.('Failed to establish connection');
    }
  }, [enabled, sessionId, nodeId, onMessage, onError, onStatusChange]);

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
      const messagePayload = {
        type: 'message',
        content: content.trim(),
        config: config,
      };
      
      console.log('📤 Sending message with config:', {
        provider: config.provider,
        model: config.model,
        hasCredentials: !!config.credentials,
        credentialsKeys: config.credentials ? Object.keys(config.credentials) : [],
        hasApiKey: !!config.credentials?.api_key,
        apiKeyLength: config.credentials?.api_key?.length,
        fullConfig: config
      });
      
      wsRef.current.send(JSON.stringify(messagePayload));

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
    console.log('🔄 Manual reconnect triggered');
    disconnect();
    reconnectAttemptsRef.current = 0;
    hasAttemptedConnectionRef.current = false;
    setError(null);
    
    // Wait a bit before reconnecting
    setTimeout(() => {
      if (enabled) {
        hasAttemptedConnectionRef.current = true;
        connect();
      }
    }, 100);
  }, [enabled, connect, disconnect]);

  // Connect on mount (only if enabled) - use ref to track if we've already tried
  useEffect(() => {
    if (!enabled) {
      console.log('⚠️ WebSocket disabled, disconnecting if connected');
      disconnect();
      setError(null);
      hasAttemptedConnectionRef.current = false;
      return;
    }

    // Only attempt connection once per enable
    if (hasAttemptedConnectionRef.current) {
      console.log('⚠️ Already attempted connection, skipping');
      return;
    }

    console.log('🔌 WebSocket enabled, attempting to connect');
    hasAttemptedConnectionRef.current = true;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]); // Only depend on enabled, not connect/disconnect

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
