'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { BlockPalette, BlockConfig } from '@/components/workflow/BlockPalette';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Save, Eye, AlertCircle, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { Node, Edge } from 'reactflow';
import { validateWorkflow, getValidationSummary, type ValidationError } from '@/lib/workflow-validation';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  is_active: boolean;
}

// UUID v4 generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Check if string is valid UUID
function isValidUUID(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
}

export default function EditWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [blocks, setBlocks] = useState<BlockConfig[]>([]);
  const [loadingBlocks, setLoadingBlocks] = useState(true);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  useEffect(() => {
    loadWorkflow();
    loadBlocksAndTools();
  }, [workflowId]);

  const loadBlocksAndTools = async () => {
    try {
      setLoadingBlocks(true);
      const [blocksData, toolsData, agentsResponse] = await Promise.all([
        agentBuilderAPI.getBlocks(),
        agentBuilderAPI.getTools(),
        agentBuilderAPI.getAgents().catch(() => []),
      ]);

      // Handle agents response (could be array or object with agents property)
      const agentsData = Array.isArray(agentsResponse) 
        ? agentsResponse 
        : (agentsResponse as any)?.agents || [];

      // Convert blocks to BlockConfig format
      const blockConfigs: BlockConfig[] = [
        // Control flow nodes
        {
          type: 'start',
          name: 'Start',
          description: 'Workflow starting point',
          category: 'control' as const,
          bg_color: '#10b981',
          icon: '▶️',
          nodeType: 'start',
        },
        {
          type: 'end',
          name: 'End',
          description: 'Workflow ending point',
          category: 'control' as const,
          bg_color: '#ef4444',
          icon: '🏁',
          nodeType: 'end',
        },
        {
          type: 'condition',
          name: 'Condition',
          description: 'Branch based on condition',
          category: 'control' as const,
          bg_color: '#f59e0b',
          icon: '◆',
          nodeType: 'condition',
        },
        // Trigger nodes
        {
          type: 'trigger_manual',
          name: 'Manual Trigger',
          description: 'Start workflow manually',
          category: 'triggers' as const,
          bg_color: '#eab308',
          icon: '⚡',
          nodeType: 'trigger',
          triggerType: 'manual',
        },
        {
          type: 'trigger_schedule',
          name: 'Schedule Trigger',
          description: 'Run on a schedule (cron)',
          category: 'triggers' as const,
          bg_color: '#3b82f6',
          icon: '🕐',
          nodeType: 'trigger',
          triggerType: 'schedule',
        },
        {
          type: 'trigger_webhook',
          name: 'Webhook Trigger',
          description: 'Trigger via HTTP webhook',
          category: 'triggers' as const,
          bg_color: '#a855f7',
          icon: '🔗',
          nodeType: 'trigger',
          triggerType: 'webhook',
        },
        {
          type: 'trigger_email',
          name: 'Email Trigger',
          description: 'Trigger when email received',
          category: 'triggers' as const,
          bg_color: '#10b981',
          icon: '📧',
          nodeType: 'trigger',
          triggerType: 'email',
        },
        {
          type: 'trigger_event',
          name: 'Event Trigger',
          description: 'Trigger on system event',
          category: 'triggers' as const,
          bg_color: '#ef4444',
          icon: '📅',
          nodeType: 'trigger',
          triggerType: 'event',
        },
        {
          type: 'trigger_database',
          name: 'Database Trigger',
          description: 'Trigger on database change',
          category: 'triggers' as const,
          bg_color: '#6366f1',
          icon: '💾',
          nodeType: 'trigger',
          triggerType: 'database',
        },
        // Agents
        ...agentsData.map((agent: any) => ({
          type: `agent_${agent.id}`,
          name: agent.name,
          description: agent.description || 'AI Agent',
          category: 'agents' as const,
          bg_color: '#a855f7',
          icon: '🤖',
          agentId: agent.id,
          nodeType: 'agent',
        })),
        // Blocks
        ...blocksData.map((block: any) => ({
          type: `block_${block.id}`,
          name: block.name,
          description: block.description || '',
          category: 'blocks' as const,
          bg_color: '#3b82f6',
          icon: block.block_type?.substring(0, 2).toUpperCase() || 'BL',
          inputs: block.input_schema,
          outputs: block.output_schema,
        })),
        // Tools
        ...toolsData.map((tool: any) => ({
          type: `tool_${tool.id}`,
          name: tool.name,
          description: tool.description || '',
          category: 'tools' as const,
          bg_color: '#10b981',
          icon: '🔧',
          inputs: tool.input_schema,
          outputs: tool.output_schema,
        })),
      ];

      console.log('Loaded blocks:', blocksData.length);
      console.log('Loaded tools:', toolsData.length);
      console.log('Loaded agents:', agentsData.length);
      console.log('Total blockConfigs:', blockConfigs.length);
      console.log('BlockConfigs by category:', {
        control: blockConfigs.filter(b => b.category === 'control').length,
        triggers: blockConfigs.filter(b => b.category === 'triggers').length,
        agents: blockConfigs.filter(b => b.category === 'agents').length,
        blocks: blockConfigs.filter(b => b.category === 'blocks').length,
        tools: blockConfigs.filter(b => b.category === 'tools').length,
      });

      setBlocks(blockConfigs);
    } catch (error: any) {
      console.error('Error loading blocks and tools:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load blocks and tools',
        variant: 'destructive',
      });
    } finally {
      setLoadingBlocks(false);
    }
  };

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      setWorkflow(data);
      setName(data.name);
      setDescription(data.description || '');
      
      const loadedNodes: Node[] = data.graph_definition.nodes.map((node: any) => ({
        id: node.id,
        type: node.node_type === 'control' ? (node.configuration?.type || 'block') : node.node_type,
        position: node.position || { x: node.position_x || 0, y: node.position_y || 0 },
        data: node.configuration || node.data || {},
      }));
      
      const loadedEdges: Edge[] = data.graph_definition.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source_node_id || edge.source,
        target: edge.target_node_id || edge.target,
        sourceHandle: edge.source_handle || edge.sourceHandle,
        targetHandle: edge.target_handle || edge.targetHandle,
      }));

      setNodes(loadedNodes);
      setEdges(loadedEdges);
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

  const handleNodesChange = useCallback((updatedNodes: Node[]) => {
    console.log('🔄 Nodes changed:', updatedNodes.length);
    setNodes(updatedNodes);
    setHasChanges(true);
    // Validate on change
    const errors = validateWorkflow(updatedNodes, edges);
    setValidationErrors(errors);
  }, [edges]);

  const handleEdgesChange = useCallback((updatedEdges: Edge[]) => {
    console.log('🔗 Edges changed:', updatedEdges.length);
    setEdges(updatedEdges);
    setHasChanges(true);
    // Validate on change
    const errors = validateWorkflow(nodes, updatedEdges);
    setValidationErrors(errors);
  }, [nodes]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (name.trim() && hasChanges && !saving) {
          handleSave();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [name, hasChanges, saving]);

  const handleSave = async () => {
    console.log('💾 Saving workflow...');
    console.log('📊 Current state:', {
      nodes: nodes.length,
      edges: edges.length,
      name,
      description,
    });
    console.log('🔗 Edges:', edges);

    if (!name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Workflow name is required',
        variant: 'destructive',
      });
      return;
    }

    // Validate workflow
    const errors = validateWorkflow(nodes, edges);
    const summary = getValidationSummary(errors);
    
    if (summary.hasErrors) {
      toast({
        title: 'Validation Failed',
        description: `Please fix ${summary.errorCount} error(s) before saving`,
        variant: 'destructive',
      });
      return;
    }
    
    if (summary.hasWarnings) {
      const confirmed = confirm(
        `Workflow has ${summary.warningCount} warning(s). Do you want to save anyway?`
      );
      if (!confirmed) return;
    }

    setSaving(true);
    try {
      // Create ID mapping for old IDs to new UUIDs
      const idMapping = new Map<string, string>();
      
      // Convert node IDs to UUIDs if needed
      const convertedNodes = nodes.map(node => {
        let nodeId = node.id;
        if (!isValidUUID(nodeId)) {
          nodeId = generateUUID();
          idMapping.set(node.id, nodeId);
          console.log(`🔄 Converting node ID: ${node.id} → ${nodeId}`);
        }
        return { ...node, id: nodeId };
      });
      
      // Convert edge IDs and references
      const convertedEdges = edges.map(edge => {
        let edgeId = edge.id;
        if (!isValidUUID(edgeId)) {
          edgeId = generateUUID();
          console.log(`🔄 Converting edge ID: ${edge.id} → ${edgeId}`);
        }
        
        return {
          ...edge,
          id: edgeId,
          source: idMapping.get(edge.source) || edge.source,
          target: idMapping.get(edge.target) || edge.target,
        };
      });
      
      // Find the start node as entry point
      const startNode = convertedNodes.find(node => node.type === 'start' || node.type === 'trigger');
      const entryPoint = startNode?.id || (convertedNodes.length > 0 ? convertedNodes[0].id : '');

      console.log('💾 Updating with converted IDs:', {
        nodes: convertedNodes.length,
        edges: convertedEdges.length,
        entryPoint,
      });

      await agentBuilderAPI.updateWorkflow(workflowId, {
        name,
        description,
        nodes: convertedNodes.map(node => {
          const isControl = node.type === 'start' || node.type === 'end' || 
                           node.type === 'condition' || node.type === 'trigger';
          return {
            id: node.id,
            node_type: isControl ? 'control' : node.type,
            node_ref_id: isControl ? null : (node.data?.agentId || node.data?.blockId || null),
            position_x: node.position.x,
            position_y: node.position.y,
            configuration: {
              ...node.data,
              type: node.type, // Preserve the actual node type for execution
            },
          };
        }),
        edges: convertedEdges.map(edge => ({
          id: edge.id,
          source_node_id: edge.source,
          target_node_id: edge.target,
          edge_type: 'normal',
          source_handle: edge.sourceHandle,
          target_handle: edge.targetHandle,
        })),
        entry_point: entryPoint,
      });

      toast({
        title: 'Success',
        description: 'Workflow updated successfully',
      });

      setHasChanges(false);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update workflow',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
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

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                if (hasChanges) {
                  if (confirm('You have unsaved changes. Are you sure you want to leave?')) {
                    router.back();
                  }
                } else {
                  router.back();
                }
              }}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Edit Workflow</h1>
              <p className="text-sm text-muted-foreground">
                {hasChanges ? 'Unsaved changes' : 'All changes saved'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/agent-builder/workflows/${workflowId}`)}
            >
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={saving || !hasChanges || !name.trim()}
              className={!name.trim() ? 'opacity-50 cursor-not-allowed' : ''}
            >
              <Save className="mr-2 h-4 w-4" />
              {saving ? 'Saving...' : 
               !name.trim() ? 'Enter Name First' :
               !hasChanges ? 'No Changes' : 
               'Save Changes'}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-80 border-r bg-background overflow-y-auto">
          <div className="p-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Workflow Details</CardTitle>
                <CardDescription>Basic information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      setHasChanges(true);
                    }}
                    placeholder="My Workflow"
                    className={!name.trim() && saving ? 'border-red-500 focus-visible:ring-red-500' : ''}
                    required
                  />
                  {!name.trim() && saving && (
                    <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                      <span>⚠️</span>
                      <span>Workflow name is required</span>
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => {
                      setDescription(e.target.value);
                      setHasChanges(true);
                    }}
                    placeholder="Describe what this workflow does..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <BlockPalette blocks={blocks} />
            
            {/* Validation Errors */}
            {validationErrors.length > 0 && (
              <div className="mt-4">
                {validationErrors.filter(e => e.type === 'error').length > 0 && (
                  <Alert variant="destructive" className="mb-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Errors</AlertTitle>
                    <AlertDescription>
                      <ul className="list-disc list-inside text-sm mt-2">
                        {validationErrors
                          .filter(e => e.type === 'error')
                          .map((error, i) => (
                            <li key={i}>{error.message}</li>
                          ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
                
                {validationErrors.filter(e => e.type === 'warning').length > 0 && (
                  <Alert className="border-yellow-500 bg-yellow-50">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <AlertTitle className="text-yellow-800">Warnings</AlertTitle>
                    <AlertDescription className="text-yellow-700">
                      <ul className="list-disc list-inside text-sm mt-2">
                        {validationErrors
                          .filter(e => e.type === 'warning')
                          .slice(0, 3)
                          .map((error, i) => (
                            <li key={i}>{error.message}</li>
                          ))}
                        {validationErrors.filter(e => e.type === 'warning').length > 3 && (
                          <li>+{validationErrors.filter(e => e.type === 'warning').length - 3} more warnings</li>
                        )}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Center - Workflow Canvas */}
        <div className="flex-1 bg-muted/20">
          <WorkflowEditor
            workflowId={workflowId}
            initialNodes={nodes}
            initialEdges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onSave={handleSave}
          />
        </div>
      </div>
    </div>
  );
}
