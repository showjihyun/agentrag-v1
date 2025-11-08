'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, GitBranch, MoreVertical, Edit, Play, Copy, Trash, Eye, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useRouter } from 'next/navigation';

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
  execution_count?: number;
  last_execution_status?: 'success' | 'failed' | 'running';
}

export default function WorkflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [workflowToDelete, setWorkflowToDelete] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const response = await agentBuilderAPI.getWorkflows();
      setWorkflows(response.workflows || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflows',
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!workflowToDelete) return;

    try {
      await agentBuilderAPI.deleteWorkflow(workflowToDelete);
      toast({
        title: 'Success',
        description: 'Workflow deleted successfully',
        variant: 'success',
      });
      loadWorkflows();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete workflow',
        variant: 'error',
      });
    } finally {
      setDeleteDialogOpen(false);
      setWorkflowToDelete(null);
    }
  };

  const handleExecute = async (workflowId: string) => {
    try {
      toast({
        title: 'Executing',
        description: 'Workflow execution started...',
      });
      
      await agentBuilderAPI.executeWorkflow(workflowId, {});
      
      toast({
        title: 'Success',
        description: 'Workflow executed successfully',
        variant: 'success',
      });
      
      loadWorkflows();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to execute workflow',
        variant: 'error',
      });
    }
  };

  const handleDuplicate = async (workflow: Workflow) => {
    try {
      await agentBuilderAPI.createWorkflow({
        name: `${workflow.name} (Copy)`,
        description: workflow.description,
        graph_definition: workflow.graph_definition,
      });
      
      toast({
        title: 'Success',
        description: 'Workflow duplicated successfully',
        variant: 'success',
      });
      
      loadWorkflows();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to duplicate workflow',
        variant: 'error',
      });
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  const filteredWorkflows = workflows.filter((w) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <GitBranch className="h-8 w-8" />
            Workflows
          </h1>
          <p className="text-muted-foreground mt-1">
            Create and manage multi-step agent workflows with visual builder
          </p>
        </div>
        <Button onClick={() => router.push('/agent-builder/workflows/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Workflow
        </Button>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search workflows by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <GitBranch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {searchQuery ? 'No workflows found' : 'No workflows yet'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'Create your first workflow to orchestrate multiple agents'}
            </p>
            {!searchQuery && (
              <Button onClick={() => router.push('/agent-builder/workflows/new')}>
                <Plus className="mr-2 h-4 w-4" />
                Create Workflow
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows.map((workflow) => (
            <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="flex items-center gap-2">
                      <GitBranch className="h-5 w-5" />
                      {workflow.name}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {workflow.description || 'No description'}
                    </CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => router.push(`/agent-builder/workflows/${workflow.id}`)}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => router.push(`/agent-builder/workflows/${workflow.id}/edit`)}
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleExecute(workflow.id)}>
                        <Play className="mr-2 h-4 w-4" />
                        Execute
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleDuplicate(workflow)}>
                        <Copy className="mr-2 h-4 w-4" />
                        Duplicate
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => {
                          setWorkflowToDelete(workflow.id);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <Trash className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline">
                    {workflow.graph_definition?.nodes?.length || 0} nodes
                  </Badge>
                  <Badge variant="outline">
                    {workflow.graph_definition?.edges?.length || 0} edges
                  </Badge>
                  {workflow.is_active && (
                    <Badge variant="default">Active</Badge>
                  )}
                  {workflow.last_execution_status && (
                    <div className="flex items-center gap-1">
                      {getStatusIcon(workflow.last_execution_status)}
                      <span className="text-xs text-muted-foreground">
                        Last run
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="text-xs text-muted-foreground">
                {workflow.execution_count ? (
                  <span>{workflow.execution_count} executions</span>
                ) : (
                  <span>Never executed</span>
                )}
                {workflow.updated_at && (
                  <span className="ml-auto">
                    Updated {new Date(workflow.updated_at).toLocaleDateString()}
                  </span>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workflow</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this workflow? This action cannot be undone.
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
