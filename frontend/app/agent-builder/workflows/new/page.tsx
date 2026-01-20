'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { ImprovedBlockPalette } from '@/components/workflow/ImprovedBlockPalette';
import { NLPWorkflowGenerator } from '@/components/workflow/NLPWorkflowGenerator';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Save, AlertCircle, AlertTriangle, Sparkles, Wand2 } from 'lucide-react';
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
  const [showAIGenerator, setShowAIGenerator] = useState(false);

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

  // Map backend node types to frontend ReactFlow node types
  // Based on ImprovedBlockPalette: Tools, Control, Triggers, Blocks
  const mapNodeType = (backendType: string): string => {
    const typeMapping: Record<string, string> = {
      // Triggers
      'manual_trigger': 'trigger',
      'schedule_trigger': 'trigger',
      'webhook_trigger': 'trigger',
      'email_trigger': 'trigger',
      'file_trigger': 'trigger',
      'slack_trigger': 'trigger',
      // AI & Agents
      'ai_agent': 'ai_agent',
      'openai_chat': 'tool',
      'anthropic_claude': 'tool',
      'google_gemini': 'tool',
      // Communication
      'slack': 'slack',
      'gmail': 'email',
      'discord': 'discord',
      'telegram': 'tool',
      // API & Integration
      'http_request': 'http_request',
      'webhook': 'tool',
      'graphql': 'tool',
      // Data & Database
      'vector_search': 'tool',
      'postgres': 'database',
      'csv_parser': 'tool',
      'json_transform': 'code',
      // Code Execution
      'python_code': 'code',
      'javascript_code': 'code',
      'calculator': 'tool',
      // Control Flow
      'start': 'start',
      'end': 'end',
      'condition': 'condition',
      'loop': 'loop',
      'parallel': 'parallel',
      'delay': 'delay',
      'switch': 'switch',
      'merge': 'merge',
      'filter': 'condition',
      'transform': 'code',
      'try_catch': 'tool',
      'human_approval': 'tool',
      // Blocks
      'text_block': 'tool',
      'code_block': 'code',
      'http_block': 'http_request',
      'database_block': 'database',
      'transform_block': 'code',
      'ai_block': 'tool',
    };
    return typeMapping[backendType] || 'tool';
  };

  // Get display label for node type
  const getNodeLabel = (backendType: string, dataLabel?: string): string => {
    if (dataLabel) return dataLabel;
    const labelMapping: Record<string, string> = {
      // Triggers
      'manual_trigger': '수동 시작',
      'schedule_trigger': '스케줄 트리거',
      'webhook_trigger': '웹훅 트리거',
      'email_trigger': '이메일 트리거',
      'file_trigger': '파일 업로드 트리거',
      'slack_trigger': 'Slack 이벤트 트리거',
      // AI & Agents
      'ai_agent': 'AI 에이전트',
      'openai_chat': 'OpenAI Chat',
      'anthropic_claude': 'Claude',
      'google_gemini': 'Gemini',
      // Communication
      'slack': 'Slack',
      'gmail': 'Gmail',
      'discord': 'Discord',
      'telegram': 'Telegram',
      // API & Integration
      'http_request': 'HTTP 요청',
      'webhook': '웹훅',
      'graphql': 'GraphQL',
      // Data & Database
      'vector_search': '벡터 검색',
      'postgres': 'PostgreSQL',
      'csv_parser': 'CSV 파서',
      'json_transform': 'JSON 변환',
      // Code Execution
      'python_code': 'Python 코드',
      'javascript_code': 'JavaScript',
      'calculator': '계산기',
      // Control Flow
      'start': '시작',
      'end': '종료',
      'condition': '조건 분기',
      'loop': '반복',
      'parallel': '병렬 실행',
      'delay': '지연',
      'switch': '다중 분기',
      'merge': '병합',
      'filter': '필터',
      'transform': '데이터 변환',
      'try_catch': '에러 처리',
      'human_approval': '사람 승인',
      // Blocks
      'text_block': '텍스트',
      'code_block': '코드 블록',
      'http_block': 'HTTP 블록',
      'database_block': 'DB 블록',
      'transform_block': '변환 블록',
      'ai_block': 'AI 블록',
    };
    return labelMapping[backendType] || backendType;
  };

  // Build node-specific configuration based on type
  // Based on ImprovedBlockPalette: Tools, Control, Triggers, Blocks
  const buildNodeConfig = (backendType: string, config: any = {}): any => {
    const baseConfig: Record<string, any> = {
      // ===== TRIGGERS =====
      'manual_trigger': { triggerType: 'manual' },
      'schedule_trigger': {
        triggerType: 'schedule',
        cron: config.cron || '0 9 * * *',
        timezone: config.timezone || 'Asia/Seoul',
      },
      'webhook_trigger': {
        triggerType: 'webhook',
        path: config.path || '/webhook',
        method: config.method || 'POST',
      },
      'email_trigger': { filter: config.filter || '' },
      'file_trigger': { path: config.path || '' },
      'slack_trigger': { event_type: config.event_type || 'message' },

      // ===== AI & AGENTS =====
      'ai_agent': {
        goal: config.goal || '',
        tools: config.tools || [],
        model: config.model || 'gpt-4o-mini',
        maxIterations: config.maxIterations || 10,
      },
      'openai_chat': {
        model: config.model || 'gpt-4o-mini',
        prompt: config.prompt || '',
        temperature: config.temperature || 0.7,
        maxTokens: config.maxTokens || 2000,
      },
      'anthropic_claude': {
        model: config.model || 'claude-3-sonnet-20240229',
        prompt: config.prompt || '',
        temperature: config.temperature || 0.7,
      },
      'google_gemini': {
        model: config.model || 'gemini-pro',
        prompt: config.prompt || '',
      },

      // ===== COMMUNICATION =====
      'slack': {
        channel: config.channel || '#general',
        message: config.message || '{{input.message}}',
      },
      'gmail': {
        to: config.to || '',
        subject: config.subject || '',
        body: config.body || '',
      },
      'discord': {
        webhook_url: config.webhook_url || '',
        message: config.message || '{{input.message}}',
      },
      'telegram': {
        chat_id: config.chat_id || '',
        message: config.message || '{{input.message}}',
      },

      // ===== API & INTEGRATION =====
      'http_request': {
        url: config.url || '',
        method: config.method || 'GET',
        headers: config.headers || {},
        body: config.body || '',
      },
      'webhook': { path: config.path || '/webhook' },
      'graphql': {
        endpoint: config.endpoint || '',
        query: config.query || '',
        variables: config.variables || {},
      },

      // ===== DATA & DATABASE =====
      'vector_search': {
        query: config.query || '{{input.query}}',
        top_k: config.top_k || 5,
        collection: config.collection || '',
      },
      'postgres': {
        query: config.query || '',
        connection: config.connection || '',
      },
      'csv_parser': {
        file_path: config.file_path || '',
        delimiter: config.delimiter || ',',
      },
      'json_transform': {
        mapping: config.mapping || {},
      },

      // ===== CODE EXECUTION =====
      'python_code': {
        code: config.code || '# Python code here\nresult = input_data',
      },
      'javascript_code': {
        code: config.code || '// JavaScript code here\nreturn inputData;',
      },
      'calculator': {
        expression: config.expression || '',
      },

      // ===== CONTROL FLOW =====
      'start': {},
      'end': {},
      'condition': {
        condition: config.condition || '',
        trueLabel: config.trueLabel || 'True',
        falseLabel: config.falseLabel || 'False',
      },
      'loop': {
        items: config.items || '{{input.items}}',
        batch_size: config.batch_size || 1,
      },
      'parallel': {
        branches: config.branches || 2,
      },
      'delay': {
        duration: config.duration || 1000,
        unit: config.unit || 'ms',
      },
      'switch': {
        expression: config.expression || '',
        cases: config.cases || [],
      },
      'merge': {
        mode: config.mode || 'concat',
      },
      'filter': {
        condition: config.condition || '',
      },
      'transform': {
        expression: config.expression || '',
      },
      'try_catch': {
        retry_count: config.retry_count || 3,
      },
      'human_approval': {
        message: config.message || '승인이 필요합니다',
        timeout: config.timeout || 86400,
      },

      // ===== BLOCKS =====
      'text_block': { text: config.text || '' },
      'code_block': {
        code: config.code || '',
        language: config.language || 'python',
      },
      'http_block': {
        url: config.url || '',
        method: config.method || 'GET',
      },
      'database_block': { query: config.query || '' },
      'transform_block': { mapping: config.mapping || {} },
      'ai_block': {
        prompt: config.prompt || '',
        model: config.model || 'gpt-4o-mini',
      },
    };

    return baseConfig[backendType] || config;
  };

  // Handle AI-generated workflow application to canvas
  const handleApplyAIWorkflow = useCallback((graphDefinition: any, workflowName: string) => {
    console.log('🤖 [AI Workflow] Received graphDefinition:', JSON.stringify(graphDefinition, null, 2));
    console.log('🤖 [AI Workflow] Workflow name:', workflowName);
    logger.log('🤖 Applying AI-generated workflow:', { workflowName, graphDefinition });
    
    if (!graphDefinition?.nodes || !graphDefinition?.edges) {
      console.error('🤖 [AI Workflow] Invalid definition - missing nodes or edges');
      toast({
        title: 'Error',
        description: 'Invalid workflow definition',
      });
      return;
    }
    
    console.log('🤖 [AI Workflow] Nodes count:', graphDefinition.nodes.length);
    console.log('🤖 [AI Workflow] Edges count:', graphDefinition.edges.length);

    // Convert AI-generated nodes to ReactFlow format with proper positioning
    const convertedNodes: Node[] = graphDefinition.nodes.map((node: any, index: number) => {
      // Calculate position in a better flow layout
      const position = node.position || {
        x: 250,
        y: 100 + index * 150,
      };

      const backendType = node.type || 'tool';
      const frontendType = mapNodeType(backendType);
      const nodeLabel = node.label || node.data?.label || getNodeLabel(backendType);
      
      // Build proper configuration for this node type
      const nodeConfig = buildNodeConfig(backendType, node.config || node.data?.config || {});

      return {
        id: node.id || generateUUID(),
        type: frontendType,
        position,
        data: {
          label: nodeLabel,
          name: nodeLabel,
          description: node.data?.description || '',
          tool_id: backendType,
          tool_name: getNodeLabel(backendType),
          nodeType: backendType,
          blockType: frontendType,
          // Node-specific configuration
          ...nodeConfig,
          // Keep original config for reference
          parameters: nodeConfig,
          configuration: nodeConfig,
        },
      };
    });

    console.log('🤖 [AI Workflow] Converted nodes:', convertedNodes);

    // Convert AI-generated edges to ReactFlow format
    const convertedEdges: Edge[] = graphDefinition.edges.map((edge: any) => ({
      id: edge.id || generateUUID(),
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle || null,
      targetHandle: edge.targetHandle || null,
      type: 'custom',
    }));

    console.log('🤖 [AI Workflow] Converted edges:', convertedEdges);
    console.log('🤖 [AI Workflow] Setting nodes and edges to state...');

    // Update state
    setName(workflowName);
    setNodes(convertedNodes);
    setEdges(convertedEdges);
    setShowAIGenerator(false);
    
    console.log('🤖 [AI Workflow] State updated successfully');

    // Validate the generated workflow
    const result = validateWorkflow(convertedNodes, convertedEdges);
    setValidationErrors([...result.errors, ...result.warnings]);

    toast({
      title: '✨ AI Workflow Applied',
      description: `${convertedNodes.length} nodes and ${convertedEdges.length} edges added to canvas`,
    });
  }, [toast]);

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
    const validationResult = validateWorkflow(nodes, edges);
    const summary = getValidationSummary(validationResult);
    
    if (summary.hasErrors) {
      // Show detailed error messages
      const errorDetails = validationResult.errors
        .map(err => `• ${err.nodeName}${err.field ? ` (${err.field})` : ''}: ${err.message}`)
        .join('\n');
      
      console.error('❌ Validation errors:', validationResult.errors);
      
      toast({
        title: 'Validation Failed',
        description: `Please fix ${summary.errorCount} error(s) before saving:\n\n${errorDetails}`,
        variant: 'destructive',
      });
      return;
    }
    
    if (summary.hasWarnings) {
      const warningDetails = validationResult.warnings
        .map(warn => `• ${warn.nodeName}${warn.field ? ` (${warn.field})` : ''}: ${warn.message}`)
        .join('\n');
      
      const confirmed = confirm(
        `Workflow has ${summary.warningCount} warning(s):\n\n${warningDetails}\n\nDo you want to save anyway?`
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
      const entryPoint = startNode?.id || (convertedNodes.length > 0 ? convertedNodes[0]?.id || '' : '');

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
      // Log full error for debugging
      console.error('❌ Workflow creation error:', {
        message: error?.message,
        code: error?.code,
        status: error?.status,
        details: error?.details,
        stack: error?.stack,
        fullError: error,
      });
      
      // Extract detailed error message
      let errorMessage = 'Failed to create workflow';
      let errorDetails: string[] = [];
      
      if (error?.details?.detail) {
        // FastAPI validation error format
        if (typeof error.details.detail === 'string') {
          errorMessage = error.details.detail;
        } else if (Array.isArray(error.details.detail)) {
          // Pydantic validation errors
          errorMessage = 'Validation errors:';
          errorDetails = error.details.detail.map((e: any) => {
            const location = e.loc ? e.loc.join(' → ') : 'unknown';
            return `• ${location}: ${e.msg}`;
          });
        } else {
          errorMessage = JSON.stringify(error.details.detail, null, 2);
        }
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      // Combine error message and details
      const fullErrorMessage = errorDetails.length > 0 
        ? `${errorMessage}\n\n${errorDetails.join('\n')}`
        : errorMessage;
      
      toast({
        title: `Error${error?.status ? ` (${error.status})` : ''}`,
        description: fullErrorMessage,
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
          <div className="flex items-center gap-2">
            <Dialog open={showAIGenerator} onOpenChange={setShowAIGenerator}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-300 hover:border-purple-400">
                  <Sparkles className="mr-2 h-4 w-4 text-purple-500" />
                  AI Workflow Generator
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Wand2 className="h-5 w-5 text-purple-500" />
                    AI Workflow Generator
                  </DialogTitle>
                </DialogHeader>
                <NLPWorkflowGenerator
                  onApply={handleApplyAIWorkflow}
                  onGenerate={(workflow) => {
                    logger.log('AI workflow generated:', workflow);
                  }}
                />
              </DialogContent>
            </Dialog>
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
