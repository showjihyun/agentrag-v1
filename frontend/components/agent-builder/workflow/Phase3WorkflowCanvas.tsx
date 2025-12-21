'use client';

import { useState, useCallback, useMemo, memo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
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
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Play,
  Square,
  RotateCcw,
  Bug,
  Activity,
  Save,
  Undo2,
  Redo2,
  Settings,
} from 'lucide-react';
import { toast } from 'sonner';
import { DebugPanel } from './DebugPanel';
import { PerformanceProfiler } from './PerformanceProfiler';
import { WorkflowSearchBar } from './WorkflowSearchBar';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { EnhancedAgentNode } from '../workflow-nodes/EnhancedAgentNode';
import { EnhancedControlNode } from '../workflow-nodes/EnhancedControlNode';
import { AnimatedEdge } from './AnimatedEdge';
import { useDebounce } from '@/hooks/useDebounce';
import { useWorkflowHistory } from '@/hooks/useWorkflowHistory';
import { useWorkflowDebugger } from '@/hooks/useWorkflowDebugger';

const nodeTypes: NodeTypes = {
  agent: memo(EnhancedAgentNode),
  control: memo(EnhancedControlNode),
};

const edgeTypes = {
  animated: memo(AnimatedEdge),
};

interface Phase3WorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: () => Promise<void>;
}

