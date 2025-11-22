'use client';

import { useState, useCallback, useMemo, memo, useRef } from 'react';
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
import {
  Play,
  Square,
  RotateCcw,
  Zap,
  List,
  Save,
  Undo2,
  Redo2,
  Copy,
  Clipboard,
  ZoomIn,
  ZoomOut,
  Maximize,
  Keyboard,
} from 'lucide-react';
import { toast } from 'sonner';
import { InlineNodeEditor } from './InlineNodeEditor';
import { WorkflowSearchBar } from './WorkflowSearchBar';
import { VirtualizedNodeList } from './VirtualizedNodeList';
import { NodeContextMenu } from './NodeContextMenu';
import { SimplifiedPropertiesPanel } from './SimplifiedPropertiesPanel';
import { ExecutionTimeline } from './ExecutionTimeline';
import { AnimatedEdge } from './AnimatedEdge';
import { EnhancedAgentNode } from '../workflow-nodes/EnhancedAgentNode';
import { EnhancedControlNode } from '../workflow-nodes/EnhancedControlNode';
import { EnhancedToolNode } from '../workflow-nodes/EnhancedToolNode';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { useDebounce } from '@/hooks/useDebounce';
import { useWorkflowHistory } from '@/hooks/useWorkflowHistory';
import { useClipboard } from '@/hooks/useClipboard';

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

interface Phase2WorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: () => Promise<void>;
}

