'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { logger } from '@/lib/logger';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Save, Play, Eye } from 'lucide-react';
import type { Node, Edge } from 'reactflow';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export default function WorkflowEditPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      logger.log('📊 Workflow loaded for editing:', {
        id: data.id,
        name: data.name,
        nodesCount: data.graph_definition?.nodes?.length || 0,
        edgesCount: data.graph_definition?.edges?.length || 0,
      });
      setWorkflow(data);

      // Transform nodes
      const transformedNodes: Node[] = data.graph_definition.nodes.map((node: any) => {
        let nodeType = node.node_type || node.type;
        
        if (nodeType === 'control') {
          nodeType = node.configuration?.type || node.configuration?.nodeType || node.data?.type || 'start';
        }
        
        return {
          id: node.id,
          type: nodeType,
          position: node.position || { x: node.position_x || 0, y: node.position_y || 0 },
          data: node.configuration || node.data || {},
        };
      });

      // Transform edges
      const transformedEdges: Edge[] = data.graph_definition.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source_node_id || edge.source,
        target: edge.target_node_id || edge.target,
        sourceHandle: edge.source_handle || edge.sourceHandle,
        targetHandle: edge.target_handle || edge.targetHandle,
      }));

      setNodes(transformedNodes);
      setEdges(transformedEdges);
    } catch (error: any) {
      console.error('❌ Failed to load workflow:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNodesChange = useCallback((updatedNodes: Node[]) => {
    setNodes(updatedNodes);
    setHasChanges(true);
  }, []);

  const handleEdgesChange = useCallback((updatedEdges: Edge[]) => {
    setEdges(updatedEdges);
    setHasChanges(true);
  }, []);

  const handleSave = async () => {
    if (!workflow) return;

    try {
      setSaving(true);

      // Transform nodes back to API format
      const apiNodes = nodes.map((node) => ({
        id: node.id,
        node_type: node.type,
        position_x: node.position.x,
        position_y: node.position.y,
        configuration: node.data,
      }));

      // Transform edges back to API format
      const apiEdges = edges.map((edge) => ({
        id: edge.id,
        source_node_id: edge.source,
        target_node_id: edge.target,
        source_handle: edge.sourceHandle,
        target_handle: edge.targetHandle,
      }));

      await agentBuilderAPI.updateWorkflow(workflowId, {
        name: workflow.name,
        description: workflow.description,
        graph_definition: {
          nodes: apiNodes,
          edges: apiEdges,
        },
      });

      setHasChanges(false);
      toast({
        title: '✅ Saved',
        description: 'Workflow saved successfully',
      });
    } catch (error: any) {
      toast({
        title: '❌ Error',
        description: error.message || 'Failed to save workflow',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleExecute = () => {
    // Save first, then navigate to view page with execution
    handleSave().then(() => {
      router.push(`/agent-builder/workflows/${workflowId}?autoExecute=true`);
    });
  };

  if (loading) {
    return (
      <div className="h-screen flex flex-col">
        <div className="border-b bg-background p-4">
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1">
          <Skeleton className="h-full w-full" />
        </div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Workflow not found</p>
          <Button onClick={() => router.push('/agent-builder/workflows')}>
            Back to Workflows
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  if (hasChanges) {
                    const confirmed = window.confirm(
                      'You have unsaved changes. Are you sure you want to leave?'
                    );
                    if (!confirmed) return;
                  }
                  router.push(`/agent-builder/workflows/${workflowId}`);
                }}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold">{workflow.name}</h1>
                  {hasChanges && (
                    <Badge variant="secondary">Unsaved Changes</Badge>
                  )}
                </div>
                {workflow.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {workflow.description}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => router.push(`/agent-builder/workflows/${workflowId}`)}
              >
                <Eye className="mr-2 h-4 w-4" />
                View
              </Button>
              <Button
                variant="outline"
                onClick={handleExecute}
                disabled={saving}
              >
                <Play className="mr-2 h-4 w-4" />
                Save & Execute
              </Button>
              <Button onClick={handleSave} disabled={saving || !hasChanges}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
            <span>{nodes.length} nodes</span>
            <span>•</span>
            <span>{edges.length} connections</span>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <WorkflowEditor
          workflowId={workflowId}
          initialNodes={nodes}
          initialEdges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          readOnly={false}
        />
      </div>
    </div>
  );
}
