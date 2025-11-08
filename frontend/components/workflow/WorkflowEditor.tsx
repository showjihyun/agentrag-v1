'use client';

import React, { useCallback, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  BackgroundVariant,
  NodeTypes,
  EdgeTypes,
  ReactFlowProvider,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { BlockNode } from './nodes/BlockNode';
import { AgentNode } from './nodes/AgentNode';
import { StartNode } from './nodes/StartNode';
import { EndNode } from './nodes/EndNode';
import { ConditionNode } from './nodes/ConditionNode';
import { TriggerNode } from './nodes/TriggerNode';
import { CustomEdge } from './edges/CustomEdge';
import { NodeConfigPanel } from './NodeConfigPanel';
import { Button } from '@/components/ui/button';
import { Undo, Redo, ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { useUndoRedo } from '@/hooks/useUndoRedo';

interface WorkflowEditorProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: (nodes: Node[], edges: Edge[]) => void;
  readOnly?: boolean;
}

const nodeTypes: NodeTypes = {
  block: BlockNode,
  agent: AgentNode,
  start: StartNode,
  end: EndNode,
  condition: ConditionNode,
  trigger: TriggerNode,
};

const edgeTypes: EdgeTypes = {
  custom: CustomEdge,
};

function WorkflowEditorInner({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
  onSave,
  readOnly = false,
}: WorkflowEditorProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Undo/Redo functionality
  const {
    state: historyState,
    set: setHistoryState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset: resetHistory,
  } = useUndoRedo<{ nodes: Node[]; edges: Edge[] }>({
    nodes: initialNodes,
    edges: initialEdges,
  });

  // Sync history state with nodes and edges
  useEffect(() => {
    if (!readOnly) {
      setHistoryState({ nodes, edges });
    }
  }, [nodes, edges, readOnly]);

  // Apply undo/redo
  const handleUndo = useCallback(() => {
    undo();
    const prevState = historyState;
    setNodes(prevState.nodes);
    setEdges(prevState.edges);
  }, [undo, historyState, setNodes, setEdges]);

  const handleRedo = useCallback(() => {
    redo();
    const nextState = historyState;
    setNodes(nextState.nodes);
    setEdges(nextState.edges);
  }, [redo, historyState, setNodes, setEdges]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (readOnly) return;

      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [readOnly, handleUndo, handleRedo]);

  // Handle node changes
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChange(changes);
      if (onNodesChangeProp) {
        // Get updated nodes after changes
        const updatedNodes = nodes; // ReactFlow will update this
        onNodesChangeProp(updatedNodes);
      }
    },
    [onNodesChange, onNodesChangeProp, nodes]
  );

  // Handle edge changes
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChange(changes);
      if (onEdgesChangeProp) {
        const updatedEdges = edges;
        onEdgesChangeProp(updatedEdges);
      }
    },
    [onEdgesChange, onEdgesChangeProp, edges]
  );

  // Handle new connections
  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly) return;
      
      const newEdge = {
        ...connection,
        type: 'custom',
        id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
      };
      
      setEdges((eds) => addEdge(newEdge, eds));
      
      if (onEdgesChangeProp) {
        onEdgesChangeProp([...edges, newEdge as Edge]);
      }
    },
    [readOnly, setEdges, edges, onEdgesChangeProp]
  );

  // Handle drag over for drop support
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop from palette
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const blockData = event.dataTransfer.getData('application/reactflow');

      if (!blockData) return;

      const block = JSON.parse(blockData);
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      // Determine node type based on block data
      let nodeType = 'block';
      if (block.nodeType === 'agent') nodeType = 'agent';
      else if (block.nodeType === 'start') nodeType = 'start';
      else if (block.nodeType === 'end') nodeType = 'end';
      else if (block.nodeType === 'condition') nodeType = 'condition';
      else if (block.nodeType === 'trigger') nodeType = 'trigger';

      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: nodeType,
        position,
        data: {
          ...block,
          label: block.name,
        },
      };

      setNodes((nds) => nds.concat(newNode));
      
      if (onNodesChangeProp) {
        onNodesChangeProp([...nodes, newNode]);
      }
    },
    [reactFlowInstance, nodes, setNodes, onNodesChangeProp]
  );

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  // Handle node update from config panel
  const handleNodeUpdate = useCallback((nodeId: string, data: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...data } };
        }
        return node;
      })
    );
  }, [setNodes]);

  // Handle node delete from config panel
  const handleNodeDelete = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
  }, [setNodes, setEdges]);

  // Handle save
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(nodes, edges);
    }
  }, [nodes, edges, onSave]);

  return (
    <div className="flex w-full h-full">
      <div ref={reactFlowWrapper} className="flex-1">
        <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
        deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
        multiSelectionKeyCode={readOnly ? null : 'Shift'}
      >
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        
        {!readOnly && (
          <Panel position="top-right" className="flex gap-2">
            <div className="flex gap-1 bg-background border rounded-md p-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleUndo}
                disabled={!canUndo}
                title="Undo (Ctrl+Z)"
              >
                <Undo className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRedo}
                disabled={!canRedo}
                title="Redo (Ctrl+Y)"
              >
                <Redo className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex gap-1 bg-background border rounded-md p-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.zoomIn()}
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.zoomOut()}
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.fitView()}
                title="Fit View"
              >
                <Maximize className="h-4 w-4" />
              </Button>
            </div>
          </Panel>
        )}
      </ReactFlow>
      </div>
      
      {/* Node Configuration Panel */}
      {selectedNode && !readOnly && (
        <NodeConfigPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onUpdate={handleNodeUpdate}
          onDelete={handleNodeDelete}
        />
      )}
    </div>
  );
}

export function WorkflowEditor(props: WorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <WorkflowEditorInner {...props} />
    </ReactFlowProvider>
  );
}
