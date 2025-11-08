'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { BlockPalette, BlockConfig } from '@/components/workflow/BlockPalette';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Save } from 'lucide-react';
import type { Node, Edge } from 'reactflow';

export default function NewWorkflowPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [saving, setSaving] = useState(false);
  const [blocks, setBlocks] = useState<BlockConfig[]>([]);
  const [loadingBlocks, setLoadingBlocks] = useState(true);

  // Load blocks and tools
  useEffect(() => {
    loadBlocksAndTools();
  }, []);

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

  const handleNodesChange = useCallback((updatedNodes: Node[]) => {
    setNodes(updatedNodes);
  }, []);

  const handleEdgesChange = useCallback((updatedEdges: Edge[]) => {
    setEdges(updatedEdges);
  }, []);

  const handleSave = async () => {
    if (!name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Workflow name is required',
        variant: 'destructive',
      });
      return;
    }

    if (nodes.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'Add at least one node to the workflow',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      const workflow = await agentBuilderAPI.createWorkflow({
        name,
        description,
        graph_definition: {
          nodes: nodes.map(node => ({
            id: node.id,
            type: node.type,
            position: node.position,
            data: node.data,
          })),
          edges: edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            sourceHandle: edge.sourceHandle,
            targetHandle: edge.targetHandle,
          })),
        },
      });

      toast({
        title: 'Success',
        description: 'Workflow created successfully',
      });

      router.push(`/agent-builder/workflows/${workflow.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create workflow',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Create New Workflow</h1>
              <p className="text-sm text-muted-foreground">
                Design your multi-step agent workflow
              </p>
            </div>
          </div>
          <Button onClick={handleSave} disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Workflow'}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Block Palette */}
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
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Workflow"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe what this workflow does..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <BlockPalette blocks={blocks} />
          </div>
        </div>

        {/* Center - Workflow Canvas */}
        <div className="flex-1 bg-muted/20">
          <WorkflowEditor
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