function Phase2WorkflowCanvasInner({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
  onSave,
}: Phase2WorkflowCanvasProps) {
  const reactFlowInstance = useReactFlow();
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
  const [executionLogs, setExecutionLogs] = useState<Array<{
    timestamp: Date;
    nodeId: string;
    message: string;
    level: 'info' | 'success' | 'error';
  }>>([]);
  const [showNodeList, setShowNodeList] = useState(false);
  const [filteredNodes, setFilteredNodes] = useState<Node[]>(nodes);
  const [isSaving, setIsSaving] = useState(false);

  // History management
  const history = useWorkflowHistory(50);
  const historyTimeoutRef = useRef<NodeJS.Timeout>();

  // Clipboard management
  const clipboard = useClipboard();

  // Debounce node changes to reduce re-renders
  const debouncedNodes = useDebounce(nodes, 100);

  // Get selected nodes
  const selectedNodes = useMemo(() => {
    return nodes.filter((node) => node.selected);
  }, [nodes]);

  // Push to history with debounce
  const pushToHistory = useCallback(() => {
    if (historyTimeoutRef.current) {
      clearTimeout(historyTimeoutRef.current);
    }
    historyTimeoutRef.current = setTimeout(() => {
      history.pushState(nodes, edges);
    }, 500);
  }, [nodes, edges, history]);

  // Memoize node change handler
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
      onNodesChange?.(nodes);
      pushToHistory();
    },
    [onNodesChangeInternal, onNodesChange, nodes, pushToHistory]
  );

  // Memoize edge change handler
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
      onEdgesChange?.(edges);
      pushToHistory();
    },
    [onEdgesChangeInternal, onEdgesChange, edges, pushToHistory]
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
      pushToHistory();
    },
    [setEdges, isExecuting, pushToHistory]
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
        pushToHistory();
        setEditingNode(null);
      }
    },
    [editingNode, setNodes, pushToHistory]
  );

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
      // Apply history state (would need to implement state restoration)
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
    pushToHistory();
  }, [selectedNodes, setNodes, setEdges, pushToHistory]);

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
    pushToHistory();
  }, [selectedNodes, setNodes, pushToHistory]);

  // Select all nodes
  const handleSelectAll = useCallback(() => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: true })));
  }, [setNodes]);

  // Copy nodes
  const handleCopy = useCallback(() => {
    clipboard.copy(selectedNodes);
  }, [clipboard, selectedNodes]);

  // Paste nodes
  const handlePaste = useCallback(() => {
    const pastedNodes = clipboard.paste();
    if (pastedNodes.length > 0) {
      setNodes((nds) => [...nds.map((n) => ({ ...n, selected: false })), ...pastedNodes]);
      pushToHistory();
      toast.success(`Pasted ${pastedNodes.length} node(s)`);
    }
  }, [clipboard, setNodes, pushToHistory]);

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

  // Execute workflow
  const handleExecute = useCallback(async () => {
    setIsExecuting(true);
    setExecutionLogs([]);

    // Reset all nodes
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined },
      }))
    );

    // Animate edges
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: true })));

    // Execute nodes sequentially
    for (const node of nodes) {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
        )
      );

      setExecutionLogs((logs) => [
        ...logs,
        {
          timestamp: new Date(),
          nodeId: node.id,
          message: `Executing ${node.data.label}`,
          level: 'info',
        },
      ]);

      const executionTime = Math.random() * 1000 + 500;
      await new Promise((resolve) => setTimeout(resolve, executionTime));

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

      setExecutionLogs((logs) => [
        ...logs,
        {
          timestamp: new Date(),
          nodeId: node.id,
          message: success
            ? `Completed ${node.data.label} in ${Math.round(executionTime)}ms`
            : `Failed ${node.data.label}`,
          level: success ? 'success' : 'error',
        },
      ]);

      if (!success) break;
    }

    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
    setIsExecuting(false);
  }, [nodes, setNodes, setEdges]);

  // Stop execution
  const handleStop = useCallback(() => {
    setIsExecuting(false);
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
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
    setExecutionLogs([]);
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
        onCopy={handleCopy}
        onPaste={handlePaste}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitView={handleFitView}
      />

      <div className="h-full flex flex-col">
        {/* Toolbar */}
        <div className="p-4 border-b bg-background flex items-center gap-2">
          <WorkflowSearchBar
            nodes={nodes}
            onFilteredNodesChange={setFilteredNodes}
          />
          
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
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={selectedNodes.length === 0}
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePaste}
              disabled={clipboard.copiedNodes.length === 0}
            >
              <Clipboard className="h-4 w-4" />
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </div>
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

              {/* View Controls */}
              <Panel position="top-left">
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowNodeList(!showNodeList)}
                  >
                    <List className="h-4 w-4 mr-2" />
                    {showNodeList ? 'Hide' : 'Show'} List
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleZoomIn}>
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleZoomOut}>
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleFitView}>
                    <Maximize className="h-4 w-4" />
                  </Button>
                </div>
              </Panel>

              {/* Keyboard Shortcuts Hint */}
              <Panel position="bottom-left">
                <div className="text-xs text-muted-foreground bg-background/80 backdrop-blur px-2 py-1 rounded border">
                  Press <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">?</kbd> for shortcuts
                </div>
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
                    {filteredNodes.length} of {nodes.length} nodes
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
          {executionLogs.length > 0 && (
            <div className="absolute bottom-4 left-4 right-4 z-10">
              <ExecutionTimeline logs={executionLogs} />
            </div>
          )}

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
                pushToHistory();
              }}
              onDuplicate={() => {
                const newNode = {
                  ...contextMenu.node,
                  id: `${contextMenu.node.id}-copy-${Date.now()}`,
                  position: {
                    x: contextMenu.node.position.x + 50,
                    y: contextMenu.node.position.y + 50,
                  },
                };
                setNodes((nds) => [...nds, newNode]);
                setContextMenu(null);
                pushToHistory();
              }}
            />
          )}

          {/* Properties Panel */}
          {selectedNode && (
            <SimplifiedPropertiesPanel
              node={selectedNode}
              isOpen={true}
              onClose={() => setSelectedNode(null)}
              onUpdate={(nodeId, updates) => {
                // Check if this is a delete operation
                if ((updates as any)._delete) {
                  setNodes((nds) => nds.filter((n) => n.id !== nodeId));
                  setEdges((eds) =>
                    eds.filter((e) => e.source !== nodeId && e.target !== nodeId)
                  );
                  setSelectedNode(null);
                  pushToHistory();
                  return;
                }
                
                setNodes((nds) =>
                  nds.map((n) =>
                    n.id === nodeId
                      ? { ...n, data: { ...n.data, ...updates } }
                      : n
                  )
                );
                pushToHistory();
              }}
            />
          )}
        </div>
      </div>
    </>
  );
}

export function Phase2WorkflowCanvas(props: Phase2WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <Phase2WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
