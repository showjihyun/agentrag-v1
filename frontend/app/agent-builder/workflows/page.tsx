'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, GitBranch, MoreVertical, Edit, Play, Copy, Trash, Eye, CheckCircle, XCircle, Clock, Zap, Sparkles, Wand2 } from 'lucide-react';
import { WorkflowGeneratorModal } from '@/components/workflow/WorkflowGeneratorModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { logger } from '@/lib/logger';
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
  user_id: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  is_public: boolean;
  is_active?: boolean; // Optional for backward compatibility
  created_at: string;
  updated_at?: string;
  execution_count?: number;
  last_execution_status?: 'success' | 'failed' | 'running' | 'completed';
  triggers?: Array<{
    id: string;
    name: string;
    type: string;
  }>;
}

export default function WorkflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created' | 'updated' | 'executions'>('updated');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [workflowToDelete, setWorkflowToDelete] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);

  const templates = [
    {
      id: 'template-1',
      name: 'Customer Support Automation',
      description: 'Classify and route customer inquiries automatically',
      category: 'Support',
      nodes: 8,
      icon: '🎧',
    },
    {
      id: 'template-2',
      name: 'Content Generation Pipeline',
      description: 'Generate, review, and publish content with AI',
      category: 'Content',
      nodes: 6,
      icon: '✍️',
    },
    {
      id: 'template-3',
      name: 'Data Analysis Workflow',
      description: 'Fetch, analyze, and visualize data automatically',
      category: 'Analytics',
      nodes: 7,
      icon: '📊',
    },
    {
      id: 'template-4',
      name: 'Email Processing',
      description: 'Process incoming emails and create tasks',
      category: 'Automation',
      nodes: 5,
      icon: '📧',
    },
  ];

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      logger.log('🔄 Loading workflows...');
      logger.log('🔑 Token:', localStorage.getItem('token') ? 'Present' : 'Missing');
      
      const response = await agentBuilderAPI.getWorkflows();
      logger.log('✅ Workflows loaded:', response);
      logger.log('📊 Workflows count:', response.workflows?.length || 0);
      
      if (response.workflows && response.workflows.length > 0) {
        logger.log('📝 First workflow:', response.workflows[0]);
      }
      
      setWorkflows(response.workflows || []);
    } catch (error: any) {
      logger.error('❌ Failed to load workflows:', error);
      logger.error('❌ Error details:', {
        message: error.message,
        status: error.status,
        detail: error.detail,
      });
      
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflows',
        variant: 'error',
      });
      // Set empty array on error to show empty state
      setWorkflows([]);
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
        description: 'Opening workflow builder with execution logs...',
      });
      
      // Navigate to builder page where execution logs are visible
      router.push(`/agent-builder/workflows/builder?workflowId=${workflowId}&autoExecute=true`);
      
    } catch (error: any) {
      // Handle API errors
      const errorMessage = error.message || error.detail || 'Failed to execute workflow';
      toast({
        title: 'Error',
        description: errorMessage,
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

  const filteredWorkflows = workflows
    .filter((w) => {
      // Search filter
      const matchesSearch = w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        w.description?.toLowerCase().includes(searchQuery.toLowerCase());
      
      // Status filter (use is_active if available, otherwise use is_public)
      const isActive = w.is_active !== undefined ? w.is_active : w.is_public;
      const matchesStatus = filterStatus === 'all' || 
        (filterStatus === 'active' && isActive) ||
        (filterStatus === 'inactive' && !isActive);
      
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      // Sort
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'updated':
          return new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime();
        case 'executions':
          return (b.execution_count || 0) - (a.execution_count || 0);
        default:
          return 0;
      }
    });

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
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowTemplates(!showTemplates)}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {showTemplates ? 'Hide Templates' : 'Browse Templates'}
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowGenerator(true)}
            className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800 hover:border-purple-400"
          >
            <Wand2 className="mr-2 h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span className="text-purple-600 dark:text-purple-400">AI 생성</span>
          </Button>
          <Button onClick={() => router.push('/agent-builder/workflows/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Workflow
          </Button>
        </div>
      </div>

      {/* Statistics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Workflows</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workflows.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {workflows.filter(w => w.is_active !== undefined ? w.is_active : w.is_public).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {workflows.reduce((sum, w) => sum + (w.execution_count || 0), 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg Nodes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {workflows.length > 0 
                ? Math.round(workflows.reduce((sum, w) => sum + (w.graph_definition?.nodes?.length || 0), 0) / workflows.length)
                : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Templates Section */}
      {showTemplates && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Workflow Templates
            </CardTitle>
            <CardDescription>
              Start with a pre-built template and customize it to your needs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {templates.map((template) => (
                <Card
                  key={template.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow border-2 hover:border-primary"
                  onClick={() => {
                    toast({
                      title: 'Creating from template',
                      description: `Creating "${template.name}"...`,
                    });
                    router.push(`/agent-builder/workflows/new?template=${template.id}`);
                  }}
                >
                  <CardHeader>
                    <div className="text-3xl mb-2">{template.icon}</div>
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-xs">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {template.nodes} nodes
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {template.category}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search, Filter, and Sort */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search workflows by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="px-3 py-2 border rounded-md bg-background text-sm"
          >
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border rounded-md bg-background text-sm"
          >
            <option value="updated">Last Updated</option>
            <option value="created">Created Date</option>
            <option value="name">Name (A-Z)</option>
            <option value="executions">Most Executed</option>
          </select>
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
                <div className="space-y-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline">
                      {workflow.graph_definition?.nodes?.length || 0} nodes
                    </Badge>
                    <Badge variant="outline">
                      {workflow.graph_definition?.edges?.length || 0} edges
                    </Badge>
                    {(workflow.is_active !== undefined ? workflow.is_active : workflow.is_public) && (
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
                  
                  {/* Workflow Structure Info */}
                  {(() => {
                    const nodes = workflow.graph_definition?.nodes || [];
                    const edges = workflow.graph_definition?.edges || [];
                    
                    // Count node types
                    const nodeTypes = {
                      start: nodes.filter((n: any) => 
                        n.type === 'start' || n.configuration?.type === 'start'
                      ).length,
                      trigger: nodes.filter((n: any) => 
                        n.type === 'trigger' || n.configuration?.type === 'trigger'
                      ).length,
                      agent: nodes.filter((n: any) => 
                        n.node_type === 'agent' || n.type === 'agent'
                      ).length,
                      block: nodes.filter((n: any) => 
                        n.node_type === 'block' || n.type === 'block'
                      ).length,
                      condition: nodes.filter((n: any) => 
                        n.type === 'condition' || n.configuration?.type === 'condition'
                      ).length,
                      end: nodes.filter((n: any) => 
                        n.type === 'end' || n.configuration?.type === 'end'
                      ).length,
                    };
                    
                    const triggerNodes = nodes.filter((n: any) => 
                      n.type === 'trigger' || n.configuration?.type === 'trigger'
                    );
                    
                    return (
                      <div className="pt-2 border-t space-y-2">
                        {/* Node Type Summary */}
                        <div className="flex items-center gap-2 flex-wrap">
                          {nodeTypes.start > 0 && (
                            <Badge variant="outline" className="text-xs">
                              ▶️ {nodeTypes.start} Start
                            </Badge>
                          )}
                          {nodeTypes.trigger > 0 && (
                            <Badge variant="outline" className="text-xs">
                              ⚡ {nodeTypes.trigger} Trigger
                            </Badge>
                          )}
                          {nodeTypes.agent > 0 && (
                            <Badge variant="outline" className="text-xs">
                              🤖 {nodeTypes.agent} Agent
                            </Badge>
                          )}
                          {nodeTypes.block > 0 && (
                            <Badge variant="outline" className="text-xs">
                              🧩 {nodeTypes.block} Block
                            </Badge>
                          )}
                          {nodeTypes.condition > 0 && (
                            <Badge variant="outline" className="text-xs">
                              🔀 {nodeTypes.condition} Condition
                            </Badge>
                          )}
                          {nodeTypes.end > 0 && (
                            <Badge variant="outline" className="text-xs">
                              🏁 {nodeTypes.end} End
                            </Badge>
                          )}
                        </div>
                        
                        {/* Trigger Details */}
                        {triggerNodes.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <Zap className="h-3 w-3 text-yellow-500" />
                              <span className="text-xs font-medium text-muted-foreground">
                                Triggers
                              </span>
                            </div>
                            <div className="space-y-1">
                              {triggerNodes.slice(0, 2).map((trigger: any) => {
                                const triggerType = trigger.data?.triggerType || 
                                                  trigger.configuration?.triggerType || 
                                                  'manual';
                                const triggerName = trigger.data?.name || 
                                                  trigger.configuration?.name || 
                                                  'Unnamed Trigger';
                                return (
                                  <div key={trigger.id} className="flex items-center gap-2 text-xs">
                                    <Badge variant="secondary" className="text-xs">
                                      {triggerType}
                                    </Badge>
                                    <span className="text-muted-foreground truncate">
                                      {triggerName}
                                    </span>
                                  </div>
                                );
                              })}
                              {triggerNodes.length > 2 && (
                                <span className="text-xs text-muted-foreground">
                                  +{triggerNodes.length - 2} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Workflow Complexity Indicator */}
                        {nodes.length > 0 && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>
                              {edges.length} connection{edges.length !== 1 ? 's' : ''}
                            </span>
                            <span>•</span>
                            <span>
                              {nodes.length < 5 ? 'Simple' : nodes.length < 10 ? 'Medium' : 'Complex'} workflow
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })()}
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

      {/* AI Workflow Generator Modal */}
      <WorkflowGeneratorModal
        isOpen={showGenerator}
        onClose={() => setShowGenerator(false)}
        onGenerate={async (generatedWorkflow) => {
          try {
            // Find the start node as entry point
            const startNode = generatedWorkflow.nodes.find((n: any) => n.type === 'start');
            const entryPoint = startNode ? startNode.id : generatedWorkflow.nodes[0]?.id || 'start';
            
            // Create workflow from generated definition
            const response = await agentBuilderAPI.createWorkflow({
              name: generatedWorkflow.name,
              description: generatedWorkflow.description,
              entry_point: entryPoint,
              graph_definition: {
                nodes: generatedWorkflow.nodes,
                edges: generatedWorkflow.edges,
              },
            });
            
            toast({
              title: '✨ 워크플로우 생성 완료',
              description: `"${generatedWorkflow.name}" 워크플로우가 생성되었습니다`,
              variant: 'success',
            });
            
            // Reload workflows
            await loadWorkflows();
            
            // Navigate to the new workflow
            router.push(`/agent-builder/workflows/${response.id}/designer`);
          } catch (error: any) {
            toast({
              title: '❌ 생성 실패',
              description: error.message || '워크플로우 생성 중 오류가 발생했습니다',
              variant: 'error',
            });
          }
        }}
      />
    </div>
  );
}
