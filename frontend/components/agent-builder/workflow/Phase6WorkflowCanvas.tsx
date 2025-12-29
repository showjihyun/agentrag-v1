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
  const { isExecuting, execute, stop, reset, debugger: workflowDebugger } = useWorkflowExecution({
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
  const handleDelete = useCallback((nodeIds: string[]) => {
    setNodes((nds) => nds.filter((node) => !nodeIds.includes(node.id)));
    setEdges((eds) => eds.filter((edge) => 
      !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)
    ));
  }, [setNodes, setEdges]);

  // Workflow metrics
  const workflowMetrics = useMemo(() => calculateNodeMetrics(nodes), [nodes]);

  return (
    <div className="h-full flex flex-col">
      <WorkflowErrorBoundary>
        <KeyboardShortcuts
          onUndo={handleUndo}
          onRedo={handleRedo}
          onSave={handleSave}
          onExecute={execute}
          onStop={stop}
        />
        
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as WorkflowTabValue)} className="flex-1 flex flex-col">
          <div className="border-b px-4 py-2">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="canvas">Canvas</TabsTrigger>
              <TabsTrigger value="debug">
                <Bug className="w-4 h-4 mr-2" />
                Debug
              </TabsTrigger>
              <TabsTrigger value="performance">
                <Activity className="w-4 h-4 mr-2" />
                Performance
              </TabsTrigger>
              <TabsTrigger value="settings">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </TabsTrigger>
              <TabsTrigger value="ai">
                <Sparkles className="w-4 h-4 mr-2" />
                AI Assistant
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="canvas" className="flex-1 m-0">
            <div className="h-full relative">
              <ReactFlow
                nodes={filteredNodes}
                edges={edges}
                onNodesChange={handleNodesChange}
                onEdgesChange={handleEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                attributionPosition="bottom-left"
                className="bg-background"
              >
                <Background />
                <Controls />
                <MiniMap
                  nodeColor={getMinimapNodeColor}
                  className="bg-background border border-border"
                />
                
                <Panel position="top-left">
                  <WorkflowToolbar
                    isExecuting={isExecuting}
                    onExecute={execute}
                    onStop={stop}
                    onReset={reset}
                    onSave={handleSave}
                    isSaving={isSaving}
                    canUndo={history.canUndo}
                    canRedo={history.canRedo}
                    onUndo={handleUndo}
                    onRedo={handleRedo}
                    selectedNodes={selectedNodes}
                    onDelete={handleDelete}
                  />
                </Panel>

                <Panel position="top-right">
                  <Card className="w-64">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Workflow Metrics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between text-xs">
                        <span>Nodes:</span>
                        <span>{workflowMetrics.totalNodes}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span>Connections:</span>
                        <span>{workflowMetrics.totalEdges}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span>Complexity:</span>
                        <span>{workflowMetrics.complexity}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Panel>
              </ReactFlow>
            </div>
          </TabsContent>

          <TabsContent value="debug" className="flex-1 m-0">
            <DebugPanel
              debugger={workflowDebugger}
              nodes={nodes}
              edges={edges}
              onNodesChange={setNodes}
            />
          </TabsContent>

          <TabsContent value="performance" className="flex-1 m-0">
            <PerformanceProfiler
              debugger={workflowDebugger}
              nodes={nodes}
            />
          </TabsContent>

          <TabsContent value="settings" className="flex-1 m-0">
            <div className="p-4">
              <Card>
                <CardHeader>
                  <CardTitle>Workflow Settings</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">Settings panel coming soon...</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="ai" className="flex-1 m-0">
            <AIAssistantPanelImproved
              workflowId={workflowId}
              nodes={nodes}
              edges={edges}
              selectedNodes={selectedNodes}
              onNodesChange={setNodes}
              onEdgesChange={setEdges}
            />
          </TabsContent>
        </Tabs>
      </WorkflowErrorBoundary>
    </div>
  );
}

export function Phase6WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <Phase6WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}