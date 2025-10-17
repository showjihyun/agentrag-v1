/**
 * React Query hooks for session management
 * 
 * Provides automatic caching, background refetching, and optimistic updates
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { MessageResponse } from '@/lib/types';
import { useAppStore } from '@/lib/stores/app-store';

// Query keys
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters: string) => [...sessionKeys.lists(), { filters }] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
  messages: (id: string) => [...sessionKeys.detail(id), 'messages'] as const,
};

/**
 * Fetch session messages with automatic caching
 */
export function useSessionMessages(sessionId: string | null) {
  return useQuery({
    queryKey: sessionKeys.messages(sessionId || ''),
    queryFn: async () => {
      if (!sessionId) return { messages: [] };
      return await apiClient.getSessionMessages(sessionId);
    },
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true,
  });
}

/**
 * Fetch user sessions list
 */
export function useUserSessions() {
  return useQuery({
    queryKey: sessionKeys.lists(),
    queryFn: async () => {
      return await apiClient.getUserSessions();
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
  });
}

/**
 * Send message with optimistic updates
 */
export function useSendMessage() {
  const queryClient = useQueryClient();
  const addMessage = useAppStore((state) => state.addMessage);
  
  return useMutation({
    mutationFn: async (data: { 
      query: string; 
      sessionId: string;
      mode?: 'fast' | 'balanced' | 'deep' | 'auto';
    }) => {
      return await apiClient.sendQuery(data.query, data.sessionId, data.mode);
    },
    
    // Optimistic update
    onMutate: async (newMessage) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ 
        queryKey: sessionKeys.messages(newMessage.sessionId) 
      });
      
      // Snapshot previous value
      const previousMessages = queryClient.getQueryData(
        sessionKeys.messages(newMessage.sessionId)
      );
      
      // Optimistically update
      const optimisticMessage: MessageResponse = {
        id: 'temp-' + Date.now(),
        content: newMessage.query,
        role: 'user',
        timestamp: new Date().toISOString(),
        session_id: newMessage.sessionId,
      };
      
      queryClient.setQueryData(
        sessionKeys.messages(newMessage.sessionId),
        (old: any) => ({
          ...old,
          messages: [...(old?.messages || []), optimisticMessage],
        })
      );
      
      // Also update Zustand store
      addMessage(newMessage.sessionId, optimisticMessage);
      
      return { previousMessages };
    },
    
    // Rollback on error
    onError: (err, newMessage, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(
          sessionKeys.messages(newMessage.sessionId),
          context.previousMessages
        );
      }
      console.error('Failed to send message:', err);
    },
    
    // Refetch after mutation
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: sessionKeys.messages(variables.sessionId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: sessionKeys.lists() 
      });
    },
    
    // Success callback
    onSuccess: (data, variables) => {
      // Update Zustand store with real message
      if (data) {
        addMessage(variables.sessionId, data as any);
      }
    },
  });
}

/**
 * Delete session
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return await apiClient.deleteSession(sessionId);
    },
    onSuccess: () => {
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}

/**
 * Create new session
 */
export function useCreateSession() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (title?: string) => {
      return await apiClient.createSession(title);
    },
    onSuccess: () => {
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}
