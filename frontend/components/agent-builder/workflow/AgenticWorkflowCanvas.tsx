'use client';

import { useState, useCallback, useMemo } from 'react';
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
  Node,
  Edge,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  Square, 
  Save, 
  Sparkles,
  Plus,
  Trash2
} from 'lucide-react';
import AgenticNode from '../workflow-nodes/AgenticNode';
import { AgenticBlockPalette } from '../blocks/AgenticBlockPalette';
import { AgenticBlockConfigPanel } from '../blocks/AgenticBlockConfigPanel';
import { BlockTypeConfig } from '@/lib/api/block-types';
import { cn } from '@/lib/utils';

// Node types including Agentic
const nodeTypes: NodeTypes = {
  agentic: AgenticNode,
};

// Initial demo nodes
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'agentic',
    position: { x: 100, y: 100 },
    data: {
      label: 'Query Analysis',
      blockType: 'agentic_rag',
      icon: 'brain',
      status: 'idle',
      config: {
        strategy: 'adaptive',
        top_k: 10,
      },
    },
  },
  {
    id: '2',
    type: 'agentic',
    position: { x: 450, y: 100 },
    data: {
      label: 'Response Reflection',
      blockType: 'agentic_reflection',
      icon: 'sparkles',
      status: 'idle',
      config: {
        max_iterations: 3,
        quality_threshold: 0.8,
      },
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    animated: true,
  },
];

interface AgenticWorkflowCanvasProps {
  workflowId?: string;
  onSave?: (nodes: Node[], edges: Edge[]) => void;
}

function AgenticWorkflowCanvasInner({ 
  workflowId = 'agentic-workflow',
  onSave 
}: AgenticWorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedBlock, setSelectedBlock] = useState<BlockTypeConfig | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeTab, setActiveTab] = useState<'canvas' | 'blocks' | 'config'>('canvas');

  // Handle connection
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true }, eds));
    },
    [setEdges]
  );

  // Add new node from block
  const handleAddBlock = useCallback((block: BlockTypeConfig) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'agentic',
      position: { 
        x: Math.random() * 400 + 100, 
        y: Math.random() * 300 + 100 
      },
      data: {
        label: block.name,
        blockType: block.type as any,
        icon: block.icon,
        bgColor: block.bg_color,
        status: 'idle',
        config: {},
      },
    };
    
    setNodes((nds) => [...nds, newNode]);
    setSelectedNode(newNode);
    setActiveTab('config');
  }, [setNodes]);

  // Update node configuration
  const handleConfigSave = useCallback((config: Record<string, any>) => {
    if (!selectedNode) return;
    
    setNodes((nds) =>
      nds.map((node) =>
        node.id === selectedNode.id
          ? { ...node, data: { ...node.data, config } }
          : node
      )
    );
  }, [selectedNode, setNodes]);

  // Delete selected nodes
  const handleDelete = useCallback(() => {
    const selectedNodeIds = nodes.filter(n => n.selected).map(n => n.id);
    setNodes((nds) => nds.filter((node) => !selectedNodeIds.includes(node.id)));
    setEdges((eds) => eds.filter((edge) => 
      !selectedNodeIds.includes(edge.source) && !selectedNodeIds.includes(edge.target)
    ));
  }, [nodes, setNodes, setEdges]);

  // Execute workflow
  const handleExecute = useCallback(async () => {
    setIsExecuting(true);
    
    // Simulate execution
    for (const node of nodes) {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? { ...n, data: { ...n.data, status: 'running' } }
            : n
        )
      );
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? { 
                ...n, 
                data: { 
                  ...n.data, 
                  status: 'success',
                  iterationCount: Math.floor(Math.random() * 3) + 1,
                  qualityScore: Math.random() * 0.3 + 0.7,
                  confidenceScore: Math.random() * 0.2 + 0.8,
                } 
              }
            : n
        )
      );
    }
    
    setIsExecuting(false);
  }, [nodes, setNodes]);

  // Stop execution
  const handleStop = useCallback(() => {
    setIsExecuting(false);
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle' },
      }))
    );
  }, [setNodes]);

  // Save workflow
  const handleSave = useCallback(() => {
    onSave?.(nodes, edges);
  }, [nodes, edges, onSave]);

  // Node selection
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setActiveTab('config');
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* Toolbar */}
      <div className="border-b bg-background p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Agentic Workflow</h2>
              <p className="text-sm text-muted-foreground">
                {nodes.length} blocks, {edges.length} connections
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('blocks')}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Block
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={!nodes.some(n => n.selected)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
            >
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
            {isExecuting ? (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleStop}
              >
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleExecute}
              >
                <Play className="h-4 w-4 mr-2" />
                Execute
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-muted/30"
          >
            <Background />
            <Controls />
            <MiniMap 
              nodeColor={(node) => {
                const data = node.data as any;
                switch (data.blockType) {
                  case 'agentic_reflection': return '#8B5CF6';
                  case 'agentic_planning': return '#10B981';
                  case 'agentic_tool_selector': return '#F59E0B';
                  case 'agentic_rag': return '#EC4899';
                  default: return '#6366F1';
                }
              }}
            />
            
            {/* Info Panel */}
            <Panel position="top-right" className="bg-background/95 backdrop-blur-sm p-4 rounded-lg border shadow-lg">
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500" />
                  <span>Reflection</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Planning</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span>Tool Selector</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-pink-500" />
                  <span>Agentic RAG</span>
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Right Sidebar */}
        <div className="w-96 border-l bg-background overflow-auto">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
            <TabsList className="w-full grid grid-cols-2">
              <TabsTrigger value="blocks">Blocks</TabsTrigger>
              <TabsTrigger value="config">Config</TabsTrigger>
            </TabsList>
            
            <TabsContent value="blocks" className="p-4">
              <AgenticBlockPalette
                onBlockSelect={handleAddBlock}
                onBlockDragStart={(block) => console.log('Drag:', block)}
              />
            </TabsContent>
            
            <TabsContent value="config" className="p-4">
              {selectedNode && selectedBlock ? (
                <AgenticBlockConfigPanel
                  block={selectedBlock}
                  initialConfig={selectedNode.data.config || {}}
                  onSave={handleConfigSave}
                  onCancel={() => setSelectedNode(null)}
                />
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">No Block Selected</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Click on a block in the canvas to configure it
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export function AgenticWorkflowCanvas(props: AgenticWorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <AgenticWorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}

export default AgenticWorkflowCanvas;
