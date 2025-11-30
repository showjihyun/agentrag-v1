'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { ImprovedBlockPalette } from '@/components/workflow/ImprovedBlockPalette';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Save, AlertCircle, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { Node, Edge } from 'reactflow';
import { validateWorkflow, getValidationSummary, type ValidationError } from '@/lib/workflow-validation';
import { instantiateTemplate, getTemplate } from '@/lib/workflow-templates';
import { useSearchParams } from 'next/navigation';
import { logger } from '@/lib/logger';

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

export default function NewWorkflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [name, setName] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [description, setDescription] = useState('');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [saving, setSaving] = useState(false);
  const [loadingBlocks, setLoadingBlocks] = useState(true);

  // Load template if specified
  useEffect(() => {
    const templateId = searchParams.get('template');
    if (templateId) {
      const template = getTemplate(templateId);
      if (template) {
        const instantiated = instantiateTemplate(templateId);
        if (instantiated) {
          setName(template.name);
          setDescription(template.description);
          setNodes(instantiated.nodes);
          setEdges(instantiated.edges);
          toast({
            title: 'Template Loaded',
            description: `Loaded "${template.name}" template`,
          });
        }
      }
    }
  }, [searchParams]);

  // Load blocks and tools
  useEffect(() => {
    loadBlocksAndTools();
  }, []);

  const loadBlocksAndTools = async () => {
    try {
      setLoadingBlocks(true);
      // Just load data for validation, ImprovedBlockPalette has its own data
      await Promise.all([
        agentBuilderAPI.getBlocks(),
        agentBuilderAPI.getTools(),
        agentBuilderAPI.getAgents().catch(() => []),
      ]);
      
      logger.log('Blocks and tools loaded successfully');
    } catch (error: any) {
      console.error('Error loading blocks and tools:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load blocks and tools',
      });
    } finally {
      setLoadingBlocks(false);
    }
  };

  const handleNodesChange = useCallback((updatedNodes: Node[]) => {
    logger.log('🔄 Nodes changed:', updatedNodes.length);
    setNodes(updatedNodes);
    // Validate on change
    const result = validateWorkflow(updatedNodes, edges);
    setValidationErrors([...result.errors, ...result.warnings]);
  }, [edges]);

  const handleEdgesChange = useCallback((updatedEdges: Edge[]) => {
    logger.log('🔗 Edges changed:', updatedEdges.length);
    setEdges(updatedEdges);
    // Validate on change
    const result = validateWorkflow(nodes, updatedEdges);
    setValidationErrors([...result.errors, ...result.warnings]);
  }, [nodes]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (name.trim() && !saving) {
          handleSave();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [name, saving]);

  const handleSave = async () => {
    logger.log('💾 Saving new workflow...');
    logger.log('📊 Current state:', {
      nodes: nodes.length,
      edges: edges.length,
      name,
      description,
    });
    logger.log('🔗 Edges:', edges);

    if (!name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Workflow name is required',
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
          logger.log(`🔄 Converting node ID: ${node.id} → ${nodeId}`);
        }
        return { ...node, id: nodeId };
      });
      
      // Convert edge IDs and references
      const convertedEdges = edges.map(edge => {
        let edgeId = edge.id;
        if (!isValidUUID(edgeId)) {
          edgeId = generateUUID();
          logger.log(`🔄 Converting edge ID: ${edge.id} → ${edgeId}`);
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

      logger.log('💾 Saving with converted IDs:', {
        nodes: convertedNodes.length,
        edges: convertedEdges.length,
        entryPoint,
      });

      const workflow = await agentBuilderAPI.createWorkflow({
        name,
        description,
        nodes: convertedNodes.map(node => {
          return {
            id: node.id,
            node_type: node.type, // 직접 매핑 - 'control' 대신 실제 타입 사용
            node_ref_id: node.data?.agentId || node.data?.blockId || null,
            position_x: node.position.x,
            position_y: node.position.y,
            configuration: {
              ...node.data,
              type: node.type, // 백업용으로 configuration에도 저장
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
        description: 'Workflow created successfully',
      });

      router.push(`/agent-builder/workflows/${workflow.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create workflow',
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
          <Button 
            onClick={handleSave} 
            disabled={saving || !name.trim()}
            className={!name.trim() ? 'opacity-50 cursor-not-allowed' : ''}
          >
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 
             !name.trim() ? 'Enter Name First' : 
             'Save Workflow'}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar - Workflow Name & Description */}
        <div className="border-b bg-background p-4">
          <div className="flex gap-4 items-start">
            <div className="flex-1 space-y-3">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Workflow Name *"
                    className={`text-lg font-semibold ${!name.trim() && saving ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
                    required
                  />
                  {!name.trim() && saving && (
                    <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                      <span>⚠️</span>
                      <span>Workflow name is required</span>
                    </p>
                  )}
                </div>
                <div className="flex-1">
                  <Input
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Description (optional)"
                    className="text-sm"
                  />
                </div>
              </div>
              
              {/* Validation Errors - Compact */}
              {validationErrors.length > 0 && (
                <div className="flex gap-2 text-xs">
                  {validationErrors.filter(e => e.severity === 'error').length > 0 && (
                    <div className="flex items-center gap-1 text-red-600">
                      <AlertCircle className="h-3 w-3" />
                      <span>{validationErrors.filter(e => e.severity === 'error').length} error(s)</span>
                    </div>
                  )}
                  {validationErrors.filter(e => e.severity === 'warning').length > 0 && (
                    <div className="flex items-center gap-1 text-yellow-600">
                      <AlertTriangle className="h-3 w-3" />
                      <span>{validationErrors.filter(e => e.severity === 'warning').length} warning(s)</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Canvas Area */}
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
