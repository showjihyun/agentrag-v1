'use client';

import { useState, useCallback, useEffect } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Play,
  Square,
  Pause,
  RotateCcw,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Eye,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { NodeConfigurationPanel } from './NodeConfigurationPanel';

// Node execution status
type ExecutionStatus = 'idle' | 'running' | 'success' | 'error' | 'skipped';

interface NodeData {
  label: string;
  type: string;
  status?: ExecutionStatus;
  executionTime?: number;
  output?: any;
  error?: string;
}

// Custom Node Component with execution status
function CustomNode({ data, selected }: { data: NodeData; selected: boolean }) {
  const getStatusColor = (status?: ExecutionStatus) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950';
      case 'success':
        return 'border-green-500 bg-green-50 dark:bg-green-950';
      case 'error':
        return 'border-red-500 bg-red-50 dark:bg-red-950';
      case 'skipped':
        return 'border-gray-300 bg-gray-50 dark:bg-gray-900';
      default:
        return 'border-gray-300 bg-white dark:bg-gray-800';
    }
  };

  const getStatusIcon = (status?: ExecutionStatus) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />;
      case 'success':
        return <CheckCircle2 className="h-3 w-3 text-green-600" />;
      case 'error':
        return <XCircle className="h-3 w-3 text-red-600" />;
      case 'skipped':
        return <span className="h-3 w-3 text-gray-400">⊘</span>;
      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[150px] transition-all cursor-pointer',
        getStatusColor(data.status),
        selected && 'ring-2 ring-primary ring-offset-2'
      )}
      onClick={(e) => {
        console.log('🎯 CustomNode div clicked!', data);
        // Don't stop propagation - let it bubble up to ReactFlow
      }}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm">{data.label}</span>
        {getStatusIcon(data.status)}
      </div>
      <div className="text-xs text-muted-foreground">{data.type}</div>
      {data.executionTime !== undefined && (
        <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {data.executionTime}ms
        </div>
      )}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

interface ImprovedWorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
}

export function ImprovedWorkflowCanvas({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
}: ImprovedWorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [executionStats, setExecutionStats] = useState({
    total: 0,
    completed: 0,
    failed: 0,
    duration: 0,
  });

  // Notify parent of changes
  useEffect(() => {
    if (onNodesChange) onNodesChange(nodes);
  }, [nodes, onNodesChange]);

  useEffect(() => {
    if (onEdgesChange) onEdgesChange(edges);
  }, [edges, onEdgesChange]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    console.log('='.repeat(50));
    console.log('🖱️ NODE CLICKED!');
    console.log('Event:', event);
    console.log('Node ID:', node.id);
    console.log('Node Type:', node.type);
    console.log('Node Data:', node.data);
    console.log('Full Node:', node);
    console.log('='.repeat(50));
    setSelectedNode(node);
  }, []);

  // Simulate workflow execution
  const handleExecute = async () => {
    setIsExecuting(true);
    setExecutionProgress(0);
    
    const totalNodes = nodes.length;
    let completed = 0;
    let failed = 0;
    const startTime = Date.now();

    // Reset all nodes to idle
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined },
      }))
    );

    // Execute nodes sequentially (in production, follow actual workflow logic)
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      
      // Set node to running
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? { ...n, data: { ...n.data, status: 'running' } }
            : n
        )
      );

      // Simulate execution
      const executionTime = Math.random() * 1000 + 500;
      await new Promise((resolve) => setTimeout(resolve, executionTime));

      // Randomly succeed or fail (90% success rate)
      const success = Math.random() > 0.1;
      
      if (success) {
        completed++;
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? {
                  ...n,
                  data: {
                    ...n.data,
                    status: 'success',
                    executionTime: Math.round(executionTime),
                    output: { result: 'Success' },
                  },
                }
              : n
          )
        );
      } else {
        failed++;
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? {
                  ...n,
                  data: {
                    ...n.data,
                    status: 'error',
                    executionTime: Math.round(executionTime),
                    error: 'Execution failed',
                  },
                }
              : n
          )
        );
        // Stop execution on error
        break;
      }

      setExecutionProgress(((i + 1) / totalNodes) * 100);
    }

    const duration = Date.now() - startTime;
    setExecutionStats({ total: totalNodes, completed, failed, duration });
    setIsExecuting(false);
  };

  const handleStop = () => {
    setIsExecuting(false);
    // Set all running nodes to idle
    setNodes((nds) =>
      nds.map((node) =>
        node.data.status === 'running'
          ? { ...node, data: { ...node.data, status: 'idle' } }
          : node
      )
    );
  };

  const handleReset = () => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined, output: undefined, error: undefined },
      }))
    );
    setExecutionProgress(0);
    setExecutionStats({ total: 0, completed: 0, failed: 0, duration: 0 });
    setSelectedNode(null);
  };

  return (
    <div className="h-full flex">
      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChangeInternal}
          onEdgesChange={onEdgesChangeInternal}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          selectNodesOnDrag={false}
          className="bg-gray-50 dark:bg-gray-900"
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
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
            }}
          />
          
          {/* Execution Controls */}
          <Panel position="top-right">
            <Card className="w-64">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Execution
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Control Buttons */}
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
                    <Button
                      onClick={handleStop}
                      variant="destructive"
                      size="sm"
                    >
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

                {/* Progress */}
                {isExecuting && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Progress</span>
                      <span>{Math.round(executionProgress)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${executionProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Stats */}
                {executionStats.total > 0 && (
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                      <span>{executionStats.completed} completed</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <XCircle className="h-3 w-3 text-red-600" />
                      <span>{executionStats.failed} failed</span>
                    </div>
                    <div className="flex items-center gap-1 col-span-2">
                      <Clock className="h-3 w-3" />
                      <span>{executionStats.duration}ms total</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </Panel>
        </ReactFlow>
      </div>
      
      {/* Node Configuration Panel */}
      {selectedNode && (
        <NodeConfigurationPanel
          node={{
            id: selectedNode.id,
            type: selectedNode.type || 'custom',
            label: selectedNode.data.label,
            // Try multiple possible locations for tool_id
            tool_id: selectedNode.data.tool_id || selectedNode.data.type || selectedNode.data.toolId || 'http_request',
            config: selectedNode.data.config
          }}
          onClose={() => setSelectedNode(null)}
          onSave={(config) => {
            setNodes((nds) =>
              nds.map((node) =>
                node.id === selectedNode.id
                  ? { ...node, data: { ...node.data, config } }
                  : node
              )
            );
            setSelectedNode(null);
          }}
          onTest={async (config) => {
            // Test the tool with the configuration
            const response = await fetch('/api/agent-builder/tools/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tool_id: selectedNode.data.type,
                parameters: config
              })
            });
            
            if (!response.ok) {
              const error = await response.json();
              throw new Error(error.error || 'Test failed');
            }
            
            const result = await response.json();
            if (!result.success) {
              throw new Error(result.error || 'Test failed');
            }
            
            return result.result;
          }}
        />
      )}
    </div>
  );
}