function Phase3WorkflowCanvasInner({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
  onSave,
}: Phase3WorkflowCanvasProps) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [isExecuting, setIsExecuting] = useState(false);
  const [filteredNodes, setFilteredNodes] = useState<Node[]>(nodes);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'canvas' | 'debug' | 'performance'>('canvas');

  // History management
  const history = useWorkflowHistory(50);

  // Debugger
  const workflowDebugger = useWorkflowDebugger();

  // Debounce node changes
  const debouncedNodes = useDebounce(nodes, 100);

  // Get selected nodes
  const selectedNodes = useMemo(() => {
    return nodes.filter((node) => node.selected);
  }, [nodes]);

  // Handle node changes
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
      onNodesChange?.(nodes);
    },
    [onNodesChangeInternal, onNodesChange, nodes]
  );

  // Handle edge changes
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
      onEdgesChange?.(edges);
    },
    [onEdgesChangeInternal, onEdgesChange, edges]
  );

  // Handle connection
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        type: 'animated',
        animated: isExecuting,
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges, isExecuting]
  );

  // Execute workflow with debugging
  const handleExecute = useCallback(async () => {
    setIsExecuting(true);
    workflowDebugger.startDebugging();

    // Reset all nodes
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined },
      }))
    );

    // Animate edges
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: true })));

    try {
      // Execute nodes sequentially with debugging
      for (const node of nodes) {
        // Update node status to running
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
          )
        );

        // Execute with debugger
        await workflowDebugger.executeNodeWithDebug(node.id, async () => {
          // Simulate execution
          const executionTime = Math.random() * 1000 + 500;
          await new Promise((resolve) => setTimeout(resolve, executionTime));

          // Random success/failure
          const success = Math.random() > 0.1;
          if (!success) {
            throw new Error(`Node ${node.data.label} failed`);
          }

          return {
            result: `Output from ${node.data.label}`,
            executionTime: Math.round(executionTime),
          };
        });

        // Update node status
        const currentState = workflowDebugger.getCurrentState();
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? {
                  ...n,
                  data: {
                    ...n.data,
                    status: currentState?.status === 'error' ? 'error' : 'success',
                    executionTime: currentState?.duration,
                  },
                }
              : n
          )
        );

        // Break on error
        if (currentState?.status === 'error') {
          break;
        }
      }

      toast.success('Workflow execution completed');
    } catch (error: any) {
      toast.error(`Execution failed: ${error.message}`);
    } finally {
      setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
      setIsExecuting(false);
      workflowDebugger.stopDebugging();
    }
  }, [nodes, setNodes, setEdges, workflowDebugger]);

  // Stop execution
  const handleStop = useCallback(() => {
    setIsExecuting(false);
    workflowDebugger.stopDebugging();
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
  }, [setEdges, workflowDebugger]);

  // Reset workflow
  const handleReset = useCallback(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          status: 'idle',
          executionTime: undefined,
        },
      }))
    );
    workflowDebugger.restart();
  }, [setNodes, workflowDebugger]);

  // Save workflow
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await onSave?.();
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
    if (history.canUndo) {
      history.undo();
      toast.info('Undo');
    }
  }, [history]);

  const handleRedo = useCallback(() => {
    if (history.canRedo) {
      history.redo();
      toast.info('Redo');
    }
  }, [history]);

  // Delete selected nodes
  const handleDelete = useCallback(() => {
    const selectedIds = selectedNodes.map((n) => n.id);
    setNodes((nds) => nds.filter((n) => !selectedIds.includes(n.id)));
    setEdges((eds) =>
      eds.filter((e) => !selectedIds.includes(e.source) && !selectedIds.includes(e.target))
    );
  }, [selectedNodes, setNodes, setEdges]);

  // Duplicate selected nodes
  const handleDuplicate = useCallback(() => {
    const newNodes = selectedNodes.map((node) => ({
      ...node,
      id: `${node.id}-copy-${Date.now()}`,
      position: {
        x: node.position.x + 50,
        y: node.position.y + 50,
      },
      selected: true,
    }));
    setNodes((nds) => [...nds.map((n) => ({ ...n, selected: false })), ...newNodes]);
  }, [selectedNodes, setNodes]);

  // Select all nodes
  const handleSelectAll = useCallback(() => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: true })));
  }, [setNodes]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    reactFlowInstance.zoomIn();
  }, [reactFlowInstance]);

  const handleZoomOut = useCallback(() => {
    reactFlowInstance.zoomOut();
  }, [reactFlowInstance]);

  const handleFitView = useCallback(() => {
    reactFlowInstance.fitView({ padding: 0.2 });
  }, [reactFlowInstance]);

  // Get performance metrics
  const performanceMetrics = useMemo(() => {
    const metrics = workflowDebugger.getPerformanceMetrics();
    
    // Transform to component format
    const nodeMetrics: Record<string, any> = {};
    Object.entries(metrics.nodeMetrics).forEach(([nodeId, metric]) => {
      const node = nodes.find(n => n.id === nodeId);
      nodeMetrics[nodeId] = {
        ...metric,
        nodeId,
        nodeName: node?.data.label || nodeId,
        errorRate: 100 - metric.successRate,
      };
    });

    return {
      ...metrics,
      nodeMetrics,
    };
  }, [workflowDebugger, nodes]);

  // Minimap node color
  const minimapNodeColor = useCallback((node: Node) => {
    switch (node.data.status) {
      case 'running':
        return '#3b82f6';
      case 'success':
        return '#10b981';
      case 'error':
        return '#ef4444';
      default:
        return '#d1d5db';
    }
  }, []);

  return (
    <>
      <KeyboardShortcuts
        nodes={nodes}
        edges={edges}
        selectedNodes={selectedNodes}
        onSave={handleSave}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onDelete={handleDelete}
        onDuplicate={handleDuplicate}
        onSelectAll={handleSelectAll}
        onCopy={() => {}}
        onPaste={() => {}}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitView={handleFitView}
      />

      <div className="h-full flex flex-col">
        {/* Toolbar */}
        <div className="p-4 border-b bg-background flex items-center gap-2">
          <WorkflowSearchBar nodes={nodes} onFilteredNodesChange={setFilteredNodes} />

          <div className="flex items-center gap-2 ml-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={handleUndo}
              disabled={!history.canUndo}
            >
              <Undo2 className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRedo}
              disabled={!history.canRedo}
            >
              <Redo2 className="h-4 w-4" />
            </Button>
            <Button variant="default" size="sm" onClick={handleSave} disabled={isSaving}>
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Canvas Area */}
          <div className="flex-1 flex flex-col">
            <Tabs value={activeTab} onValueChange={(v: any) => setActiveTab(v)} className="flex-1 flex flex-col">
              <div className="border-b px-4">
                <TabsList>
                  <TabsTrigger value="canvas">
                    <Settings className="h-4 w-4 mr-2" />
                    Canvas
                  </TabsTrigger>
                  <TabsTrigger value="debug">
                    <Bug className="h-4 w-4 mr-2" />
                    Debug
                  </TabsTrigger>
                  <TabsTrigger value="performance">
                    <Activity className="h-4 w-4 mr-2" />
                    Performance
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="canvas" className="flex-1 m-0">
                <ReactFlow
                  nodes={filteredNodes}
                  edges={edges}
                  onNodesChange={handleNodesChange}
                  onEdgesChange={handleEdgesChange}
                  onConnect={onConnect}
                  nodeTypes={nodeTypes}
                  edgeTypes={edgeTypes}
                  fitView
                  nodesDraggable={!isExecuting}
                  nodesConnectable={!isExecuting}
                  elementsSelectable={!isExecuting}
                  className="bg-gray-50 dark:bg-gray-900"
                >
                  <Background />
                  <Controls />
                  <MiniMap nodeColor={minimapNodeColor} />

                  {/* Execution Controls */}
                  <Panel position="top-right">
                    <Card className="w-64">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Activity className="h-4 w-4" />
                          Execution
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex gap-2">
                          <Button
                            onClick={handleExecute}
                            disabled={isExecuting}
                            size="sm"
                            className="flex-1"
                          >
                            <Play className="h-3 w-3 mr-1" />
                            Execute
                          </Button>
                          {isExecuting && (
                            <Button onClick={handleStop} variant="destructive" size="sm">
                              <Square className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            onClick={handleReset}
                            variant="outline"
                            size="sm"
                            disabled={isExecuting}
                          >
                            <RotateCcw className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </Panel>
                </ReactFlow>
              </TabsContent>

              <TabsContent value="debug" className="flex-1 m-0 p-4">
                <DebugPanel
                  nodes={nodes}
                  currentNodeId={workflowDebugger.currentNodeId}
                  executionHistory={workflowDebugger.executionHistory}
                  breakpoints={workflowDebugger.breakpoints}
                  onBreakpointToggle={workflowDebugger.toggleBreakpoint}
                  onStepOver={workflowDebugger.stepOver}
                  onStepInto={workflowDebugger.stepInto}
                  onContinue={workflowDebugger.continueExecution}
                  onRestart={workflowDebugger.restart}
                  onTimeTravel={workflowDebugger.timeTravel}
                />
              </TabsContent>

              <TabsContent value="performance" className="flex-1 m-0 p-4 overflow-auto">
                <PerformanceProfiler
                  nodes={nodes}
                  nodeMetrics={performanceMetrics.nodeMetrics}
                  totalDuration={performanceMetrics.totalDuration}
                  avgDuration={performanceMetrics.avgDuration}
                  successRate={performanceMetrics.successRate}
                  errorRate={performanceMetrics.errorRate}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </>
  );
}

export function Phase3WorkflowCanvas(props: Phase3WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <Phase3WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
