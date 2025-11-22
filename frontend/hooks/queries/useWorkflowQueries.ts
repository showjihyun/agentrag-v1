import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryClient';
import { toast } from 'sonner';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: any[];
  edges: any[];
  created_at: string;
  updated_at: string;
}

interface WorkflowStatus {
  workflow_id: string;
  status: string;
  progress_percent: number;
  current_node_id?: string;
}

/**
 * Fetch all workflows
 */
export function useWorkflows(filters?: string) {
  return useQuery({
    queryKey: queryKeys.workflows.list(filters || ''),
    queryFn: async () => {
      const response = await fetch(`/api/agent-builder/workflows${filters ? `?${filters}` : ''}`);
      if (!response.ok) throw new Error('Failed to fetch workflows');
      return response.json() as Promise<Workflow[]>;
    },
  });
}

/**
 * Fetch single workflow
 */
export function useWorkflow(id: string) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: async () => {
      const response = await fetch(`/api/agent-builder/workflows/${id}`);
      if (!response.ok) throw new Error('Failed to fetch workflow');
      return response.json() as Promise<Workflow>;
    },
    enabled: !!id,
  });
}

/**
 * Fetch workflow status
 */
export function useWorkflowStatus(id: string, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.workflows.status(id),
    queryFn: async () => {
      const response = await fetch(`/api/agent-builder/workflows/${id}/status`);
      if (!response.ok) throw new Error('Failed to fetch workflow status');
      return response.json() as Promise<WorkflowStatus>;
    },
    enabled: !!id,
    refetchInterval: options?.refetchInterval,
  });
}

/**
 * Create workflow mutation
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      const response = await fetch('/api/agent-builder/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create workflow');
      return response.json() as Promise<Workflow>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      toast.success('Workflow created successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create workflow');
    },
  });
}

/**
 * Update workflow mutation
 */
export function useUpdateWorkflow(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      const response = await fetch(`/api/agent-builder/workflows/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update workflow');
      return response.json() as Promise<Workflow>;
    },
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.workflows.detail(id) });

      // Snapshot previous value
      const previousWorkflow = queryClient.getQueryData(queryKeys.workflows.detail(id));

      // Optimistically update
      queryClient.setQueryData(queryKeys.workflows.detail(id), (old: any) => ({
        ...old,
        ...newData,
      }));

      return { previousWorkflow };
    },
    onError: (error: Error, _newData, context) => {
      // Rollback on error
      if (context?.previousWorkflow) {
        queryClient.setQueryData(queryKeys.workflows.detail(id), context.previousWorkflow);
      }
      toast.error(error.message || 'Failed to update workflow');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      toast.success('Workflow updated successfully');
    },
  });
}

/**
 * Delete workflow mutation
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`/api/agent-builder/workflows/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete workflow');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      toast.success('Workflow deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete workflow');
    },
  });
}

/**
 * Execute workflow mutation
 */
export function useExecuteWorkflow(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input?: any) => {
      const response = await fetch(`/api/agent-builder/workflows/${id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input }),
      });
      if (!response.ok) throw new Error('Failed to execute workflow');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.status(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.executions(id) });
      toast.success('Workflow execution started');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to execute workflow');
    },
  });
}
