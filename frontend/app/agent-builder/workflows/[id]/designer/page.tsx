'use client';

import { useState, useCallback, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactFlow, {
  Node,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import WorkflowPropertiesPanel from '@/components/agent-builder/WorkflowPropertiesPanel';
import WorkflowExecutionDialog from '@/components/agent-builder/WorkflowExecutionDialog';
import {
  ArrowLeft,
  Save,
  Play,
  CheckCircle,
  Bot,
  Box,
  GitBranch,
  Repeat,
  Layers,
} from 'lucide-react';

// Import custom node components (will be created in next subtask)
import AgentNode from '@/components/agent-builder/workflow-nodes/AgentNode';
import BlockNode from '@/components/agent-builder/workflow-nodes/BlockNode';
import ControlNode from '@/components/agent-builder/workflow-nodes/ControlNode';

const nodeTypes: NodeTypes = {
  agent: AgentNode,
  block: BlockNode,
  control: ControlNode,
};

interface WorkflowData {
  id: string;
  name: string;
  description: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
    entry_point: string;
  };
}

interface Agent {
  id: string;
  name: string;
  description: string;
}

interface Block {
  id: string;
  name: string;
  description: string;
  block_type: string;
}

export default function WorkflowDesignerPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<WorkflowData | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isPropertiesPanelOpen, setIsPropertiesPanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isExecutionDialogOpen, setIsExecutionDialogOpen] = useState(false);
  const [currentExecutionId, setCurrentExecutionId] = useState<string | null>(null);

  // Load workflow data
  useEffect(() => {
    const loadWorkflow = async () => {
      try {
        const response = await fetch(`/api/agent-builder/workflows/${workflowId}`);
        if (!response.ok) throw new Error('Failed to load workflow');
        const data = await response.json();
        setWorkflow(data);

        // Load nodes and edges from graph definition
        if (data.graph_definition) {
          setNodes(data.graph_definition.nodes || []);
          setEdges(data.graph_definition.edges || []);
        }
      } catch (error) {
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to load workflow',
        });
      }
    };

    loadWorkflow();
  }, [workflowId, toast, setNodes, setEdges]);

  // Load agents and blocks for palette
  useEffect(() => {
    const loadResources = async () => {
      try {
        const [agentsRes, blocksRes] = await Promise.all([
          fetch('/api/agent-builder/agents'),
          fetch('/api/agent-builder/blocks'),
        ]);

        if (agentsRes.ok) {
          const agentsData = await agentsRes.json();
          setAgents(agentsData);
        }

        if (blocksRes.ok) {
          const blocksData = await blocksRes.json();
          setBlocks(blocksData);
        }
      } catch (error) {
        console.error('Failed to load resources:', error);
      }
    };

    loadResources();
  }, []);

  const onConnect = useCallback(
    (connection: Connection) => {
      // Validate connection
      if (!connection.source || !connection.target) {
        toast({
          variant: 'destructive',
          title: 'Invalid Connection',
          description: 'Both source and target nodes must be selected',
        });
        return;
      }

      // Prevent self-connections
      if (connection.source === connection.target) {
        toast({
          variant: 'destructive',
          title: 'Invalid Connection',
          description: 'Cannot connect a node to itself',
        });
        return;
      }

      // Check if connection already exists
      const existingConnection = edges.find(
        (edge) =>
          edge.source === connection.source &&
          edge.target === connection.target &&
          edge.sourceHandle === connection.sourceHandle &&
          edge.targetHandle === connection.targetHandle
      );

      if (existingConnection) {
        toast({
          variant: 'destructive',
          title: 'Duplicate Connection',
          description: 'This connection already exists',
        });
        return;
      }

      // Add the connection
      setEdges((eds) => addEdge(connection, eds));
      
      toast({
        title: 'Connection Created',
        description: 'Nodes connected successfully',
      });
    },
    [setEdges, edges, toast]
  );

  const handleDragStart = (event: React.DragEvent, nodeType: string, data: any) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ nodeType, data }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      try {
        const reactFlowBounds = event.currentTarget.getBoundingClientRect();
        const transferData = event.dataTransfer.getData('application/reactflow');
        
        if (!transferData) {
          toast({
            variant: 'destructive',
            title: 'Drop Failed',
            description: 'Invalid node data',
          });
          return;
        }

        const data = JSON.parse(transferData);

        const position = {
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        };

        const newNode: Node = {
          id: `${data.nodeType}-${Date.now()}`,
          type: data.nodeType,
          position,
          data: {
            label: data.data.name,
            ...data.data,
          },
        };

        setNodes((nds) => nds.concat(newNode));
        
        toast({
          title: 'Node Added',
          description: `${data.data.name} added to workflow`,
        });
      } catch (error) {
        toast({
          variant: 'destructive',
          title: 'Drop Failed',
          description: 'Failed to add node to workflow',
        });
      }
    },
    [setNodes, toast]
  );

  const handleNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setIsPropertiesPanelOpen(true);
  }, []);

  const handleNodeDragStop = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      // Find nearby nodes within connection range
      const connectionRange = 150; // pixels
      const sourceNode = node;

      nodes.forEach((targetNode) => {
        if (targetNode.id === sourceNode.id) return;

        // Calculate distance between nodes
        const dx = targetNode.position.x - sourceNode.position.x;
        const dy = targetNode.position.y - sourceNode.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < connectionRange) {
          // Check if connection already exists
          const existingConnection = edges.find(
            (edge) =>
              (edge.source === sourceNode.id && edge.target === targetNode.id) ||
              (edge.source === targetNode.id && edge.target === sourceNode.id)
          );

          if (!existingConnection) {
            // Determine connection direction based on vertical position
            let newConnection: Connection;
            if (sourceNode.position.y < targetNode.position.y) {
              // Source is above target - connect source output to target input
              newConnection = {
                source: sourceNode.id,
                target: targetNode.id,
                sourceHandle: 'output',
                targetHandle: 'input',
              };
            } else {
              // Source is below target - connect target output to source input
              newConnection = {
                source: targetNode.id,
                target: sourceNode.id,
                sourceHandle: 'output',
                targetHandle: 'input',
              };
            }

            // Add the connection
            setEdges((eds) => addEdge(newConnection, eds));

            toast({
              title: 'Auto-Connected',
              description: 'Nodes automatically connected',
            });
          }
        }
      });
    },
    [nodes, edges, setEdges, toast]
  );

  const handleCloseProperties = () => {
    setIsPropertiesPanelOpen(false);
    setSelectedNode(null);
  };

  const handleUpdateNode = (nodeId: string, updates: Partial<Node['data']>) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...updates } }
          : node
      )
    );
    
    toast({
      title: 'Node Updated',
      description: 'Node properties saved successfully',
    });
  };

  const handleSave = async () => {
    if (!workflow) return;

    setIsSaving(true);
    try {
      // Find the start node as entry point
      const startNode = nodes.find(node => node.type === 'start' || node.type === 'trigger');
      const entryPoint = startNode?.id || (nodes.length > 0 ? nodes[0].id : '');

      const response = await fetch(`/api/agent-builder/workflows/${workflowId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflow.name,
          description: workflow.description,
          nodes: nodes.map(node => {
            const isControl = node.type === 'start' || node.type === 'end' || 
                             node.type === 'condition' || node.type === 'trigger';
            return {
              id: node.id,
              node_type: isControl ? 'control' : node.type,
              node_ref_id: isControl ? null : (node.data?.agentId || node.data?.blockId || null),
              position_x: node.position.x,
              position_y: node.position.y,
              configuration: node.data || {},
            };
          }),
          edges: edges.map(edge => ({
            id: edge.id,
            source_node_id: edge.source,
            target_node_id: edge.target,
            edge_type: 'normal',
            source_handle: edge.sourceHandle,
            target_handle: edge.targetHandle,
          })),
          entry_point: entryPoint,
        }),
      });

      if (!response.ok) throw new Error('Failed to save workflow');

      toast({
        title: 'Success',
        description: 'Workflow saved successfully',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to save workflow',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_definition: { nodes, edges },
        }),
      });

      if (!response.ok) throw new Error('Validation failed');

      const result = await response.json();
      
      if (result.valid) {
        toast({
          title: 'Validation Successful',
          description: 'Workflow is valid and ready to execute',
        });
      } else {
        toast({
          variant: 'destructive',
          title: 'Validation Failed',
          description: result.errors?.join(', ') || 'Workflow has errors',
        });
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to validate workflow',
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleRun = async () => {
    // Save first, then execute
    await handleSave();
    
    try {
      const response = await fetch(`/api/agent-builder/executions/workflows/${workflowId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_data: {},
        }),
      });

      if (!response.ok) throw new Error('Failed to start execution');

      const result = await response.json();
      
      // Show execution dialog
      setCurrentExecutionId(result.execution_id);
      setIsExecutionDialogOpen(true);
      
      toast({
        title: 'Execution Started',
        description: 'Workflow execution has been initiated',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to start workflow execution',
      });
    }
  };

  const handleBack = () => {
    router.push('/agent-builder/workflows');
  };

  if (!workflow) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading workflow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Toolbar */}
      <div className="border-b bg-card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h2 className="text-lg font-semibold">{workflow.name}</h2>
              <p className="text-sm text-muted-foreground">Workflow Designer</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleValidate}
              disabled={isValidating}
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              {isValidating ? 'Validating...' : 'Validate'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
            >
              <Save className="mr-2 h-4 w-4" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
            <Button size="sm" onClick={handleRun}>
              <Play className="mr-2 h-4 w-4" />
              Run
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Node Palette */}
        <aside className="w-64 border-r bg-card overflow-auto">
          <ScrollArea className="h-full">
            <div className="p-3 space-y-3">
              <div>
                <h3 className="text-xs font-semibold mb-1.5">Agents</h3>
                <div className="space-y-1.5">
                  {agents.map((agent) => (
                    <Card
                      key={agent.id}
                      className="cursor-move hover:shadow-md transition-shadow"
                      draggable
                      onDragStart={(e) => handleDragStart(e, 'agent', agent)}
                    >
                      <CardContent className="p-2">
                        <div className="flex items-center gap-2">
                          <Bot className="h-3.5 w-3.5 text-primary" />
                          <span className="text-xs font-medium">{agent.name}</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-xs font-semibold mb-1.5">Blocks</h3>
                <div className="space-y-1.5">
                  {blocks.map((block) => (
                    <Card
                      key={block.id}
                      className="cursor-move hover:shadow-md transition-shadow"
                      draggable
                      onDragStart={(e) => handleDragStart(e, 'block', block)}
                    >
                      <CardContent className="p-2">
                        <div className="flex items-center gap-2">
                          <Box className="h-3.5 w-3.5 text-secondary" />
                          <span className="text-xs font-medium">{block.name}</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-xs font-semibold mb-1.5">Control Flow</h3>
                <div className="space-y-1.5">
                  <Card
                    className="cursor-move hover:shadow-md transition-shadow"
                    draggable
                    onDragStart={(e) =>
                      handleDragStart(e, 'control', {
                        name: 'Conditional',
                        controlType: 'conditional',
                      })
                    }
                  >
                    <CardContent className="p-2">
                      <div className="flex items-center gap-2">
                        <GitBranch className="h-3.5 w-3.5 text-yellow-500" />
                        <span className="text-xs font-medium">Conditional</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card
                    className="cursor-move hover:shadow-md transition-shadow"
                    draggable
                    onDragStart={(e) =>
                      handleDragStart(e, 'control', {
                        name: 'Loop',
                        controlType: 'loop',
                      })
                    }
                  >
                    <CardContent className="p-2">
                      <div className="flex items-center gap-2">
                        <Repeat className="h-3.5 w-3.5 text-green-500" />
                        <span className="text-xs font-medium">Loop</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card
                    className="cursor-move hover:shadow-md transition-shadow"
                    draggable
                    onDragStart={(e) =>
                      handleDragStart(e, 'control', {
                        name: 'Parallel',
                        controlType: 'parallel',
                      })
                    }
                  >
                    <CardContent className="p-2">
                      <div className="flex items-center gap-2">
                        <Layers className="h-3.5 w-3.5 text-purple-500" />
                        <span className="text-xs font-medium">Parallel</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </ScrollArea>
        </aside>

        {/* React Flow Canvas */}
        <div
          className="flex-1 bg-muted/20"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={handleNodeClick}
            onNodeDragStop={handleNodeDragStop}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid={true}
            snapGrid={[15, 15]}
            defaultEdgeOptions={{
              animated: true,
            }}
          >
            <Background variant={BackgroundVariant.Dots} />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Properties Panel */}
        <WorkflowPropertiesPanel
          node={selectedNode}
          isOpen={isPropertiesPanelOpen}
          onClose={handleCloseProperties}
          onUpdate={handleUpdateNode}
        />

        {/* Execution Dialog */}
        <WorkflowExecutionDialog
          isOpen={isExecutionDialogOpen}
          onClose={() => setIsExecutionDialogOpen(false)}
          executionId={currentExecutionId}
          workflowName={workflow.name}
        />
      </div>
    </div>
  );
}
