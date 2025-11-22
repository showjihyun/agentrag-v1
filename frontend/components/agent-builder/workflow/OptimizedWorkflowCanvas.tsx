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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Play, Square, RotateCcw, Zap, Settings2, List } from 'lucide-react';
import { InlineNodeEditor } from './InlineNodeEditor';
import { WorkflowSearchBar } from './WorkflowSearchBar';
import { VirtualizedNodeList } from './VirtualizedNodeList';
import { NodeContextMenu } from './NodeContextMenu';
import { SimplifiedPropertiesPanel } from './SimplifiedPropertiesPanel';
import { AnimatedEdge } from './AnimatedEdge';
import { EnhancedAgentNode } from '../workflow-nodes/EnhancedAgentNode';
import { EnhancedControlNode } from '../workflow-nodes/EnhancedControlNode';
import { EnhancedToolNode } from '../workflow-nodes/EnhancedToolNode';
import { useDebounce } from '@/hooks/useDebounce';

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

interface OptimizedWorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
}

function OptimizedWorkflowCanvasInner({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
}: OptimizedWorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [editingNode, setEditingNode] = useState<{
    node: Node;
    position: { x: number; y: number };
  } | null>(null);
  const [contextMenu, setContextMenu] = useState<{
    node: Node;
    position: { x: number; y: number };
  } | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showNodeList, setShowNodeList] = useState(false);
  const [filteredNodes, setFilteredNodes] = useState<Node[]>(nodes);

  // Debounce node changes to reduce re-renders
  const debouncedNodes = useDebounce(nodes, 100);

  // Memoize node change handler
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
      onNodesChange?.(nodes);
    },
    [onNodesChangeInternal, onNodesChange, nodes]
  );

  // Memoize edge change handler
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
      onEdgesChange?.(edges);
    },
    [onEdgesChangeInternal, onEdgesChange, edges]
  );

  // Memoize connection handler
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

  // Handle node click
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    event.stopPropagation();
    setSelectedNode(node);
    setContextMenu(null);
  }, []);

  // Handle node double-click for inline editing
  const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
    event.stopPropagation();
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setEditingNode({
      node,
      position: { x: rect.left, y: rect.top },
    });
  }, []);

  // Handle node context menu
  const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    event.stopPropagation();
    setContextMenu({
      node,
      position: { x: event.clientX, y: event.clientY },
    });
  }, []);

  // Handle inline edit save
  const handleInlineEditSave = useCallback(
    (label: string, description?: string) => {
      if (editingNode) {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === editingNode.node.id
              ? { ...n, data: { ...n.data, label, description } }
              : n
          )
        );
        setEditingNode(null);
      }
    },
    [editingNode, setNodes]
  );

  // Execute workflow
  const handleExecute = useCallback(async () => {
    setIsExecuting(true);

    // Reset all nodes
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined },
      }))
    );

    // Animate edges
    setEdges((eds) =>
      eds.map((edge) => ({ ...edge, animated: true }))
    );

    // Execute nodes sequentially
    for (const node of nodes) {
      // Set running
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
        )
      );

      // Simulate execution
      const executionTime = Math.random() * 1000 + 500;
      await new Promise((resolve) => setTimeout(resolve, executionTime));

      // Random success/failure
      const success = Math.random() > 0.1;

      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? {
                ...n,
                data: {
                  ...n.data,
                  status: success ? 'success' : 'error',
                  executionTime: Math.round(executionTime),
                },
              }
            : n
        )
      );

      if (!success) break;
    }

    // Stop edge animation
    setEdges((eds) =>
      eds.map((edge) => ({ ...edge, animated: false }))
    );

    setIsExecuting(false);
  }, [nodes, setNodes, setEdges]);

  // Stop execution
  const handleStop = useCallback(() => {
    setIsExecuting(false);
    setEdges((eds) =>
      eds.map((edge) => ({ ...edge, animated: false }))
    );
  }, [setEdges]);

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
  }, [setNodes]);

  // Memoize minimap node color
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
    <div className="h-full flex flex-col">
      {/* Search Bar */}
      <div className="p-4 border-b bg-background">
        <WorkflowSearchBar
          nodes={nodes}
          onFilteredNodesChange={setFilteredNodes}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={filteredNodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeContextMenu={onNodeContextMenu}
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
                    <Zap className="h-4 w-4" />
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

            {/* Node List Toggle */}
            <Panel position="top-left">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowNodeList(!showNodeList)}
              >
                <List className="h-4 w-4 mr-2" />
                {showNodeList ? 'Hide' : 'Show'} List
              </Button>
            </Panel>
          </ReactFlow>
        </div>

        {/* Node List Sidebar */}
        {showNodeList && (
          <div className="w-80 border-l bg-background">
            <div className="h-full flex flex-col">
              <div className="p-4 border-b">
                <h3 className="font-semibold text-sm">Nodes</h3>
                <p className="text-xs text-muted-foreground">
                  {filteredNodes.length} nodes
                </p>
              </div>
              <VirtualizedNodeList
                nodes={filteredNodes}
                onNodeClick={(node) => setSelectedNode(node)}
                selectedNodeId={selectedNode?.id}
              />
            </div>
          </div>
        )}

        {/* Execution Timeline */}


        {/* Inline Editor */}
        {editingNode && (
          <InlineNodeEditor
            nodeId={editingNode.node.id}
            initialLabel={editingNode.node.data.label}
            initialDescription={editingNode.node.data.description}
            position={editingNode.position}
            onSave={handleInlineEditSave}
            onCancel={() => setEditingNode(null)}
          />
        )}

        {/* Context Menu */}
        {contextMenu && (
          <NodeContextMenu
            node={contextMenu.node}
            position={contextMenu.position}
            onClose={() => setContextMenu(null)}
            onEdit={() => {
              setEditingNode({
                node: contextMenu.node,
                position: contextMenu.position,
              });
              setContextMenu(null);
            }}
            onDelete={() => {
              setNodes((nds) => nds.filter((n) => n.id !== contextMenu.node.id));
              setContextMenu(null);
            }}
            onDuplicate={() => {
              const newNode = {
                ...contextMenu.node,
                id: `${contextMenu.node.id}-copy`,
                position: {
                  x: contextMenu.node.position.x + 50,
                  y: contextMenu.node.position.y + 50,
                },
              };
              setNodes((nds) => [...nds, newNode]);
              setContextMenu(null);
            }}
          />
        )}

        {/* Properties Panel */}
        {selectedNode && (
          <SimplifiedPropertiesPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onChange={(updates) => {
              setNodes((nds) =>
                nds.map((n) =>
                  n.id === selectedNode.id
                    ? { ...n, data: { ...n.data, ...updates } }
                    : n
                )
              );
            }}
          />
        )}
      </div>
    </div>
  );
}

export function OptimizedWorkflowCanvas(props: OptimizedWorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <OptimizedWorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
