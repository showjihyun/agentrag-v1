'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { logger } from '@/lib/logger';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Edit, Play, Copy, Trash, GitBranch, Clock, CheckCircle, XCircle, Eye } from 'lucide-react';
import type { Node, Edge } from 'reactflow';
import { useWorkflowExecutionStream } from '@/hooks/useWorkflowExecutionStream';
import { ExecutionProgress } from '@/components/workflow/ExecutionProgress';
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
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('canvas');
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRecord | null>(null);
  const [executionDetailsOpen, setExecutionDetailsOpen] = useState(false);

  // SSE for real-time execution status
  const {
    nodeStatuses,
    isConnected,
    isComplete,
  } = useWorkflowExecutionStream({
    workflowId,
    executionId: executionId || undefined,
    enabled: executing,
    onComplete: (status) => {
      logger.log('✅ Workflow execution completed:', status);
      setExecuting(false);
      loadExecutions();
      toast({
        title: 'Execution Complete',
        description: `Workflow execution ${status}`,
      });
    },
    onError: (error) => {
      logger.error('❌ Workflow execution error:', error);
      setExecuting(false);
      toast({
        title: 'Execution Error',
        description: error,
        variant: 'error',
      });
    },
  });

  // Debug: Log SSE connection status and node statuses
  useEffect(() => {
    logger.log('🔍 SSE Debug:', {
      executing,
      executionId,
      isConnected,
      isComplete,
      nodeStatusesCount: Object.keys(nodeStatuses).length,
      nodeStatuses,
    });
  }, [executing, executionId, isConnected, isComplete, nodeStatuses]);

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
      logger.log('📊 Workflow loaded:', {
        id: data.id,
        name: data.name,
        nodesCount: data.graph_definition?.nodes?.length || 0,
        edgesCount: data.graph_definition?.edges?.length || 0,
        nodes: data.graph_definition?.nodes,
        edges: data.graph_definition?.edges,
      });
      setWorkflow(data);
    } catch (error: any) {
      console.error('❌ Failed to load workflow:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    logger.log('🚀 Starting workflow execution:', workflowId);
    
    // Generate execution ID
    const execId = `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setExecutionId(execId);
    setExecuting(true);
    
    // Stay on current tab - user can manually switch to executions tab if needed
    // setActiveTab('executions'); // Removed: Don't auto-switch tabs
    
    toast({
      title: 'Executing',
      description: 'Workflow execution started. Check Executions tab for logs.',
    });
    
    // SSE will handle the execution and status updates
    // The useWorkflowExecutionStream hook will automatically connect
    // and receive real-time updates
  };

  const handleDuplicate = async () => {
    if (!workflow) return;

    try {
      // Use the new duplicate endpoint
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/duplicate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate workflow');
      }

      const newWorkflow = await response.json();

      toast({
        title: '✅ Workflow Duplicated',
        description: 'Successfully created a copy of the workflow',
      });

      // Navigate to the new workflow
      router.push(`/agent-builder/workflows/${newWorkflow.id}`);
    } catch (error: any) {
      toast({
        title: '❌ Error',
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

  const nodes: Node[] = workflow.graph_definition.nodes.map((node: any) => {
    // Determine node type
    let nodeType = node.node_type || node.type;
    
    // Handle control nodes - they should have a specific type in configuration
    if (nodeType === 'control') {
      nodeType = node.configuration?.type || node.configuration?.nodeType || node.data?.type || 'start';
      logger.log('🎛️ Control node detected:', {
        originalType: node.node_type,
        configType: node.configuration?.type,
        finalType: nodeType,
        configuration: node.configuration,
      });
    }
    
    const transformedNode = {
      id: node.id,
      type: nodeType,
      position: node.position || { x: node.position_x || 0, y: node.position_y || 0 },
      data: node.configuration || node.data || {},
    };
    
    logger.log('🔄 Node transformation:', {
      original: { id: node.id, type: node.node_type, config: node.configuration },
      transformed: { id: transformedNode.id, type: transformedNode.type, data: transformedNode.data },
    });
    
    return transformedNode;
  });

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

          <TabsContent value="canvas" className="flex-1 m-0 bg-muted/20 flex flex-col overflow-hidden">
            {/* Canvas Area - 70% */}
            <div className="flex-1 overflow-hidden">
              <WorkflowEditor
                workflowId={workflowId}
                initialNodes={nodes}
                initialEdges={edges}
                readOnly={true}
              />
            </div>
            
            {/* Execution Logs Panel - 30% */}
            <div className="h-[30%] min-h-[200px] border-t bg-white dark:bg-gray-950">
              <Card className="h-full flex flex-col rounded-none border-0">
                <CardHeader className="p-3 border-b bg-gray-50 dark:bg-gray-900">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Execution Logs
                      {executing && (
                        <Badge variant="secondary" className="ml-2">
                          <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
                          Running
                        </Badge>
                      )}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                      {executions.length} executions
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto p-3">
                  {executions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No execution logs yet</p>
                      <p className="text-xs mt-1">Click Execute to run the workflow</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {executions.slice(0, 10).map((exec) => (
                        <div
                          key={exec.id}
                          className="p-2 rounded border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors cursor-pointer"
                          onClick={() => {
                            setSelectedExecution(exec);
                            setExecutionDetailsOpen(true);
                          }}
                        >
                          <div className="flex items-start gap-2">
                            <span className={`text-sm font-mono font-bold ${
                              exec.status === 'success' ? 'text-green-600' :
                              exec.status === 'failed' ? 'text-red-600' :
                              'text-blue-600'
                            }`}>
                              {exec.status === 'success' ? '✓' :
                               exec.status === 'failed' ? '✗' :
                               '⟳'}
                            </span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-medium truncate">
                                  Execution {exec.id.substring(0, 8)}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  {exec.duration.toFixed(2)}s
                                </Badge>
                                <Badge
                                  variant={
                                    exec.status === 'success' ? 'default' :
                                    exec.status === 'failed' ? 'destructive' :
                                    'secondary'
                                  }
                                  className="text-xs"
                                >
                                  {exec.status}
                                </Badge>
                              </div>
                              {exec.error_message && (
                                <p className="text-xs text-red-600 line-clamp-1">
                                  {exec.error_message}
                                </p>
                              )}
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(exec.started_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="executions" className="flex-1 m-0 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-auto">
              <div className="container mx-auto p-6">
                {/* Real-time Execution Progress */}
                {executing && (
                  <div className="mb-4">
                    <ExecutionProgress
                      workflowId={workflowId}
                      executionId={executionId || undefined}
                      isExecuting={executing}
                      nodeStatuses={nodeStatuses}
                      onNodeClick={(nodeId) => {
                        logger.log('Node clicked:', nodeId);
                        // Could highlight node in canvas
                      }}
                    />
                  </div>
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
                                  {exec.status === 'success' ? (
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
                                      exec.status === 'success'
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
            </div>
            
            {/* Execution Logs Panel - Bottom 30% */}
            <div className="h-[30%] min-h-[200px] border-t bg-gray-50 dark:bg-gray-900">
              <Card className="h-full flex flex-col rounded-none border-0">
                <CardHeader className="p-3 border-b bg-white dark:bg-gray-950">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Execution Logs
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                      {executions.length} executions
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto p-3">
                  {executions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No execution logs yet</p>
                      <p className="text-xs mt-1">Logs will appear here when you run workflows</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {executions.slice(0, 10).map((exec) => (
                        <div
                          key={exec.id}
                          className="p-2 rounded border border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                          onClick={() => {
                            setSelectedExecution(exec);
                            setExecutionDetailsOpen(true);
                          }}
                        >
                          <div className="flex items-start gap-2">
                            <span className={`text-sm font-mono ${
                              exec.status === 'success' ? 'text-green-600' :
                              exec.status === 'failed' ? 'text-red-600' :
                              'text-blue-600'
                            }`}>
                              {exec.status === 'success' ? '✓' :
                               exec.status === 'failed' ? '✗' :
                               '⟳'}
                            </span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-medium truncate">
                                  Execution {exec.id.substring(0, 8)}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  {exec.duration.toFixed(2)}s
                                </Badge>
                                <Badge
                                  variant={
                                    exec.status === 'success' ? 'default' :
                                    exec.status === 'failed' ? 'destructive' :
                                    'secondary'
                                  }
                                  className="text-xs"
                                >
                                  {exec.status}
                                </Badge>
                              </div>
                              {exec.error_message && (
                                <p className="text-xs text-red-600 line-clamp-1">
                                  {exec.error_message}
                                </p>
                              )}
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(exec.started_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
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
