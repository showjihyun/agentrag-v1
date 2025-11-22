'use client';

import { useState, useCallback, useMemo, memo, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, Square, RotateCcw, Bug, Activity, Settings, Sparkles } from 'lucide-react';
import { DebugPanel } from './DebugPanel';
import { PerformanceProfiler } from './PerformanceProfiler';
import { AIAssistantPanelImproved } from './AIAssistantPanelImproved';
import { WorkflowToolbar } from './WorkflowToolbar';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { EnhancedAgentNode } from '../workflow-nodes/EnhancedAgentNode';
import { EnhancedControlNode } from '../workflow-nodes/EnhancedControlNode';
import { EnhancedToolNode } from '../workflow-nodes/EnhancedToolNode';
import { AnimatedEdge } from './AnimatedEdge';
import { WorkflowErrorBoundary } from '@/components/ErrorBoundary';
import { useWorkflowExecution } from '@/hooks/useWorkflowExecution';
import { useWorkflowHistory } from '@/hooks/useWorkflowHistory';
import { calculateNodeMetrics, getMinimapNodeColor } from '@/utils/workflowHelpers';
import type { WorkflowCanvasProps, WorkflowTabValue } from '@/types/workflow';

// Memoized node types
const nodeTypes: NodeTypes = {
  agent: memo(EnhancedAgentNode),
  control: memo(EnhancedControlNode),
  tool: memo(EnhancedToolNode),
};

// Memoized edge types
const edgeTypes = {
  animated: memo(AnimatedEdge),
};

function Phase6WorkflowCanvasInner({
  workflowId = 'demo-workflow',
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
  onSave,
}: WorkflowCanvasProps) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [filteredNodes, setFilteredNodes] = useState(nodes);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<WorkflowTabValue>('canvas');

  // Custom hooks
  const history = useWorkflowHistory(50);
  const { isExecuting, execute, stop, reset, debugger } = useWorkflowExecution({
    nodes,
    setNodes,
    setEdges,
  });

  // Sync filtered nodes when nodes change
  useEffect(() => {
    setFilteredNodes(nodes);
  }, [nodes]);

  // Notify parent of node changes
  useEffect(() => {
    onNodesChange?.(nodes);
  }, [nodes, onNodesChange]);

  // Notify parent of edge changes
  useEffect(() => {
    onEdgesChange?.(edges);
  }, [edges, onEdgesChange]);

  // Selected nodes
  const selectedNodes = useMemo(() => nodes.filter(n => n.selected), [nodes]);

  // Handle node changes
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
    },
    [onNodesChangeInternal]
  );

  // Handle edge changes
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
    },
    [onEdgesChangeInternal]
  );

  // Handle connection
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, type: 'animated', animated: isExecuting }, eds));
    },
    [setEdges, isExecuting]
  );

  // Save workflow
  const handleSave = useCallback(async () => {
    if (!onSave) return;
    
    setIsSaving(true);
    try {
      await onSave();
    } finally {
      setIsSaving(false);
    }
  }, [onSave]);

  // Undo/Redo
  const handleUndo = useCallback(() => history.canUndo && history.undo(), [history]);
  const handleRedo = useCallback(() => history.canRedo && history.redo(), [history]);

  // Node operations
  const handleDelete = useCallback((