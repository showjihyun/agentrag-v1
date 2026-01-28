/**
 * Workflow Editor - 드래그 앤 드롭 기반 워크플로우 편집기
 * React Flow 기반으로 구현된 시각적 워크플로우 편집기
 */
import React, { useCallback, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Connection,
  EdgeChange,
  NodeChange,
  ReactFlowProvider,
  ReactFlowInstance,
  Panel,
  useReactFlow,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Play, 
  Save, 
  Download, 
  Upload, 
  Undo, 
  Redo, 
  ZoomIn, 
  ZoomOut,
  Grid,
  Settings,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  MessageSquare,
  Bot
} from 'lucide-react';

// 커스텀 노드 컴포넌트들
import { LLMNode } from './nodes/LLMNode';
import { ToolNode } from './nodes/ToolNode';
import { ConditionNode } from './nodes/ConditionNode';
import { InputNode } from './nodes/InputNode';
import { OutputNode } from './nodes/OutputNode';
import { AgentNode } from './nodes/AgentNode';
import { OrchestrationNode } from './nodes/OrchestrationNode';

// 커스텀 엣지 컴포넌트들
import { DefaultEdge } from './edges/DefaultEdge';
import { ConditionalEdge } from './edges/ConditionalEdge';
import { DataEdge } from './edges/DataEdge';

// 사이드바 컴포넌트들
import { NodePalette } from './sidebar/NodePalette';
import { PropertyPanel } from './sidebar/PropertyPanel';
import { WorkflowSettings } from './sidebar/WorkflowSettings';

// 훅과 유틸리티
import { useWorkflowStore } from '@/lib/stores/workflow-store';
import { useWorkflowValidation } from '@/hooks/useWorkflowValidation';
import { useWorkflowExecution, ExecutionUpdate } from '@/hooks/useWorkflowExecution';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

// AI Chat Panel
import { AIAgentChatPanel } from '@/components/agent-builder/workflow/AIAgentChatPanel';

// 타입 정의
interface WorkflowEditorProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  readOnly?: boolean;
  onSave?: (workflow: any) => void;
  onExecute?: (workflow: any) => void;
  className?: string;
}

interface NodeTemplate {
  id: string;
  type: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  category: string;
  defaultData: any;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ExecutionLog {
  id: string;
  nodeId: string;
  nodeName: string;
  status: 'running' | 'success' | 'error' | 'warning';
  message: string;
  timestamp: Date;
  duration?: number;
  output?: any;  // ✅ 노드 출력 결과
  input?: any;   // ✅ 노드 입력 데이터
  error?: string; // ✅ 에러 메시지
}

// 노드 타입 정의
const nodeTypes = {
  llm: LLMNode,
  tool: ToolNode,
  condition: ConditionNode,
  input: InputNode,
  output: OutputNode,
  agent: AgentNode,
  orchestration: OrchestrationNode,
};

// 엣지 타입 정의
const edgeTypes = {
  default: DefaultEdge,
  conditional: ConditionalEdge,
  data: DataEdge,
};

// 노드 템플릿
const nodeTemplates: NodeTemplate[] = [
  {
    id: 'input',
    type: 'input',
    label: 'Input',
    description: 'Workflow input node',
    icon: <div className="w-4 h-4 bg-green-500 rounded" />,
    category: 'Basic',
    defaultData: { label: 'Input', value: '' }
  },
  {
    id: 'output',
    type: 'output',
    label: 'Output',
    description: 'Workflow output node',
    icon: <div className="w-4 h-4 bg-red-500 rounded" />,
    category: 'Basic',
    defaultData: { label: 'Output', value: '' }
  },
  {
    id: 'llm',
    type: 'llm',
    label: 'LLM',
    description: 'Large Language Model node',
    icon: <div className="w-4 h-4 bg-blue-500 rounded" />,
    category: 'AI',
    defaultData: { 
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      maxTokens: 1000,
      prompt: ''
    }
  },
  {
    id: 'tool',
    type: 'tool',
    label: 'Tool',
    description: 'External tool integration',
    icon: <div className="w-4 h-4 bg-purple-500 rounded" />,
    category: 'Tools',
    defaultData: { 
      toolType: 'web_search',
      parameters: {}
    }
  },
  {
    id: 'condition',
    type: 'condition',
    label: 'Condition',
    description: 'Conditional branching',
    icon: <div className="w-4 h-4 bg-yellow-500 rounded" />,
    category: 'Logic',
    defaultData: { 
      condition: '',
      operator: 'equals'
    }
  },
  {
    id: 'agent',
    type: 'agent',
    label: 'Agent',
    description: 'AI Agent execution',
    icon: <div className="w-4 h-4 bg-indigo-500 rounded" />,
    category: 'AI',
    defaultData: { 
      agentType: 'openai_functions',
      tools: [],
      systemPrompt: ''
    }
  },
  {
    id: 'orchestration',
    type: 'orchestration',
    label: 'Orchestration',
    description: 'Multi-agent orchestration',
    icon: <div className="w-4 h-4 bg-pink-500 rounded" />,
    category: 'Advanced',
    defaultData: { 
      pattern: 'sequential',
      agents: [],
      config: {}
    }
  }
];

const WorkflowEditorContent: React.FC<WorkflowEditorProps> = ({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  readOnly = false,
  onSave,
  onExecute,
  className
}) => {
  // React Flow 상태
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  // UI 상태
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [showGrid, setShowGrid] = useState(true);
  const [showMiniMap, setShowMiniMap] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'palette' | 'properties' | 'settings'>('palette');
  
  // 편집 상태
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  // AI Chat Panel 상태
  const [showAIChatPanel, setShowAIChatPanel] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);
  
