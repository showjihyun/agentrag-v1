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
import { ArrowLeft, Edit, Play, Copy, Trash, GitBranch, Clock, CheckCircle, XCircle, Eye } from 'lucide-react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface ExecutionRecord {
  id: string;
  status: 'success' | 'failed' | 'running';
  duration: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  input_data?: any;
  output_data?: any;
}

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
  const [activeTab, setActiveTab] = useState('canvas');
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRecord | null>(null);
  const [executionDetailsOpen, setExecutionDetailsOpen] = useState(false);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  useEffect(() => {
    if (activeTab === 'executions') {
      loadExecutions();
    }
  }, [activeTab, workflowId]);

  const loadExecutions = async () => {
    try {
      setLoadingExecutions(true);
      
      // Call API to get executions
      const data = await agentBuilderAPI.getWorkflowExecutions(workflowId, {
        limit: 50,
        offset: 0,
      });
      
      // Transform API response to match our interface
      const executionRecords: ExecutionRecord[] = (data.executions || []).map((exec: any) => ({
        id: exec.id,
        status: exec.status,
        duration: exec.duration || 0,
        started_at: exec.started_at,
        completed_at: exec.completed_at,
        error_message: exec.error_message,
        input_data: exec.input_data,
        output_data: exec.output_data,
      }));
      
      setExecutions(executionRecords);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load executions',
      });
      
      // Fallback to empty array on error
      setExecutions([]);
    } finally {
      setLoadingExecutions(false);
    }
  };

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      setWorkflow(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
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

      const result = await agentBuilderAPI.executeWorkflow(workflowId, {});
      
      // Check if execution failed immediately
      if (result.status === 'failed') {
        toast({
          title: 'Execution Failed',
          description: result.message || result.error_message || 'Workflow execution failed',
          variant: 'error',
        });
        setExecuting(false);
        setActiveTab('executions');
        loadExecutions();
        return;
      }
      
      const executionId = result.execution_id;

      // Switch to executions tab immediately
      setActiveTab('executions');

      // Poll for execution status
      let attempts = 0;
      const maxAttempts = 20; // 10 seconds max
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const execData = await agentBuilderAPI.getWorkflowExecutions(workflowId, {
            limit: 1,
            offset: 0,
          });
          
          const latestExec = execData.executions?.[0];
          
          if (latestExec && latestExec.id === executionId) {
            if (latestExec.status !== 'running') {
              // Execution completed
              clearInterval(pollInterval);
              loadExecutions();
              
              if (latestExec.status === 'completed' || latestExec.status === 'success') {
                toast({
                  title: 'Success',
                  description: result.message || 'Workflow executed successfully',
                  variant: 'success',
                });
              } else {
                toast({
                  title: 'Execution Failed',
                  description: latestExec.error_message || result.message || 'Workflow execution failed',
                  variant: 'error',
                });
              }
              setExecuting(false);
            }
          }
          
          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            loadExecutions();
            setExecuting(false);
          }
        } catch (error) {
          console.error('Error polling execution status:', error);
        }
      }, 500);

    } catch (error: any) {
      const errorMessage = error.message || error.detail || 'Failed to execute workflow';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'error',
      });
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

  const nodes: Node[] = workflow.graph_definition.nodes.map((node: any) => ({
    id: node.id,
    type: node.node_type === 'control' ? (node.configuration?.type || 'block') : node.node_type,
    position: node.position || { x: node.position_x || 0, y: node.position_y || 0 },
    data: node.configuration || node.data || {},
  }));

  const edges: Edge[] = workflow.graph_definition.edges.map((edge: any) => ({
    id: edge.id,
    source: edge.source_node_id || edge.source,
    target: edge.target_node_id || edge.target,
    sourceHandle: edge.source_handle || edge.sourceHandle,
    targetHandle: edge.target_handle || edge.targetHandle,
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

      {/* Tabs */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="border-b px-4">
            <TabsList>
              <TabsTrigger value="canvas">Canvas</TabsTrigger>
              <TabsTrigger value="executions">Executions</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="canvas" className="flex-1 m-0 bg-muted/20">
            <WorkflowEditor
              workflowId={workflowId}
              initialNodes={nodes}
              initialEdges={edges}
              readOnly={true}
            />
          </TabsContent>

          <TabsContent value="executions" className="flex-1 m-0 overflow-auto">
            <div className="container mx-auto p-6">
              {/* Running Executions Alert */}
              {executing && (
                <Card className="mb-4 border-blue-500 bg-blue-50">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-blue-500 animate-spin" />
                      <div className="flex-1">
                        <div className="font-medium text-blue-900">Workflow Executing</div>
                        <div className="text-sm text-blue-700">
                          Your workflow is currently running. Results will appear below when complete.
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              <Card>
                <CardHeader>
                  <CardTitle>Execution History</CardTitle>
                  <CardDescription>
                    View past workflow executions and their results
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingExecutions ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                      <p className="mt-4 text-muted-foreground">Loading executions...</p>
                    </div>
                  ) : executions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No executions yet</p>
                      <p className="text-sm mt-2">Run this workflow to see execution history</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Status</TableHead>
                          <TableHead>Execution ID</TableHead>
                          <TableHead>Duration</TableHead>
                          <TableHead>Started At</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {executions.map((exec) => (
                          <TableRow key={exec.id} className={exec.status === 'failed' ? 'bg-destructive/5' : ''}>
                            <TableCell>
                              <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                  {exec.status === 'success' || exec.status === 'completed' ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : null}
                                  {exec.status === 'failed' && (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                  {exec.status === 'running' && (
                                    <Clock className="h-4 w-4 text-blue-500 animate-spin" />
                                  )}
                                  <Badge
                                    variant={
                                      exec.status === 'success' || exec.status === 'completed'
                                        ? 'default'
                                        : exec.status === 'failed'
                                        ? 'destructive'
                                        : 'secondary'
                                    }
                                  >
                                    {exec.status}
                                  </Badge>
                                </div>
                                {exec.status === 'failed' && exec.error_message && (
                                  <div className="text-xs text-destructive truncate max-w-xs" title={exec.error_message}>
                                    {exec.error_message}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="font-mono text-sm">
                              {exec.id.substring(0, 8)}...
                            </TableCell>
                            <TableCell>{exec.duration.toFixed(2)}s</TableCell>
                            <TableCell>
                              {new Date(exec.started_at).toLocaleString()}
                            </TableCell>
                            <TableCell>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => {
                                  setSelectedExecution(exec);
                                  setExecutionDetailsOpen(true);
                                }}
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="flex-1 m-0 overflow-auto">
            <div className="container mx-auto p-6">
              <Card>
                <CardHeader>
                  <CardTitle>Workflow Settings</CardTitle>
                  <CardDescription>
                    Configure workflow behavior and notifications
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">Active Status</div>
                        <div className="text-sm text-muted-foreground">
                          Enable or disable this workflow
                        </div>
                      </div>
                      <Badge variant={workflow?.is_active ? 'default' : 'secondary'}>
                        {workflow?.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <div className="font-medium mb-2">Workflow Information</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Created:</span>
                          <span>{new Date(workflow?.created_at || '').toLocaleString()}</span>
                        </div>
                        {workflow?.updated_at && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Last Updated:</span>
                            <span>{new Date(workflow.updated_at).toLocaleString()}</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Nodes:</span>
                          <span>{nodes.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Connections:</span>
                          <span>{edges.length}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Delete Confirmation Dialog */}
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

      {/* Execution Details Dialog */}
      <AlertDialog open={executionDetailsOpen} onOpenChange={setExecutionDetailsOpen}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Execution Details</AlertDialogTitle>
            <AlertDialogDescription>
              Detailed information about this workflow execution
            </AlertDialogDescription>
          </AlertDialogHeader>
          {selectedExecution && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Execution ID</div>
                  <div className="font-mono text-sm mt-1">{selectedExecution.id}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Status</div>
                  <div className="mt-1">
                    <Badge
                      variant={
                        selectedExecution.status === 'success'
                          ? 'default'
                          : selectedExecution.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {selectedExecution.status}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Duration</div>
                  <div className="text-sm mt-1">{selectedExecution.duration.toFixed(2)}s</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Started At</div>
                  <div className="text-sm mt-1">
                    {new Date(selectedExecution.started_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {selectedExecution.error_message && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Error Message</div>
                  <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
                    {selectedExecution.error_message}
                  </div>
                </div>
              )}

              {selectedExecution.input_data && Object.keys(selectedExecution.input_data).length > 0 && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Input Data</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-40">
                    {JSON.stringify(selectedExecution.input_data, null, 2)}
                  </pre>
                </div>
              )}

              {selectedExecution.output_data && Object.keys(selectedExecution.output_data).length > 0 && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Output Data</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-40">
                    {JSON.stringify(selectedExecution.output_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>Close</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
