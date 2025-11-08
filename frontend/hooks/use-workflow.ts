'use client';

import { useState, useEffect, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useToast } from '@/hooks/use-toast';

export interface WorkflowData {
  id?: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: Node[];
    edges: Edge[];
  };
  is_active: boolean;
}

export function useWorkflow(workflowId?: string) {
  const { toast } = useToast();
  const [workflow, setWorkflow] = useState<WorkflowData | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Load workflow
  const loadWorkflow = useCallback(async () => {
    if (!workflowId) return;

    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      setWorkflow(data);
      setHasUnsavedChanges(false);
      setLastSaved(new Date(data.updated_at || data.created_at));
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [workflowId, toast]);

  // Save workflow
  const saveWorkflow = useCallback(
    async (nodes: Node[], edges: Edge[], showToast = true) => {
      if (!workflow) return;

      try {
        setSaving(true);

        const updatedWorkflow = {
          ...workflow,
          graph_definition: {
            nodes,
            edges,
          },
        };

        if (workflow.id) {
          // Update existing workflow
          await agentBuilderAPI.updateWorkflow(workflow.id, updatedWorkflow);
        } else {
          // Create new workflow
          const created = await agentBuilderAPI.createWorkflow(updatedWorkflow);
          setWorkflow(created);
        }

        setHasUnsavedChanges(false);
        setLastSaved(new Date());

        if (showToast) {
          toast({
            title: 'Success',
            description: 'Workflow saved successfully',
            variant: 'success',
          });
        }
      } catch (error: any) {
        toast({
          title: 'Error',
          description: error.message || 'Failed to save workflow',
          variant: 'error',
        });
        throw error;
      } finally {
        setSaving(false);
      }
    },
    [workflow, toast]
  );

  // Update workflow metadata
  const updateMetadata = useCallback(
    (updates: Partial<WorkflowData>) => {
      if (!workflow) return;
      setWorkflow({ ...workflow, ...updates });
      setHasUnsavedChanges(true);
    },
    [workflow]
  );

  // Mark as changed
  const markAsChanged = useCallback(() => {
    setHasUnsavedChanges(true);
  }, []);

  // Auto-save effect
  useEffect(() => {
    if (!autoSaveEnabled || !hasUnsavedChanges || !workflow) return;

    const timer = setTimeout(() => {
      if (workflow.graph_definition) {
        saveWorkflow(
          workflow.graph_definition.nodes,
          workflow.graph_definition.edges,
          false
        );
      }
    }, 3000); // Auto-save after 3 seconds of inactivity

    return () => clearTimeout(timer);
  }, [autoSaveEnabled, hasUnsavedChanges, workflow, saveWorkflow]);

  // Load on mount
  useEffect(() => {
    if (workflowId) {
      loadWorkflow();
    }
  }, [workflowId, loadWorkflow]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  return {
    workflow,
    loading,
    saving,
    hasUnsavedChanges,
    lastSaved,
    autoSaveEnabled,
    setAutoSaveEnabled,
    loadWorkflow,
    saveWorkflow,
    updateMetadata,
    markAsChanged,
  };
}
