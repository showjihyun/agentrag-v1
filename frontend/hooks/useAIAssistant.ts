import { useState, useCallback } from 'react';
import { useAPI } from './useAPI';
import {
  ErrorDiagnosis,
  BreakpointSuggestion,
  OptimizationSuggestion,
  ChatMessage,
} from '@/types/workflow';

interface DebugQueryRequest {
  workflow_id: string;
  query: string;
  workflow_context: Record<string, any>;
}

interface DebugQueryResponse {
  answer: string;
  suggestions?: string[];
}

/**
 * Unified hook for AI Assistant functionality
 */
export function useAIAssistant(workflowId: string) {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState('');

  // API hooks for different AI features
  const breakpoints = useAPI<BreakpointSuggestion[]>(
    `/api/agent-builder/ai-assistant/${workflowId}/suggest-breakpoints`
  );

  const optimizations = useAPI<OptimizationSuggestion[]>(
    `/api/agent-builder/ai-assistant/${workflowId}/suggest-optimizations`
  );

  const errorDiagnosis = useAPI<ErrorDiagnosis>(
    `/api/agent-builder/ai-assistant/${workflowId}/diagnose-error`,
    { method: 'POST' }
  );

  const debugQuery = useAPI<DebugQueryResponse>(
    '/api/agent-builder/ai-assistant/debug-query',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  );

  // Send chat query
  const sendQuery = useCallback(
    async (userQuery: string) => {
      if (!userQuery.trim()) return;

      // Add user message to history
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: userQuery, timestamp: new Date() },
      ]);

      try {
        const response = await fetch('/api/agent-builder/ai-assistant/debug-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workflow_id: workflowId,
            query: userQuery,
            workflow_context: {},
          } as DebugQueryRequest),
        });

        const data: DebugQueryResponse = await response.json();

        // Add assistant response to history
        setChatHistory((prev) => [
          ...prev,
          { role: 'assistant', content: data.answer, timestamp: new Date() },
        ]);

        return data;
      } catch (error) {
        const errorMessage = 'Sorry, I encountered an error. Please try again.';
        setChatHistory((prev) => [
          ...prev,
          { role: 'assistant', content: errorMessage, timestamp: new Date() },
        ]);
        throw error;
      }
    },
    [workflowId]
  );

  // Clear chat history
  const clearChat = useCallback(() => {
    setChatHistory([]);
  }, []);

  return {
    // Chat
    chatHistory,
    query,
    setQuery,
    sendQuery,
    clearChat,

    // Breakpoints
    breakpointSuggestions: breakpoints.data,
    isLoadingBreakpoints: breakpoints.isLoading,
    fetchBreakpoints: breakpoints.execute,

    // Optimizations
    optimizationSuggestions: optimizations.data,
    isLoadingOptimizations: optimizations.isLoading,
    fetchOptimizations: optimizations.execute,

    // Error Diagnosis
    errorDiagnosisResult: errorDiagnosis.data,
    isLoadingDiagnosis: errorDiagnosis.isLoading,
    diagnoseError: errorDiagnosis.execute,

    // Overall loading state
    isLoading:
      breakpoints.isLoading ||
      optimizations.isLoading ||
      errorDiagnosis.isLoading ||
      debugQuery.isLoading,
  };
}
