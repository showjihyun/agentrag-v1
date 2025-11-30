/**
 * useChatHistory Hook
 * 
 * Provides chat history management:
 * - Session management
 * - Message handling
 * - Search functionality
 */

import { useState, useEffect, useCallback } from 'react';
import { chatHistoryAPI, ChatSession, ChatMessage, CreateSessionRequest } from '@/lib/api/chat-history';

interface UseChatHistoryReturn {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  createSession: (request?: CreateSessionRequest) => Promise<string>;
  selectSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  addMessage: (role: 'user' | 'assistant', content: string) => Promise<ChatMessage | null>;
  clearSession: () => Promise<void>;
  updateTitle: (title: string) => Promise<void>;
  searchMessages: (query: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
}

export function useChatHistory(): UseChatHistoryReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshSessions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await chatHistoryAPI.listSessions();
      setSessions(response.sessions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(async (request: CreateSessionRequest = {}) => {
    try {
      const response = await chatHistoryAPI.createSession(request);
      await refreshSessions();
      return response.session_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      throw err;
    }
  }, [refreshSessions]);

  const selectSession = useCallback(async (sessionId: string) => {
    try {
      setLoading(true);
      const [session, messagesResponse] = await Promise.all([
        chatHistoryAPI.getSession(sessionId),
        chatHistoryAPI.getMessages(sessionId),
      ]);
      setCurrentSession(session);
      setMessages(messagesResponse.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session');
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await chatHistoryAPI.deleteSession(sessionId);
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      await refreshSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session');
    }
  }, [currentSession, refreshSessions]);

  const addMessage = useCallback(async (role: 'user' | 'assistant', content: string) => {
    if (!currentSession) return null;
    try {
      const message = await chatHistoryAPI.addMessage(currentSession.id, { role, content });
      setMessages(prev => [...prev, message]);
      return message;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add message');
      return null;
    }
  }, [currentSession]);

  const clearSession = useCallback(async () => {
    if (!currentSession) return;
    try {
      await chatHistoryAPI.clearSession(currentSession.id);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear session');
    }
  }, [currentSession]);

  const updateTitle = useCallback(async (title: string) => {
    if (!currentSession) return;
    try {
      await chatHistoryAPI.updateSessionTitle(currentSession.id, title);
      setCurrentSession(prev => prev ? { ...prev, title } : null);
      await refreshSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update title');
    }
  }, [currentSession, refreshSessions]);

  const searchMessages = useCallback(async (query: string) => {
    try {
      setLoading(true);
      await chatHistoryAPI.searchMessages(query);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  return {
    sessions,
    currentSession,
    messages,
    loading,
    error,
    createSession,
    selectSession,
    deleteSession,
    addMessage,
    clearSession,
    updateTitle,
    searchMessages,
    refreshSessions,
  };
}
