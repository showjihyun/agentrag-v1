'use client';

/**
 * Chatflow Server-Sent Events (SSE) Hook
 * 
 * Provides real-time streaming for chatflow conversations using SSE.
 * More reliable than WebSocket for one-way communication with automatic reconnection.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface StreamEvent {
  event: string;
  data: Record<string, any>;
  id?: string;
}

export interface ChatflowSSEState {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  
  // Chat state
  messages: ChatMessage[];
  isProcessing: boolean;
  currentResponse: string;
  
  // Session info
  sessionId: string | null;
  
  // Streaming info
  thinkingStep: string | null;
  toolCalls: Array<{ name: string; parameters: any; result?: any }>;
}

export interface UseChatflowSSEOptions {
  chatflowId: string;
  sessionId?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

export interface UseChatflowSSEReturn {
  // State
  state: ChatflowSSEState;
  
  // Actions
  sendMessage: (message: string, context?: Record<string, any>) => Promise<void>;
  clearHistory: () => Promise<void>;
  reconnect: () => void;
  disconnect: () => void;
  
  // Utils
  isReady: boolean;
}

export function useChatflowSSE({
  chatflowId,
  sessionId: initialSessionId,
  autoReconnect = true,
  maxReconnectAttempts = 5,
  reconnectInterval = 3000,
}: UseChatflowSSEOptions): UseChatflowSSEReturn {
  const { toast } = useToast();
  
  // State
  const [state, setState] = useState<ChatflowSSEState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    messages: [],
    isProcessing: false,
    currentResponse: '',
    sessionId: initialSessionId || null,
    thinkingStep: null,
    toolCalls: [],
  });
  
  // Refs
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);
  
  // Event handlers
  const handleStreamEvent = useCallback((event: StreamEvent) => {
    setState(prev => {
      const newState = { ...prev };
      
      switch (event.event) {
        case 'session_start':
          newState.sessionId = event.data.session_id;
          newState.isProcessing = true;
          newState.currentResponse = '';
          newState.thinkingStep = null;
          newState.toolCalls = [];
          currentMessageIdRef.current = `msg_${Date.now()}`;
          break;
          
        case 'message_received':
          // Add user message to history
          newState.messages = [...prev.messages, {
            id: `user_${Date.now()}`,
            type: 'user',
            content: event.data.message,
            timestamp: event.data.timestamp,
          }];
          break;
          
        case 'processing_start':
          newState.isProcessing = true;
          break;
          
        case 'thinking':
          newState.thinkingStep = event.data.description || event.data.step;
          break;
          
        case 'tool_call':
          newState.toolCalls = [...prev.toolCalls, {
            name: event.data.tool_name,
            parameters: event.data.parameters,
          }];
          break;
          
        case 'tool_result':
          newState.toolCalls = prev.toolCalls.map(call => 
            call.name === event.data.tool_name 
              ? { ...call, result: event.data.result }
              : call
          );
          break;
          
        case 'token':
          newState.currentResponse += event.data.token;
          break;
          
        case 'message_complete':
          // Add assistant message to history
          if (newState.currentResponse && currentMessageIdRef.current) {
            newState.messages = [...newState.messages, {
              id: currentMessageIdRef.current,
              type: 'assistant',
              content: newState.currentResponse,
              timestamp: event.data.timestamp,
              metadata: {
                toolCalls: newState.toolCalls,
                thinkingSteps: newState.thinkingStep ? [newState.thinkingStep] : [],
              }
            }];
          }
          
          newState.isProcessing = false;
          newState.currentResponse = '';
          newState.thinkingStep = null;
          newState.toolCalls = [];
          currentMessageIdRef.current = null;
          break;
          
        case 'error':
          newState.error = event.data.error;
          newState.isProcessing = false;
          newState.currentResponse = '';
          newState.thinkingStep = null;
          
          toast({
            title: '❌ Chat Error',
            description: event.data.error,
            variant: 'destructive',
          });
          break;
          
        case 'heartbeat':
          // Keep connection alive - no state change needed
          break;
          
        default:
          console.log('Unknown SSE event:', event.event, event.data);
      }
      
      return newState;
    });
  }, [toast]);
  
  // Send message function
  const sendMessage = useCallback(async (
    message: string, 
    context?: Record<string, any>
  ) => {
    if (!chatflowId || state.isProcessing) {
      return;
    }
    
    try {
      const response = await fetch(`/api/agent-builder/chatflows/${chatflowId}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: state.sessionId,
          context,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body reader available');
      }
      
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE events
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        let currentEvent: Partial<StreamEvent> = {};
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent.event = line.slice(7);
          } else if (line.startsWith('data: ')) {
            try {
              currentEvent.data = JSON.parse(line.slice(6));
            } catch (e) {
              console.error('Failed to parse SSE data:', line);
            }
          } else if (line.startsWith('id: ')) {
            currentEvent.id = line.slice(4);
          } else if (line === '') {
            // Empty line indicates end of event
            if (currentEvent.event && currentEvent.data) {
              handleStreamEvent(currentEvent as StreamEvent);
            }
            currentEvent = {};
          }
        }
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
        isProcessing: false,
      }));
      
      toast({
        title: '❌ Send Error',
        description: error instanceof Error ? error.message : 'Failed to send message',
        variant: 'destructive',
      });
    }
  }, [chatflowId, state.sessionId, state.isProcessing, handleStreamEvent, toast]);
  
  // Clear history function
  const clearHistory = useCallback(async () => {
    if (!chatflowId || !state.sessionId) {
      return;
    }
    
    try {
      const response = await fetch(
        `/api/agent-builder/chatflows/${chatflowId}/chat/history/${state.sessionId}`,
        { method: 'DELETE' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to clear history');
      }
      
      setState(prev => ({
        ...prev,
        messages: [],
        currentResponse: '',
        thinkingStep: null,
        toolCalls: [],
      }));
      
      toast({
        title: '🗑️ History Cleared',
        description: 'Chat history has been cleared.',
      });
      
    } catch (error) {
      console.error('Error clearing history:', error);
      toast({
        title: '❌ Clear Error',
        description: 'Failed to clear chat history',
        variant: 'destructive',
      });
    }
  }, [chatflowId, state.sessionId, toast]);
  
  // Reconnect function
  const reconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    setState(prev => ({
      ...prev,
      isConnecting: true,
      error: null,
    }));
    
    // Note: For SSE, we don't maintain persistent connections
    // Each message creates its own streaming request
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
      }));
    }, 100);
  }, []);
  
  // Disconnect function
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, []);
  
  // Initialize connection
  useEffect(() => {
    if (chatflowId) {
      reconnect();
    }
    
    return () => {
      disconnect();
    };
  }, [chatflowId, reconnect, disconnect]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);
  
  const isReady = state.isConnected && !state.isConnecting && !state.error;
  
  return {
    state,
    sendMessage,
    clearHistory,
    reconnect,
    disconnect,
    isReady,
  };
}