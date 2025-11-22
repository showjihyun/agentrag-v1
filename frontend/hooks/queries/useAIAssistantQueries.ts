import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryClient';
import { toast } from 'sonner';
import {
  BreakpointSuggestion,
  OptimizationSuggestion,
  ErrorDiagnosis,
} from '@/types/workflow';

/**
 * Fetch breakpoint suggestions
 */
export function useBreakpointSuggestions(workflowId: string, enabled = false) {
  return useQuery({
    queryKey: queryKeys.aiAssistant.breakpoints(workflowId),
    queryFn: async () => {
      const response = await fetch(
        `/api/agent-builder/ai-assistant/${workflowId}/suggest-breakpoints`
      );
      if (!response.ok) throw new Error('Failed to fetch breakpoint suggestions');
      return response.json() as Promise<BreakpointSuggestion[]>;
    },
    enabled: !!workflowId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch optimization suggestions
 */
export function useOptimizationSuggestions(workflowId: string, enabled = false) {
  return useQuery({
    queryKey: queryKeys.aiAssistant.optimizations(workflowId),
    queryFn: async () => {
      const response = await fetch(
        `/api/agent-builder/ai-assistant/${workflowId}/suggest-optimizations`
      );
      if (!response.ok) throw new Error('Failed to fetch optimization suggestions');
      return response.json() as Promise<OptimizationSuggestion[]>;
    },
    enabled: !!workflowId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Diagnose error mutation
 */
export function useDiagnoseError(workflowId: string) {
  return useMutation({
    mutationFn: async (errorData: { error: string; context: any }) => {
      const response = await fetch(
        `/api/agent-builder/ai-assistant/${workflowId}/diagnose-error`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(errorData),
        }
      );
      if (!response.ok) throw new Error('Failed to diagnose error');
      return response.json() as Promise<ErrorDiagnosis>;
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to diagnose error');
    },
  });
}

/**
 * Send debug query mutation
 */
export function useDebugQuery(workflowId: string) {
  return useMutation({
    mutationFn: async (query: string) => {
      const response = await fetch('/api/agent-builder/ai-assistant/debug-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflowId,
          query,
          workflow_context: {},
        }),
      });
      if (!response.ok) throw new Error('Failed to send debug query');
      return response.json() as Promise<{ answer: string; suggestions?: string[] }>;
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to send query');
    },
  });
}
