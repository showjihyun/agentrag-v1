'use client';

import { useState, useCallback, useMemo, memo } from 'react';
import {
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  NodeTypes,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { toast } from 'sonner';
import { DebugPanel } from './DebugPanel';
import { PerformanceProfiler } from './PerformanceProfiler';
import { AIAssistantPanel } from './AIAssistantPanel';
import { WorkflowToolbar } from './WorkflowToolbar';
import { WorkflowTabs, WorkflowTabValue } from './WorkflowTabs';
import { CanvasContent } from './CanvasContent';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { EnhancedAgentNode } from '../workflow-nodes/EnhancedAgentNode';
import { EnhancedControlNode } from '../workflow-nodes/EnhancedControlNode';
import { EnhancedToolNode } from '../workflow-nodes/EnhancedToolNode';
import { AnimatedEdge } from './AnimatedEdge';
import { useDebounce } from '@/hooks/useDebounce';
import { useWorkflowHistory } from '@/hooks/useWorkflowHistory';
import { useWorkflowDebugger } from '@/hooks/useWorkflowDebugger';
import { useWorkflowExecution } from '@/hooks/useWorkflowExecution';
import { ErrorBoundary } from '@/components/ErrorBoundary';

const nodeTypes: NodeTypes = {
  agent: memo(EnhancedAgentNode),
  control: memo(EnhancedControlNode),
  tool: memo(EnhancedToolNode),
};

const edgeTypes = {
  animated: memo(AnimatedEdge),
};

interface RefactoredPhase5CanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: () => Promise<void>;
}

function RefactoredPhase5CanvasInner({
  workflowId = 'demo-workflow',
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
  onSave,
}: RefactoredPhase5CanvasProps) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [filteredNodes, setFilteredNodes] = useState<Node[]>(nodes);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<WorkflowTabValue>('canvas');

  // History management
  const history = useWorkflowHistory(50);

  // Debugger
  const debugger = useWorkflowDebugger();

  // Workflow execution
  const { isExecuting, execute, stop, reset } = useWorkflowExecution(
    nodes,
    setNodes,
    setEdges,
    debugger
  );

  // Debounce node changes
  const debouncedNodes = useDebounce(nodes, 100);

  // Get selected nodes
  const selectedNodes = useMemo(() => {
    return nodes.filter((node) => node.selected);
  }, [nodes]);

  // Handle node changes with external callback
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
    },
    [onNodesChangeInternal]
  );

  // Notify external listeners when nodes change
  useMemo(() => {
    onNodesChange?.(nodes);
  }, [nodes, onNodesChange]);

  // Handle edge changes
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
    },
    [onEdgesChangeInternal]
  );

  // Notify external listeners when edges change
  useMemo(() => {
    onEdgesChange?.(edges);
  }, [edges, onEdgesChange]);

  // Handle connection
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge({ ...connection, type: 'animated' }, eds));
      history.push({ nodes, edges });
    },
    [setEdges, nodes, edges, history]
  );

  // Save workflow
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      if (onSave) {
        await onSave();
      }
      toast.success('Workflow saved successfully');
    } catch (error) {
      toast.error('Failed to save workflow');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  }, [onSave]);

  // Undo/Redo
  const handleUndo = useCallback(() => {
    const state = history.undo();
    if (state) {
      setNodes(state.nodes);
      setEdges(state.edges);
      toast.success('Undo successful');
    }
  }, [history, setNodes, setEdges]);

  const handleRedo = useCallback(() => {
    const state = history.redo();
    if (state) {
      setNodes(state.nodes);
      setEdges(state.edges);
      toast.success('Redo successful');
    }
  }, [history, setNodes, setEdges]);

  // Search results handler
  const handleSearchResults = useCallback((results: Node[]) => {
    setFilteredNodes(results);
    
    // Highlight search results
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        selected: results.some((r) => r.id === node.id),
      }))
    );

    // Fit view to results
    if (results.length > 0 && reactFlowInstance) {
      reactFlowInstance.fitView({
        nodes: results,
        padding: 0.2,
        duration: 300,
      });
    }
  }, [setNodes, reactFlowInstance]);

  return (
    <div className="h-full flex flex-col">
      <WorkflowToolbar
        onSave={handleSave}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onExecute={execute}
        onStop={stop}
        onReset={reset}
        canUndo={history.canUndo()}
        canRedo={history.canRedo()}
        isSaving={isSaving}
        isExecuting={isExecuting}
      />

      <WorkflowTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        canvasContent={
          <CanvasContent
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            onSearchResults={handleSearchResults}
          />
        }
        debugContent={
          <DebugPanel
            debugger={debugger}
            nodes={nodes}
            edges={edges}
            onNodesChange={setNodes}
          />
        }
        performanceContent={
          <PerformanceProfiler
            debugger={debugger}
            nodes={nodes}
          />
        }
        aiContent={
          <AIAssistantPanel
            workflowId={workflowId}
            nodes={nodes}
            edges={edges}
            selectedNodes={selectedNodes}
            onApplySuggestion={(suggestion) => {
              toast.success('Suggestion applied');
            }}
          />
        }
      />

      <KeyboardShortcuts
        onSave={handleSave}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onExecute={execute}
        onStop={stop}
      />
    </div>
  );
}

export function RefactoredPhase5Canvas(props: RefactoredPhase5CanvasProps) {
  return (
    <ErrorBoundary>
      <ReactFlowProvider>
        <RefactoredPhase5CanvasInner {...props} />
      </ReactFlowProvider>
    </ErrorBoundary>
  );
}