  // 히스토리 관리
  const [history, setHistory] = useState<{ nodes: Node[], edges: Edge[] }[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // 스토어와 훅
  const { 
    currentWorkflow, 
    updateWorkflow, 
    saveWorkflow,
    isLoading 
  } = useWorkflowStore();
  
  const { validateWorkflow } = useWorkflowValidation();
  const { 
    executeWorkflow, 
    executeWorkflowStreaming,
    streamingUpdates,
    currentExecution 
  } = useWorkflowExecution({
    onStreamingUpdate: (update: ExecutionUpdate) => {
      // 실행 로그 추가
      const log: ExecutionLog = {
        id: `${update.execution_id}_${Date.now()}`,
        nodeId: update.node_id || update.data?.node_id || 'workflow',
        nodeName: update.data?.node_name || update.update_type,
        status: update.update_type.includes('error') ? 'error' 
              : update.update_type.includes('complete') ? 'success' 
              : 'running',
        message: update.data?.message || JSON.stringify(update.data || {}),
        timestamp: new Date(update.timestamp),
        duration: update.duration_ms || update.data?.execution_time_ms,
        output: update.output || update.data?.output || update.data?.result,  // ✅ 여러 경로 확인
        input: update.input || update.data?.input,  // ✅ input 추가
        error: update.error || update.data?.error,  // ✅ error 추가
      };
      setExecutionLogs(prev => [...prev, log]);
      
      // AI 노드 결과를 채팅 메시지로 추가
      if (update.update_type === 'node_complete' && update.data?.node_type) {
        const aiNodeTypes = ['llm', 'agent', 'orchestration', 'ai_agent'];
        if (aiNodeTypes.includes(update.data.node_type)) {
          // output에서 response 추출
          const outputData = update.output || update.data?.output || update.data?.result;
          const responseText = outputData?.response || outputData?.output || JSON.stringify(outputData, null, 2);
          
          const aiResponse: ChatMessage = {
            role: 'assistant',
            content: responseText,
            timestamp: new Date(update.timestamp),
          };
          setChatMessages(prev => [...prev, aiResponse]);
        }
      }
      
      // 워크플로우 완료 시 최종 결과 표시
      if (update.update_type === 'workflow_complete') {
        const finalMessage: ChatMessage = {
          role: 'assistant',
          content: `✅ Workflow completed successfully!\n\nExecution Time: ${update.data?.execution_time_seconds?.toFixed(2)}s\n\nResults:\n${JSON.stringify(update.data?.results, null, 2)}`,
          timestamp: new Date(update.timestamp),
        };
        setChatMessages(prev => [...prev, finalMessage]);
      }
      
      // 에러 발생 시 에러 메시지 표시
      if (update.update_type === 'workflow_error' || update.update_type === 'node_error') {
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content: `❌ Error: ${update.error || update.data?.error || 'Unknown error occurred'}`,
          timestamp: new Date(update.timestamp),
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    },
    onExecutionComplete: (result) => {
      setExecutionResults(result);
      setIsExecuting(false);
    },
    onExecutionError: (error) => {
      setValidationErrors([`Execution failed: ${error.message}`]);
      setIsExecuting(false);
    }
  });
  
  // 드래그 앤 드롭 핸들러
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);
  
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      
      if (!reactFlowInstance) return;
      
      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      
      if (!type) return;
      
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });
      
      const template = nodeTemplates.find(t => t.type === type);
      if (!template) return;
      
      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: { ...template.defaultData, label: template.label },
      };
      
      setNodes((nds) => nds.concat(newNode));
      saveToHistory();
    },
    [reactFlowInstance, setNodes]
  );
  
  // 연결 핸들러
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        id: `edge_${Date.now()}`,
        type: 'default',
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
      saveToHistory();
    },
    [setEdges]
  );
  
  // 노드 변경 핸들러
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes);
      
      // 선택된 노드 업데이트
      const selectedChange = changes.find(change => 
        change.type === 'select' && change.selected
      );
      if (selectedChange) {
        const selectedNode = nodes.find(node => node.id === selectedChange.id);
        setSelectedNode(selectedNode || null);
      }
    },
    [onNodesChange, nodes]
  );
  
  // 엣지 변경 핸들러
  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(changes);
      
      // 선택된 엣지 업데이트
      const selectedChange = changes.find(change => 
        change.type === 'select' && change.selected
      );
      if (selectedChange) {
        const selectedEdge = edges.find(edge => edge.id === selectedChange.id);
        setSelectedEdge(selectedEdge || null);
      }
    },
    [onEdgesChange, edges]
  );
  
  // 히스토리 관리
  const saveToHistory = useCallback(() => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({ nodes: [...nodes], edges: [...edges] });
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex, nodes, edges]);
  
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      setNodes(prevState.nodes);
      setEdges(prevState.edges);
      setHistoryIndex(historyIndex - 1);
    }
  }, [history, historyIndex, setNodes, setEdges]);
  
  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setNodes(nextState.nodes);
      setEdges(nextState.edges);
      setHistoryIndex(historyIndex + 1);
    }
  }, [history, historyIndex, setNodes, setEdges]);
  
  // 키보드 단축키
  useKeyboardShortcuts({
    'ctrl+z': undo,
    'ctrl+y': redo,
    'ctrl+s': handleSave,
    'delete': handleDelete,
    'ctrl+c': handleCopy,
    'ctrl+v': handlePaste,
  });
  
  // 워크플로우 저장
  const handleSave = useCallback(async () => {
    if (readOnly) return;
    
    const workflow = {
      id: workflowId,
      nodes,
      edges,
      metadata: {
        lastModified: new Date().toISOString(),
        version: '1.0'
      }
    };
    
    try {
      if (onSave) {
        await onSave(workflow);
      } else {
        await saveWorkflow(workflow);
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  }, [workflowId, nodes, edges, readOnly, onSave, saveWorkflow]);
  
  // 워크플로우 실행
  const handleExecute = useCallback(async () => {
    if (readOnly) return;
    
    // 검증
    const errors = validateWorkflow(nodes, edges);
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    setIsExecuting(true);
    setValidationErrors([]);
    setExecutionLogs([]); // 로그 초기화
    
    // AI 노드가 있는지 확인
    const hasAINodes = nodes.some(node => 
      ['llm', 'agent', 'orchestration'].includes(node.type || '')
    );
    
    // AI 노드가 있으면 채팅 패널 자동 열기
    if (hasAINodes) {
      setShowAIChatPanel(true);
      
      // 실행 시작 메시지 추가
      const startMessage: ChatMessage = {
        role: 'assistant',
        content: `🚀 Starting workflow execution...\n\nNodes: ${nodes.length}\nEdges: ${edges.length}\nAI Nodes: ${nodes.filter(n => ['llm', 'agent', 'orchestration'].includes(n.type || '')).length}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, startMessage]);
    }
    
    try {
      // 워크플로우 데이터 변환 (타입 호환성)
      const workflowData = {
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type || 'unknown',
          position: n.position,
          data: n.data,
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          ...(e.sourceHandle && { sourceHandle: e.sourceHandle }),
          ...(e.targetHandle && { targetHandle: e.targetHandle }),
          data: e.data,
        })),
      } as any;
      
      if (onExecute) {
        await onExecute(workflowData);
      } else {
        // 스트리밍 모드로 실행하여 실시간 업데이트 받기
        await executeWorkflowStreaming(workflowData);
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      setValidationErrors([`Execution failed: ${error}`]);
    } finally {
      setIsExecuting(false);
    }
  }, [nodes, edges, readOnly, onExecute, executeWorkflowStreaming, validateWorkflow]);
  
  // AI 채팅 메시지 전송
  const handleSendChatMessage = useCallback(async (message: string) => {
    setIsSendingChat(true);
    
    // 사용자 메시지 추가
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    setChatMessages(prev => [...prev, userMessage]);
    
    try {
      // 워크플로우 데이터 변환
      const workflowData = {
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type || 'unknown',
          position: n.position,
          data: n.data,
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          ...(e.sourceHandle && { sourceHandle: e.sourceHandle }),
          ...(e.targetHandle && { targetHandle: e.targetHandle }),
          data: e.data,
        })),
      } as any;
      
      // 입력 데이터로 사용자 메시지 전달
      await executeWorkflowStreaming(workflowData, { user_input: message });
      
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to process message'}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSendingChat(false);
    }
  }, [nodes, edges, executeWorkflowStreaming]);
  
  // 실행 로그 초기화
  const handleClearLogs = useCallback(() => {
    setExecutionLogs([]);
    setChatMessages([]);
  }, []);
  
  // 노드/엣지 삭제
  const handleDelete = useCallback(() => {
    if (selectedNode) {
      setNodes(nds => nds.filter(node => node.id !== selectedNode.id));
      setSelectedNode(null);
      saveToHistory();
    }
    if (selectedEdge) {
      setEdges(eds => eds.filter(edge => edge.id !== selectedEdge.id));
      setSelectedEdge(null);
      saveToHistory();
    }
  }, [selectedNode, selectedEdge, setNodes, setEdges, saveToHistory]);
  
  // 복사/붙여넣기
  const handleCopy = useCallback(() => {
    if (selectedNode) {
      localStorage.setItem('copiedNode', JSON.stringify(selectedNode));
    }
  }, [selectedNode]);
  
  const handlePaste = useCallback(() => {
    const copiedNodeStr = localStorage.getItem('copiedNode');
    if (copiedNodeStr && reactFlowInstance) {
      const copiedNode = JSON.parse(copiedNodeStr);
      const newNode = {
        ...copiedNode,
        id: `${copiedNode.type}_${Date.now()}`,
        position: {
          x: copiedNode.position.x + 50,
          y: copiedNode.position.y + 50
        }
      };
      setNodes(nds => nds.concat(newNode));
      saveToHistory();
    }
  }, [reactFlowInstance, setNodes, saveToHistory]);
  
  // 노드 속성 업데이트
  const updateNodeData = useCallback((nodeId: string, newData: any) => {
    setNodes(nds => 
      nds.map(node => 
        node.id === nodeId 
          ? { ...node, data: { ...node.data, ...newData } }
          : node
      )
    );
    saveToHistory();
  }, [setNodes, saveToHistory]);
  
  return (
    <div className={`flex h-full ${className}`}>
      {/* 메인 편집 영역 */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          {/* 컨트롤 패널 */}
          <Controls />
          
          {/* 미니맵 */}
          {showMiniMap && (
            <MiniMap 
              nodeColor={(node) => {
                switch (node.type) {
                  case 'input': return '#10b981';
                  case 'output': return '#ef4444';
                  case 'llm': return '#3b82f6';
                  case 'tool': return '#8b5cf6';
                  case 'condition': return '#f59e0b';
                  case 'agent': return '#6366f1';
                  case 'orchestration': return '#ec4899';
                  default: return '#6b7280';
                }
              }}
            />
          )}
          
          {/* 배경 */}
          <Background 
            variant={showGrid ? BackgroundVariant.Dots : BackgroundVariant.Lines} 
            gap={20} 
            size={1} 
          />
          
          {/* 상단 툴바 */}
          <Panel position="top-left">
            <Card className="p-2">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={readOnly || isLoading}
                >
                  <Save className="w-4 h-4 mr-1" />
                  Save
                </Button>
                
                <Button
                  size="sm"
                  onClick={handleExecute}
                  disabled={readOnly || isExecuting || nodes.length === 0}
                >
                  <Play className="w-4 h-4 mr-1" />
                  {isExecuting ? 'Running...' : 'Run'}
                </Button>
                
                <Separator orientation="vertical" className="h-6" />
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={undo}
                  disabled={historyIndex <= 0}
                >
                  <Undo className="w-4 h-4" />
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={redo}
                  disabled={historyIndex >= history.length - 1}
                >
                  <Redo className="w-4 h-4" />
                </Button>
                
                <Separator orientation="vertical" className="h-6" />
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowGrid(!showGrid)}
                >
                  <Grid className="w-4 h-4" />
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowMiniMap(!showMiniMap)}
                >
                  {showMiniMap ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
                
                <Separator orientation="vertical" className="h-6" />
                
                {/* AI Chat Toggle Button */}
                <Button
                  size="sm"
                  variant={showAIChatPanel ? "default" : "outline"}
                  onClick={() => setShowAIChatPanel(!showAIChatPanel)}
                  className={showAIChatPanel ? "bg-blue-600 hover:bg-blue-700" : ""}
                >
                  <Bot className="w-4 h-4 mr-1" />
                  AI Chat
                  {chatMessages.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                      {chatMessages.length}
                    </Badge>
                  )}
                </Button>
              </div>
            </Card>
          </Panel>
          
          {/* 검증 오류 표시 */}
          {validationErrors.length > 0 && (
            <Panel position="top-right">
              <Card className="p-3 max-w-sm">
                <div className="text-sm font-medium text-red-600 mb-2">
                  Validation Errors
                </div>
                <ul className="text-xs text-red-500 space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </Card>
            </Panel>
          )}
          
          {/* 실행 결과 표시 */}
          {executionResults && (
            <Panel position="bottom-right">
              <Card className="p-3 max-w-md">
                <div className="text-sm font-medium mb-2">
                  Execution Results
                </div>
                <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                  {JSON.stringify(executionResults, null, 2)}
                </pre>
              </Card>
            </Panel>
          )}
        </ReactFlow>
      </div>
      
      {/* 사이드바 */}
      <div className="w-80 border-l bg-white">
        {/* 사이드바 탭 */}
        <div className="flex border-b">
          <button
            className={`flex-1 px-4 py-2 text-sm font-medium ${
              sidebarTab === 'palette' 
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setSidebarTab('palette')}
          >
            Palette
          </button>
          <button
            className={`flex-1 px-4 py-2 text-sm font-medium ${
              sidebarTab === 'properties' 
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setSidebarTab('properties')}
          >
            Properties
          </button>
          <button
            className={`flex-1 px-4 py-2 text-sm font-medium ${
              sidebarTab === 'settings' 
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setSidebarTab('settings')}
          >
            Settings
          </button>
        </div>
        
        {/* 사이드바 내용 */}
        <div className="h-full overflow-hidden">
          {sidebarTab === 'palette' && (
            <NodePalette 
              templates={nodeTemplates}
              onDragStart={(event, nodeType) => {
                event.dataTransfer.setData('application/reactflow', nodeType);
                event.dataTransfer.effectAllowed = 'move';
              }}
            />
          )}
          
          {sidebarTab === 'properties' && (
            <PropertyPanel
              selectedNode={selectedNode}
              selectedEdge={selectedEdge}
              onUpdateNode={updateNodeData}
              onUpdateEdge={(edgeId, newData) => {
                setEdges(eds => 
                  eds.map(edge => 
                    edge.id === edgeId 
                      ? { ...edge, data: { ...edge.data, ...newData } }
                      : edge
                  )
                );
              }}
            />
          )}
          
          {sidebarTab === 'settings' && (
            <WorkflowSettings
              workflow={{ nodes, edges }}
              onUpdate={(settings) => {
                // 워크플로우 설정 업데이트
                console.log('Workflow settings updated:', settings);
              }}
            />
          )}
        </div>
      </div>
      
      {/* AI Agent Chat Panel */}
      <AIAgentChatPanel
        isOpen={showAIChatPanel}
        onToggle={() => setShowAIChatPanel(!showAIChatPanel)}
        chatMessages={chatMessages}
        onSendMessage={handleSendChatMessage}
        isSending={isSendingChat || isExecuting}
        llmProvider="Workflow"
        llmModel={nodes.find(n => n.type === 'llm')?.data?.model || 'AI Agent'}
        executionLogs={executionLogs}
        onClearLogs={handleClearLogs}
        defaultWidth={35}
        minWidth={25}
        maxWidth={50}
      />
    </div>
  );
};

export const WorkflowEditor: React.FC<WorkflowEditorProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowEditorContent {...props} />
    </ReactFlowProvider>
  );
};