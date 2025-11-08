'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Edit, Play, Copy, Trash, GitBranch } from 'lucide-react';
import type { Node, Edge } from 'reactflow';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

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

export default function WorkflowViewPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      setWorkflow(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    setExecuting(true);
    try {
      toast({
        title: 'Executing',
        description: 'Workflow execution started...',
      });

      await agentBuilderAPI.executeWorkflow(workflowId, {});

      toast({
        title: 'Success',
        description: 'Workflow executed successfully',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to execute workflow',
        variant: 'destructive',
      });
    } finally {
      setExecuting(false);
    }
  };

  const handleDuplicate = async () => {
    if (!workflow) return;

    try {
      await agentBuilderAPI.createWorkflow({
        name: `${workflow.name} (Copy)`,
        description: workflow.description,
        graph_definition: workflow.graph_definition,
      });

      toast({
        title: 'Success',
        description: 'Workflow duplicated successfully',
      });

      router.push('/agent-builder/workflows');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to duplicate workflow',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    try {
      await agentBuilderAPI.deleteWorkflow(workflowId);
      toast({
        title: 'Success',
        description: 'Workflow deleted successfully',
      });
      router.push('/agent-builder/workflows');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete workflow',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-[600px] w-full" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Workflow not found</p>
            <Button
              variant="link"
              onClick={() => router.push('/agent-builder/workflows')}
            >
              Back to Workflows
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const nodes: Node[] = workflow.graph_definition.nodes.map(node => ({
    id: node.id,
    type: node.type || 'block',
    position: node.position,
    data: node.data,
  }));

  const edges: Edge[] = workflow.graph_definition.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    targetHandle: edge.targetHandle,
  }));

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="container mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/agent-builder/workflows')}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <div className="flex items-center gap-2">
                  <GitBranch className="h-6 w-6" />
                  <h1 className="text-2xl font-bold">{workflow.name}</h1>
                  {workflow.is_active && (
                    <Badge variant="default">Active</Badge>
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
                onClick={handleDuplicate}
              >
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </Button>
              <Button
                variant="outline"
                onClick={handleExecute}
                disabled={executing}
              >
                <Play className="mr-2 h-4 w-4" />
                {executing ? 'Executing...' : 'Execute'}
              </Button>
              <Button
                onClick={() => router.push(`/agent-builder/workflows/${workflowId}/edit`)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <Button
                variant="destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash className="mr-2 h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{nodes.length} nodes</span>
            <span>•</span>
            <span>{edges.length} connections</span>
            <span>•</span>
            <span>Created {new Date(workflow.created_at).toLocaleDateString()}</span>
            {workflow.updated_at && (
              <>
                <span>•</span>
                <span>Updated {new Date(workflow.updated_at).toLocaleDateString()}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Workflow Canvas (Read-only) */}
      <div className="flex-1 bg-muted/20">
        <WorkflowEditor
          workflowId={workflowId}
          initialNodes={nodes}
          initialEdges={edges}
          readOnly={true}
        />
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workflow</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{workflow.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
