/**
 * React Query Custom Hooks
 * 
 * Type-safe hooks for data fetching with React Query
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { queryKeys } from './config';
import { RAGApiClient } from '@/lib/api-client';
import { MessageResponse, SessionResponse, DocumentResponse } from '@/lib/types';

const api = new RAGApiClient();

// ============================================================================
// Chat Queries
// ============================================================================

/**
 * Fetch chat sessions
 */
export function useSessions(options?: Omit<UseQueryOptions<SessionResponse[]>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.chat.sessions(),
    queryFn: () => api.getSessions(),
    ...options,
  });
}

/**
 * Fetch messages for a session
 */
export function useMessages(
  sessionId: string,
  options?: Omit<UseQueryOptions<MessageResponse[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.chat.messages(sessionId),
    queryFn: () => api.getMessages(sessionId),
    enabled: !!sessionId,
    ...options,
  });
}

/**
 * Send message mutation
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      api.sendMessage(sessionId, content),
    
    onMutate: async ({ sessionId, content }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.chat.messages(sessionId) });

      // Snapshot previous value
      const previousMessages = queryClient.getQueryData<MessageResponse[]>(
        queryKeys.chat.messages(sessionId)
      );

      // Optimistically update
      queryClient.setQueryData<MessageResponse[]>(
        queryKeys.chat.messages(sessionId),
        (old = []) => [
          ...old,
          {
            id: `temp-${Date.now()}`,
            role: 'user',
            content,
            created_at: new Date().toISOString(),
          } as MessageResponse,
        ]
      );

      return { previousMessages };
    },

    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          queryKeys.chat.messages(variables.sessionId),
          context.previousMessages
        );
      }
    },

    onSettled: (data, error, variables) => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.messages(variables.sessionId) });
    },
  });
}

// ============================================================================
// Document Queries
// ============================================================================

/**
 * Fetch documents
 */
export function useDocuments(options?: Omit<UseQueryOptions<DocumentResponse[]>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: () => api.getDocuments(),
    ...options,
  });
}

/**
 * Upload document mutation
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
  });
}

/**
 * Delete document mutation
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => api.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
  });
}

// ============================================================================
// User Queries
// ============================================================================

/**
 * Fetch user profile
 */
export function useUserProfile(options?: Omit<UseQueryOptions<any>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.user.profile(),
    queryFn: () => api.getCurrentUser(),
    ...options,
  });
}
