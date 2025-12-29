'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Panel,
  NodeTypes,
  EdgeTypes,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Plus,
  Save,
  Play,
  Settings,
  Users,
  Brain,
  Zap,
  GitBranch,
  Target,
  Trash2,
  Copy,
  Edit,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import type { Agent, Agentflow, AgentflowAgent } from '@/lib/api/agent-builder';

// Custom Node Types
const AgentNode = ({ data, selected }: { data: any; selected: boolean }) => {
  return (
    <div
      className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
        selected ? 'border-blue-500' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
          <Users className="w-4 h-4 text-blue-600" />
        </div>
        <div className="flex-1">
          <div className="font-medium text-sm">{data.name}</div>
          <div className="text-xs text-gray-500">{data.role}</div>
        </div>
      </div>
      
      {data.capabilities && data.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {data.capabilities.slice(0, 2).map((capability: string, index: number) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {capability}
            </Badge>
          ))}
          {data.capabilities.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{data.capabilities.length - 2}
            </Badge>
          )}
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Priority: {data.priority || 1}</span>
        <span>Timeout: {data.timeout_seconds || 60}s</span>
      </div>
      
      {/* Connection Handles */}
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full transform -translate-y-1/2 border-2 border-white" />
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full transform -translate-y-1/2 border-2 border-white" />
    </div>
  );
};

