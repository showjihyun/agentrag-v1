import { useState, useCallback } from 'react';
import { ChatMessage } from '@/types/workflow';
import {
  useBreakpointSuggestions,
  useOptimizationSuggestions,
  useDiagnoseError,
  useDebugQuery,
} from './queries/useAIAssistantQueries';

/**
 * Enhanced AI Assistant hook using React Query
 * Replaces the old useAIAssistant hook with better caching and state management
 */
export function useAIAssistantWithQuery(workflowId: string) {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState('');

  // Queries with manual trigger
  const breakpoints = useBreakpointSuggestions(workflowId, false);
  const optimizations = useOptimizationSuggestions(workflowId, false);
  
  // Mutations
  const diagnoseError = useDiagnoseError(workflowId);
  const debugQuery = useDebugQuery(workflowId);

  // Send chat query
  const sendQuery = useCallback(
    async (userQuery: string) => {
      if (!userQuery.trim()) return;

      // Add user message
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: userQuery, timestamp: new Date() },
      ]);

      try {
        const result = await debugQuery.mutateAsync(userQuery);
        
        // Add assistant response
        setChatHistory((prev) => [
          ...prev,
          { role: 'assistant', content: result.answer, timestamp: new Date() },
        ]);

        return result;
      } catch (error) {
        const errorMessage = 'Sorry, I encountered an error. Please try again.';
        setChatHistory((prev) => [
          ...prev,
          { role: 'assistant', content: errorMessage, timestamp: new Date() },
        ]);
        throw error;
      }
    },
    [debugQuery]
  );

  // Clear chat history
  const clearChat = useCallback(() => {
    setChatHistory([]);
  }, []);

  // Fetch breakpoints
  const fetchBreakpoints = useCallback(() => {
    return breakpoints.refetch();
  }, [breakpoints]);

  // Fetch optimizations
  const fetchOptimizations = useCallback(() => {
    return optimizations.refetch();
  }, [optimizations]);

  return {
    // Chat
    chatHistory,
    query,
    setQuery,
    sendQuery,
    clearChat,

    // Breakpoints
    breakpointSuggestions: breakpoints.data,
    isLoadingBreakpoints: breakpoints.isLoading || breakpoints.isFetching,
    fetchBreakpoints,

    // Optimizations
    optimizationSuggestions: optimizations.data,
    isLoadingOptimizations: optimizations.isLoading || optimizations.isFetching,
    fetchOptimizations,

    // Error Diagnosis
    errorDiagnosisResult: diagnoseError.data,
    isLoadingDiagnosis: diagnoseError.isPending,
    diagnoseError: diagnoseError.mutate,

    // Overall loading state
    isLoading:
      breakpoints.isLoading ||
      optimizations.isLoading ||
      diagnoseError.isPending ||
      debugQuery.isPending,
  };
}