const SupervisorNode = ({ data, selected }: { data: any; selected: boolean }) => {
  return (
    <div
      className={`px-4 py-3 shadow-lg rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 text-white border-2 min-w-[200px] ${
        selected ? 'border-yellow-400' : 'border-transparent'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
          <Brain className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="font-medium text-sm">AI Supervisor</div>
          <div className="text-xs opacity-80">{data.llm_model || 'llama3.1'}</div>
        </div>
      </div>
      
      <div className="text-xs opacity-90">
        Max Iterations: {data.max_iterations || 10}
      </div>
      
      {/* Connection Handles */}
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-purple-400 rounded-full transform -translate-y-1/2 border-2 border-white" />
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-purple-400 rounded-full transform -translate-y-1/2 border-2 border-white" />
    </div>
  );
};

const nodeTypes: NodeTypes = {
  agent: AgentNode,
  supervisor: SupervisorNode,
};

const edgeTypes: EdgeTypes = {};

interface VisualWorkflowEditorProps {
  agentflowId: string;
  initialData?: Agentflow;
  onSave?: (data: any) => void;
}

export function VisualWorkflowEditor({
  agentflowId,
  initialData,
  onSave,
}: VisualWorkflowEditorProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // UI state
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [showNodeEditor, setShowNodeEditor] = useState(false);

  // Fetch agentflow data
  const { data: agentflow, isLoading } = useQuery({
    queryKey: ['agentflow', agentflowId],
    queryFn: () => agentBuilderAPI.getAgentflow(agentflowId),
    enabled: !!agentflowId,
  });

  // Fetch available agents
  const { data: availableAgents } = useQuery({
    queryKey: ['agents', 'available'],
    queryFn: () => agentBuilderAPI.getAgents({ page_size: 100 }),
  });

  // Initialize nodes and edges from agentflow data
  useEffect(() => {
    if (agentflow?.graph_definition) {
      const graphNodes = agentflow.graph_definition.nodes || [];
      const graphEdges = agentflow.graph_definition.edges || [];

      // Convert to React Flow format
      const flowNodes = graphNodes.map((node: any) => ({
        id: node.id,
        type: node.type,
        position: node.position || { x: 0, y: 0 },
        data: {
          ...node.data,
          label: node.data.name,
        },
      }));

      const flowEdges = graphEdges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type === 'dependency' ? 'smoothstep' : 'default',
        animated: edge.data?.type === 'data_flow',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: edge.data?.type === 'dependency' ? '#ef4444' : '#3b82f6',
        },
        style: {
          stroke: edge.data?.type === 'dependency' ? '#ef4444' : '#3b82f6',
          strokeWidth: 2,
        },
        label: edge.data?.label,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    }
  }, [agentflow, setNodes, setEdges]);

  // Add supervisor node if enabled
  useEffect(() => {
    if (agentflow?.supervisor_config?.enabled) {
      const supervisorExists = nodes.some(node => node.type === 'supervisor');
      if (!supervisorExists) {
        const supervisorNode = {
          id: 'supervisor',
          type: 'supervisor',
          position: { x: 400, y: 50 },
          data: {
            name: 'AI Supervisor',
            ...agentflow.supervisor_config,
          },
        };
        setNodes(prev => [supervisorNode, ...prev]);
      }
    }
  }, [agentflow?.supervisor_config, nodes, setNodes]);

  // Handle connection between nodes
  const onConnect = useCallback(
    (params: Connection) => {
      const edge = {
        ...params,
        type: 'default',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#3b82f6',
        },
        style: {
          stroke: '#3b82f6',
          strokeWidth: 2,
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowNodeEditor(true);
  }, []);

  // Add new agent node
  const addAgentNode = useCallback((agent: Agent) => {
    const newNode = {
      id: `agent-${Date.now()}`,
      type: 'agent',
      position: {
        x: Math.random() * 400 + 100,
        y: Math.random() * 300 + 100,
      },
      data: {
        agent_id: agent.id,
        name: agent.name,
        role: 'worker',
        description: agent.description,
        capabilities: [],
        priority: 1,
        max_retries: 3,
        timeout_seconds: 60,
      },
    };

    setNodes((nds) => [...nds, newNode]);
    setShowAgentSelector(false);
    
    toast({
      title: '에이전트 추가됨',
      description: `${agent.name}이(가) 워크플로우에 추가되었습니다.`,
    });
  }, [setNodes, toast]);

  // Save workflow
  const saveWorkflow = useCallback(async () => {
    try {
      const graphDefinition = {
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: node.data,
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          data: {
            label: edge.label,
            type: edge.animated ? 'data_flow' : 'control_flow',
          },
        })),
        viewport: reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 },
      };

      await agentBuilderAPI.updateAgentflow(agentflowId, {
        graph_definition: graphDefinition,
      });

      queryClient.invalidateQueries({ queryKey: ['agentflow', agentflowId] });
      
      toast({
        title: '워크플로우 저장됨',
        description: '시각적 워크플로우가 성공적으로 저장되었습니다.',
      });

      if (onSave) {
        onSave(graphDefinition);
      }
    } catch (error) {
      toast({
        title: '저장 실패',
        description: '워크플로우 저장 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  }, [nodes, edges, reactFlowInstance, agentflowId, queryClient, toast, onSave]);

  // Execute workflow
  const executeWorkflow = useCallback(async () => {
    try {
      await saveWorkflow(); // Save first
      
      const result = await agentBuilderAPI.executeAgentflow(agentflowId, {
        input: 'Visual workflow execution',
        context: { source: 'visual_editor' },
      });

      toast({
        title: '워크플로우 실행 시작',
        description: `실행 ID: ${result.execution_id}`,
      });
    } catch (error) {
      toast({
        title: '실행 실패',
        description: '워크플로우 실행 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  }, [saveWorkflow, agentflowId, toast]);

  // Delete selected node
  const deleteSelectedNode = useCallback(() => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
      setEdges((eds) => eds.filter((edge) => 
        edge.source !== selectedNode.id && edge.target !== selectedNode.id
      ));
      setSelectedNode(null);
      setShowNodeEditor(false);
    }
  }, [selectedNode, setNodes, setEdges]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>워크플로우 로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[600px] w-full border rounded-lg overflow-hidden bg-gray-50">
      <div ref={reactFlowWrapper} className="h-full w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onInit={setReactFlowInstance}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          
          {/* Top Panel */}
          <Panel position="top-left">
            <div className="flex items-center gap-2 bg-white rounded-lg shadow-lg p-2">
              <Button
                size="sm"
                onClick={() => setShowAgentSelector(true)}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                에이전트 추가
              </Button>
              
              <Separator orientation="vertical" className="h-6" />
              
              <Button
                size="sm"
                variant="outline"
                onClick={saveWorkflow}
                className="flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                저장
              </Button>
              
              <Button
                size="sm"
                onClick={executeWorkflow}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              >
                <Play className="w-4 h-4" />
                실행
              </Button>
            </div>
          </Panel>

          {/* Node Info Panel */}
          {selectedNode && (
            <Panel position="top-right">
              <Card className="w-80 shadow-lg">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">노드 정보</CardTitle>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowNodeEditor(true)}
                      >
                        <Edit className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={deleteSelectedNode}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">이름:</span> {selectedNode.data.name}
                    </div>
                    <div>
                      <span className="font-medium">역할:</span> {selectedNode.data.role}
                    </div>
                    <div>
                      <span className="font-medium">우선순위:</span> {selectedNode.data.priority || 1}
                    </div>
                    {selectedNode.data.capabilities && selectedNode.data.capabilities.length > 0 && (
                      <div>
                        <span className="font-medium">역량:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedNode.data.capabilities.map((cap: string, index: number) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Panel>
          )}
        </ReactFlow>
      </div>

      {/* Agent Selector Dialog */}
      <Dialog open={showAgentSelector} onOpenChange={setShowAgentSelector}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>에이전트 선택</DialogTitle>
            <DialogDescription>
              워크플로우에 추가할 에이전트를 선택하세요.
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-96">
            <div className="grid grid-cols-1 gap-3">
              {availableAgents?.agents?.map((agent: Agent) => (
                <Card
                  key={agent.id}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => addAgentNode(agent)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <Users className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium">{agent.name}</h4>
                        <p className="text-sm text-gray-500">{agent.description}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {agent.llm_provider}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {agent.llm_model}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Node Editor Dialog */}
      <Dialog open={showNodeEditor} onOpenChange={setShowNodeEditor}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>노드 편집</DialogTitle>
            <DialogDescription>
              선택된 노드의 속성을 편집하세요.
            </DialogDescription>
          </DialogHeader>
          
          {selectedNode && (
            <div className="space-y-4">
              <div>
                <Label>이름</Label>
                <Input
                  value={selectedNode.data.name || ''}
                  onChange={(e) => {
                    const updatedNode = {
                      ...selectedNode,
                      data: { ...selectedNode.data, name: e.target.value },
                    };
                    setNodes((nds) =>
                      nds.map((node) => (node.id === selectedNode.id ? updatedNode : node))
                    );
                    setSelectedNode(updatedNode);
                  }}
                />
              </div>
              
              <div>
                <Label>역할</Label>
                <Input
                  value={selectedNode.data.role || ''}
                  onChange={(e) => {
                    const updatedNode = {
                      ...selectedNode,
                      data: { ...selectedNode.data, role: e.target.value },
                    };
                    setNodes((nds) =>
                      nds.map((node) => (node.id === selectedNode.id ? updatedNode : node))
                    );
                    setSelectedNode(updatedNode);
                  }}
                />
              </div>
              
              <div>
                <Label>설명</Label>
                <Textarea
                  value={selectedNode.data.description || ''}
                  onChange={(e) => {
                    const updatedNode = {
                      ...selectedNode,
                      data: { ...selectedNode.data, description: e.target.value },
                    };
                    setNodes((nds) =>
                      nds.map((node) => (node.id === selectedNode.id ? updatedNode : node))
                    );
                    setSelectedNode(updatedNode);
                  }}
                />
              </div>
              
              <div>
                <Label>우선순위</Label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={selectedNode.data.priority || 1}
                  onChange={(e) => {
                    const updatedNode = {
                      ...selectedNode,
                      data: { ...selectedNode.data, priority: parseInt(e.target.value) },
                    };
                    setNodes((nds) =>
                      nds.map((node) => (node.id === selectedNode.id ? updatedNode : node))
                    );
                    setSelectedNode(updatedNode);
                  }}
                />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}