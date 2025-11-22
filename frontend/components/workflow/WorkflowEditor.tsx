'use client';

import React, { useCallback, useRef, useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
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
import '@/styles/workflow-execution.css';
import { BlockNode } from './nodes/BlockNode';
import { AgentNode } from './nodes/AgentNode';
import { ToolNode } from './nodes/ToolNode';
import { StartNode } from './nodes/StartNode';
import { EndNode } from './nodes/EndNode';
import { ConditionNode } from './nodes/ConditionNode';
import { TriggerNode } from './nodes/TriggerNode';
import { LoopNode } from './nodes/LoopNode';
import { ParallelNode } from './nodes/ParallelNode';
import { DelayNode } from './nodes/DelayNode';
import { HttpRequestNode } from './nodes/HttpRequestNode';
import SwitchNode from './nodes/SwitchNode';
import MergeNode from './nodes/MergeNode';
import CodeNode from './nodes/CodeNode';
import WebhookResponseNode from './nodes/WebhookResponseNode';
import SlackNode from './nodes/SlackNode';
import DiscordNode from './nodes/DiscordNode';
import EmailNode from './nodes/EmailNode';
import GoogleDriveNode from './nodes/GoogleDriveNode';
import S3Node from './nodes/S3Node';
import DatabaseNode from './nodes/DatabaseNode';
import ManagerAgentNode from './nodes/ManagerAgentNode';
import MemoryNode from './nodes/MemoryNode';
import ConsensusNode from './nodes/ConsensusNode';
import HumanApprovalNode from './nodes/HumanApprovalNode';
import { CustomEdge } from './edges/CustomEdge';
import { NodeConfigPanel } from './NodeConfigPanel';
import { NodeConfigurationPanel } from './NodeConfigurationPanel';
import { SimplifiedPropertiesPanel } from '../agent-builder/workflow/SimplifiedPropertiesPanel';
import { ExecutionDetailsPanel } from './ExecutionDetailsPanel';
import { ExecutionControlPanel } from './ExecutionControlPanel';
import { ExecutionStatusBadge } from './ExecutionStatusBadge';
import { NodeExecutionDetailsPanel } from './NodeExecutionDetailsPanel';
import { NodeDebugPanel } from './NodeDebugPanel';
import { NodeSearch } from './NodeSearch';
import { useWorkflowExecutionStream } from '@/hooks/useWorkflowExecutionStream';
import { useAIAgentChat } from '@/hooks/useAIAgentChat';
import { Button } from '@/components/ui/button';
import { Undo, Redo, ZoomIn, ZoomOut, Maximize, X, Bot } from 'lucide-react';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { logger } from '@/lib/logger';

// UUID v4 generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

interface WorkflowEditorProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: (nodes: Node[], edges: Edge[]) => void;
  readOnly?: boolean;
  highlightedNodeId?: string | null;
  onHighlightNode?: (nodeId: string | null) => void;
  // Execution visualization props
  executionMode?: boolean;
  executionId?: string;
  onExecutionStart?: () => void;
  onExecutionStop?: () => void;
}

const nodeTypes: NodeTypes = {
  block: BlockNode,
  agent: AgentNode,
  tool: ToolNode,
  start: StartNode,
  end: EndNode,
  condition: ConditionNode,
  trigger: TriggerNode,
  loop: LoopNode,
  parallel: ParallelNode,
  delay: DelayNode,
  http_request: HttpRequestNode,
  try_catch: ConditionNode, // Reuse ConditionNode for now
  switch: SwitchNode,
  merge: MergeNode,
  code: CodeNode,
  schedule_trigger: TriggerNode, // Reuse TriggerNode with different config
  webhook_trigger: TriggerNode, // Reuse TriggerNode with different config
  webhook_response: WebhookResponseNode,
  slack: SlackNode,
  discord: DiscordNode,
  email: EmailNode,
  google_drive: GoogleDriveNode,
  s3: S3Node,
  database: DatabaseNode,
  manager_agent: ManagerAgentNode,
  memory: MemoryNode,
  consensus: ConsensusNode,
  human_approval: HumanApprovalNode,
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
  highlightedNodeId,
  onHighlightNode,
  executionMode = false,
  executionId,
  onExecutionStart,
  onExecutionStop,
}: WorkflowEditorProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  
  // Execution visualization
  const {
    nodeStatuses,
    isConnected: isExecutionConnected,
    isComplete: isExecutionComplete,
    executionStatus,
    retryCount,
    maxRetries,
    connect: connectExecution,
    disconnect: disconnectExecution,
    reset: resetExecution,
  } = useWorkflowExecutionStream({
    workflowId: workflowId || '',
    executionId,
    enabled: executionMode && !!workflowId,
    onComplete: (status) => {
      logger.log('✅ Execution completed:', status);
      toast({
        title: status === 'completed' ? '✅ Execution Completed' : '❌ Execution Failed',
        description: status === 'completed' 
          ? 'Workflow executed successfully' 
          : 'Workflow execution failed',
        duration: 3000,
      });
    },
    onError: (error) => {
      logger.error('❌ Execution error:', error);
      toast({
        title: '❌ Execution Error',
        description: error,
        duration: 4000,
      });
    },
  });
  
  // Refs for callbacks to avoid circular dependencies
  const handleTriggerActionRef = useRef<(nodeId: string) => void>(() => {});
  const handleConfigureTriggerRef = useRef<(nodeId: string) => void>(() => {});
  const handleCopyWebhookURLRef = useRef<(nodeId: string) => void>(() => {});
  
  // Initialize nodes with trigger callbacks and disabled styling
  const initializeNodes = useCallback((nodesToInit: Node[]) => {
    return nodesToInit.map(node => {
      const baseNode = {
        ...node,
        // Apply disabled styling
        className: node.data?.disabled 
          ? 'opacity-50 grayscale pointer-events-auto' 
          : node.className,
      };

      if (node.type === 'trigger') {
        return {
          ...baseNode,
          data: {
            ...baseNode.data,
            onTrigger: () => handleTriggerActionRef.current(node.id),
            onConfigure: () => handleConfigureTriggerRef.current(node.id),
            onCopyWebhook: () => handleCopyWebhookURLRef.current(node.id),
          },
        };
      }
      return baseNode;
    });
  }, []);
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  // Track if we've initialized to prevent re-initialization loops
  const initializedRef = useRef(false);
  
  // Update node styles based on execution status
  useEffect(() => {
    if (!executionMode || Object.keys(nodeStatuses).length === 0) return;
    
    setNodes((nds) =>
      nds.map((node) => {
        const status = nodeStatuses[node.id];
        if (!status) return node;
        
        // Apply status-based styling
        let className = 'node-idle';
        switch (status.status) {
          case 'pending':
            className = 'node-pending';
            break;
          case 'running':
            className = 'node-running';
            break;
          case 'success':
            className = 'node-success';
            break;
          case 'failed':
            className = 'node-error';
            break;
          case 'skipped':
            className = 'node-skipped';
            break;
        }
        
        return {
          ...node,
          className,
          data: {
            ...node.data,
            executionStatus: status.status,
            executionError: status.error,
            executionOutput: status.output,
            startTime: status.startTime,
            endTime: status.endTime,
          },
        };
      })
    );
  }, [nodeStatuses, executionMode, setNodes]);
  
  // Update edge styles based on execution status
  useEffect(() => {
    if (!executionMode || Object.keys(nodeStatuses).length === 0) return;
    
    setEdges((eds) =>
      eds.map((edge) => {
        const sourceStatus = nodeStatuses[edge.source];
        const targetStatus = nodeStatuses[edge.target];
        
        // Determine edge execution state
        let isExecuting = false;
        let executionStatus: string | undefined;
        
        if (sourceStatus?.status === 'running' || targetStatus?.status === 'running') {
          isExecuting = true;
        } else if (sourceStatus?.status === 'success' && targetStatus?.status === 'success') {
          executionStatus = 'success';
        } else if (sourceStatus?.status === 'failed' || targetStatus?.status === 'failed') {
          executionStatus = 'error';
        }
        
        return {
          ...edge,
          data: {
            ...edge.data,
            isExecuting,
            executionStatus,
          },
          animated: isExecuting, // Built-in ReactFlow animation
        };
      })
    );
  }, [nodeStatuses, executionMode, setEdges]);
  
  // Update nodes and edges when initialNodes/initialEdges change
  useEffect(() => {
    // Only initialize once or when explicitly changed from parent
    if (initializedRef.current && initialNodes.length === nodes.length) {
      return;
    }
    
    logger.log('🔄 WorkflowEditor: Updating nodes from initialNodes', {
      initialNodesCount: initialNodes.length,
      initialEdgesCount: initialEdges.length,
      currentNodesCount: nodes.length,
    });
    
    if (initialNodes.length > 0) {
      const initialized = initializeNodes(initialNodes);
      setNodes(initialized);
      initializedRef.current = true;
    }
    
    if (initialEdges.length > 0) {
      setEdges(initialEdges);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNodes, initialEdges]);
  
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedExecutionNode, setSelectedExecutionNode] = useState<Node | null>(null);
  const [debugNodeId, setDebugNodeId] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [showAIChatPanel, setShowAIChatPanel] = useState(true); // TODO: Will be auto-detected
  const [aiAgentNodes, setAiAgentNodes] = useState<Node[]>([{ id: 'mock' } as Node]); // TODO: Will be auto-detected
  const [selectedAIAgent, setSelectedAIAgent] = useState<Node | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [isMounted, setIsMounted] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Prevent hydration mismatch by only rendering portal on client
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // WebSocket-based AI Agent chat
  const {
    messages: chatMessages,
    sendMessage: sendChatMessage,
    clearMessages: clearChatMessages,
    isConnected: isChatConnected,
    isProcessing: isSending,
    error: chatError,
    reconnect: reconnectChat,
  } = useAIAgentChat({
    sessionId: `workflow-${workflowId || 'new'}-${selectedAIAgent?.id || 'default'}`,
    nodeId: selectedAIAgent?.id || 'default',
    config: {
      provider: selectedAIAgent?.data?.parameters?.provider || 'ollama',
      model: selectedAIAgent?.data?.parameters?.model || 'llama3.3:70b',
      system_prompt: selectedAIAgent?.data?.parameters?.system_prompt || '',
      temperature: selectedAIAgent?.data?.parameters?.temperature || 0.7,
      max_tokens: selectedAIAgent?.data?.parameters?.max_tokens || 1000,
      enable_memory: selectedAIAgent?.data?.parameters?.enable_memory ?? true,
      memory_type: selectedAIAgent?.data?.parameters?.memory_type || 'short_term',
    },
    onError: (error) => {
      toast({
        title: '❌ Chat Error',
        description: error,
        variant: 'destructive',
        duration: 5000,
      });
    },
  });
  
  // Check for AI Agent tools and auto-show chat panel
  useEffect(() => {
    console.log('🔍 Checking for AI Agent tools...', {
      totalNodes: nodes.length,
      nodeTypes: nodes.map(n => ({ 
        id: n.id, 
        type: n.type, 
        label: n.data?.label,
        name: n.data?.name,
        tool_id: n.data?.tool_id,
        tool_name: n.data?.tool_name,
        category: n.data?.category,
        blockType: n.data?.blockType,
        nodeType: n.data?.nodeType
      }))
    });
    
    const aiAgents = nodes.filter(node => {
      // Get all possible identifiers
      const label = (node.data?.label || node.data?.name || '').toLowerCase();
      const toolId = (node.data?.tool_id || node.data?.id || '').toLowerCase();
      const toolName = (node.data?.tool_name || '').toLowerCase();
      const blockType = (node.data?.blockType || '').toLowerCase();
      const nodeType = (node.data?.nodeType || '').toLowerCase();
      const category = (node.data?.category || '').toLowerCase();
      
      // Check multiple conditions for AI Agent detection
      const isAIAgent = 
        // Direct type checks
        node.data?.type === 'tool_ai_agent' || 
        node.data?.type === 'ai_agent' ||
        nodeType === 'ai_agent' ||
        blockType === 'ai_agent' ||
        // Tool ID checks
        toolId === 'ai_agent' ||
        toolId === 'ai-agent' ||
        toolId.includes('ai_agent') ||
        toolId.includes('ai-agent') ||
        // Tool name checks
        toolName === 'ai agent' ||
        toolName === 'ai-agent' ||
        toolName.includes('ai agent') ||
        toolName.includes('ai-agent') ||
        // Label checks
        label === 'ai agent' ||
        label === 'ai-agent' ||
        label.includes('ai agent') ||
        label.includes('ai-agent') ||
        // Category check for tool nodes
        (node.type === 'tool' && category === 'ai') ||
        (node.type === 'tool' && category.includes('ai'));
      
      if (isAIAgent) {
        console.log('✅ Found AI Agent:', {
          id: node.id,
          type: node.type,
          label,
          toolId,
          toolName,
          category,
          nodeType,
          blockType
        });
      }
      return isAIAgent;
    });
    
    console.log('🤖 AI Agents found:', aiAgents.length, aiAgents);
    
    setAiAgentNodes(aiAgents);
    
    // Auto-show chat panel if AI Agent tools exist (both edit and view mode)
    if (aiAgents.length > 0) {
      console.log('✅ Showing AI Agent chat panel');
      setShowAIChatPanel(true);
      // Auto-select first AI Agent if none selected
      if (!selectedAIAgent) {
        console.log('🎯 Auto-selecting first AI Agent:', aiAgents[0].id);
        setSelectedAIAgent(aiAgents[0]);
      }
    } else {
      console.log('❌ No AI Agents found, hiding chat panel');
      setShowAIChatPanel(false);
      setSelectedAIAgent(null);
    }
  }, [nodes, selectedAIAgent]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Handle node highlighting
  useEffect(() => {
    if (!highlightedNodeId || !reactFlowInstance) return;
    
    // Find the node
    const node = nodes.find(n => n.id === highlightedNodeId);
    if (!node) return;
    
    // Zoom to the node
    reactFlowInstance.fitView({
      nodes: [{ id: highlightedNodeId }],
      duration: 500,
      padding: 0.5,
    });
    
    // Update node style to highlight
    setNodes((nds) =>
      nds.map((n) =>
        n.id === highlightedNodeId
          ? {
              ...n,
              style: {
                ...n.style,
                border: '3px solid #ef4444',
                boxShadow: '0 0 20px rgba(239, 68, 68, 0.5)',
              },
            }
          : n
      )
    );
    
    // Remove highlight after 3 seconds
    const timeout = setTimeout(() => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === highlightedNodeId
            ? {
                ...n,
                style: {
                  ...n.style,
                  border: undefined,
                  boxShadow: undefined,
                },
              }
            : n
        )
      );
      onHighlightNode?.(null);
    }, 3000);
    
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightedNodeId, reactFlowInstance]);
  const [showExecutionDetails, setShowExecutionDetails] = useState(false);
  const [executionData, setExecutionData] = useState<any>(null);

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
    nodes: [],
    edges: [],
  });

  // Sync history state with nodes and edges
  useEffect(() => {
    if (!readOnly) {
      setHistoryState({ nodes, edges });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, readOnly]);

  // Sync nodes changes to parent (debounced to prevent loops)
  const nodesChangeTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  useEffect(() => {
    if (onNodesChangeProp && !readOnly && initializedRef.current) {
      // Clear previous timeout
      if (nodesChangeTimeoutRef.current) {
        clearTimeout(nodesChangeTimeoutRef.current);
      }
      
      // Debounce the callback to prevent rapid updates
      nodesChangeTimeoutRef.current = setTimeout(() => {
        logger.log('🔄 Nodes changed:', nodes.length);
        onNodesChangeProp(nodes);
      }, 100);
    }
    
    return () => {
      if (nodesChangeTimeoutRef.current) {
        clearTimeout(nodesChangeTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, readOnly]);

  // Sync edges changes to parent (debounced to prevent loops)
  const edgesChangeTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  useEffect(() => {
    if (onEdgesChangeProp && !readOnly && initializedRef.current) {
      // Clear previous timeout
      if (edgesChangeTimeoutRef.current) {
        clearTimeout(edgesChangeTimeoutRef.current);
      }
      
      // Debounce the callback to prevent rapid updates
      edgesChangeTimeoutRef.current = setTimeout(() => {
        logger.log('🔗 Edges changed:', edges.length);
        onEdgesChangeProp(edges);
      }, 100);
    }
    
    return () => {
      if (edgesChangeTimeoutRef.current) {
        clearTimeout(edgesChangeTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [edges, readOnly]);

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
      // Search (Ctrl+F)
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        setSearchOpen(true);
        return;
      }

      if (readOnly) return;

      // Undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } 
      // Redo
      else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [readOnly, handleUndo, handleRedo]);

  // Handle node selection from search
  const handleSelectNode = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node && reactFlowInstance) {
      // Zoom to node
      reactFlowInstance.fitView({
        nodes: [{ id: nodeId }],
        duration: 500,
        padding: 0.5,
      });
      
      // Select node
      setNodes(nds => nds.map(n => ({
        ...n,
        selected: n.id === nodeId
      })));
      
      // Highlight node temporarily
      setTimeout(() => {
        setNodes(nds => nds.map(n => ({
          ...n,
          selected: false
        })));
      }, 2000);
    }
  }, [nodes, reactFlowInstance, setNodes]);

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

  // Handle nodes change with delete confirmation
  const handleNodesChangeWithConfirm = useCallback(
    (changes: any) => {
      if (readOnly) {
        onNodesChange(changes);
        return;
      }

      // Check if any changes are removals
      const removeChanges = changes.filter((change: any) => change.type === 'remove');
      
      if (removeChanges.length > 0) {
        const nodesToDelete = removeChanges.map((change: any) => 
          nodes.find(n => n.id === change.id)
        ).filter(Boolean);
        
        const totalConnections = nodesToDelete.reduce((count: number, node: any) => {
          return count + edges.filter(e => e.source === node.id || e.target === node.id).length;
        }, 0);
        
        const confirmed = window.confirm(
          `Delete ${nodesToDelete.length} node${nodesToDelete.length !== 1 ? 's' : ''}?\n\n` +
          `This will also remove ${totalConnections} connected edge${totalConnections !== 1 ? 's' : ''}.`
        );
        
        if (!confirmed) {
          return; // Cancel deletion
        }
        
        toast({
          title: '🗑️ Nodes Deleted',
          description: `Removed ${nodesToDelete.length} node${nodesToDelete.length !== 1 ? 's' : ''} and ${totalConnections} connection${totalConnections !== 1 ? 's' : ''}`,
          duration: 2000,
        });
      }
      
      onNodesChange(changes);
      if (onNodesChangeProp) {
        const updatedNodes = nodes;
        onNodesChangeProp(updatedNodes);
      }
    },
    [readOnly, nodes, edges, onNodesChange, onNodesChangeProp, toast]
  );

  // Handle new connections
  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly) return;
      
      logger.log('🔗 Manual connection created:', connection);
      
      const newEdge = {
        ...connection,
        type: 'custom',
        id: generateUUID(),
      };
      
      setEdges((eds) => {
        const updatedEdges = addEdge(newEdge, eds);
        logger.log('📊 Total edges after manual connection:', updatedEdges.length);
        return updatedEdges;
      });
    },
    [readOnly, setEdges]
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
      else if (block.nodeType === 'control') {
        // Map control types to specific node types
        if (block.type === 'loop') nodeType = 'loop';
        else if (block.type === 'parallel') nodeType = 'parallel';
        else if (block.type === 'delay') nodeType = 'delay';
        else if (block.type === 'try_catch') nodeType = 'try_catch';
        else if (block.type === 'switch') nodeType = 'switch';
        else if (block.type === 'merge') nodeType = 'merge';
        else nodeType = 'condition'; // Default to condition for unknown control types
      }

      const nodeId = generateUUID();
      const newNode: Node = {
        id: nodeId,
        type: nodeType,
        position,
        data: {
          ...block,
          label: block.name,
          // Add trigger callbacks
          ...(nodeType === 'trigger' && {
            onTrigger: () => handleTriggerActionRef.current(nodeId),
            onConfigure: () => handleConfigureTriggerRef.current(nodeId),
            onCopyWebhook: () => handleCopyWebhookURLRef.current(nodeId),
          }),
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
    console.log('🖱️ Node clicked:', {
      nodeId: node.id,
      nodeType: node.type,
      executionMode,
      readOnly,
      hasStatus: !!nodeStatuses[node.id]
    });
    
    if (executionMode && nodeStatuses[node.id]) {
      // In execution mode, show debug panel
      setDebugNodeId(node.id);
    } else if (!readOnly) {
      // In edit mode, show config panel
      console.log('✅ Setting selected node:', node);
      setSelectedNode(node);
    } else {
      console.log('⚠️ Node click ignored - readOnly:', readOnly);
    }
  }, [executionMode, nodeStatuses, readOnly]);

  // Handle trigger actions
  const handleTriggerAction = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    toast({
      title: '⚡ Trigger Activated',
      description: `Manually triggered: ${node.data?.name || 'Trigger'}`,
      duration: 2000,
    });

    // Update node to show executing state
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === nodeId) {
          return {
            ...n,
            data: {
              ...n.data,
              isExecuting: true,
              executionStatus: 'running',
            },
          };
        }
        return n;
      })
    );

    // Simulate execution completion after 2 seconds
    setTimeout(() => {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === nodeId) {
            return {
              ...n,
              data: {
                ...n.data,
                isExecuting: false,
                executionStatus: 'success',
              },
            };
          }
          return n;
        })
      );

      toast({
        title: '✅ Trigger Complete',
        description: 'Workflow execution finished successfully',
        duration: 2000,
      });

      // Clear status after 3 seconds
      setTimeout(() => {
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === nodeId) {
              return {
                ...n,
                data: {
                  ...n.data,
                  executionStatus: undefined,
                },
              };
            }
            return n;
          })
        );
      }, 3000);
    }, 2000);
  }, [nodes, setNodes, toast]);

  const handleConfigureTrigger = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      toast({
        title: '⚙️ Configure Trigger',
        description: 'Configuration panel opened',
        duration: 1500,
      });
    }
  }, [nodes, toast]);

  const handleCopyWebhookURL = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    const webhookURL = `${window.location.origin}/api/webhooks/${nodeId}`;
    
    navigator.clipboard.writeText(webhookURL).then(() => {
      toast({
        title: '📋 Webhook URL Copied',
        description: 'URL copied to clipboard',
        duration: 2000,
      });
    }).catch(() => {
      toast({
        title: '❌ Copy Failed',
        description: 'Failed to copy URL to clipboard',
        duration: 2000,
      });
    });
  }, [nodes, toast]);

  // Update refs
  useEffect(() => {
    handleTriggerActionRef.current = handleTriggerAction;
    handleConfigureTriggerRef.current = handleConfigureTrigger;
    handleCopyWebhookURLRef.current = handleCopyWebhookURL;
  }, [handleTriggerAction, handleConfigureTrigger, handleCopyWebhookURL]);

  // Handle node drag stop - auto connect to nearby nodes
  const onNodeDragStop = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (readOnly) return;

      // Find nearby nodes within connection range
      const connectionRange = 150; // pixels
      const sourceNode = node;
      let newEdgesCreated: Edge[] = [];

      // Helper function to check if node can be a source (has output)
      const canBeSource = (nodeType: string) => {
        return !['end'].includes(nodeType);
      };

      // Helper function to check if node can be a target (has input)
      const canBeTarget = (nodeType: string) => {
        return !['start', 'trigger'].includes(nodeType);
      };

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
            // Determine connection direction based on vertical position and node types
            let newConnection: Connection | null = null;
            
            if (sourceNode.position.y < targetNode.position.y) {
              // Source is above target
              if (canBeSource(sourceNode.type || '') && canBeTarget(targetNode.type || '')) {
                newConnection = {
                  source: sourceNode.id,
                  target: targetNode.id,
                  sourceHandle: 'output',
                  targetHandle: 'input',
                };
              }
            } else {
              // Source is below target
              if (canBeSource(targetNode.type || '') && canBeTarget(sourceNode.type || '')) {
                newConnection = {
                  source: targetNode.id,
                  target: sourceNode.id,
                  sourceHandle: 'output',
                  targetHandle: 'input',
                };
              }
            }

            // Add the connection if valid
            if (newConnection) {
              const newEdge = {
                ...newConnection,
                type: 'custom',
                id: generateUUID(),
              } as Edge;

              newEdgesCreated.push(newEdge);
            }
          }
        }
      });

      // Update edges if any new connections were created
      if (newEdgesCreated.length > 0) {
        logger.log('✨ Auto-connection created:', newEdgesCreated.length, 'new edge(s)');
        
        setEdges((eds) => {
          const updatedEdges = [...eds, ...newEdgesCreated];
          logger.log('📊 Total edges after auto-connection:', updatedEdges.length);
          
          // Show toast notification
          toast({
            title: '✨ Auto-Connected',
            description: `${newEdgesCreated.length} connection${newEdgesCreated.length > 1 ? 's' : ''} created`,
            duration: 2000,
          });
          
          // Notify parent component with updated edges
          if (onEdgesChangeProp) {
            // Use setTimeout to ensure state is updated before callback
            setTimeout(() => {
              logger.log('📤 Notifying parent of edge changes');
              onEdgesChangeProp(updatedEdges);
            }, 0);
          }
          
          return updatedEdges;
        });
      }
    },
    [readOnly, nodes, edges, setEdges, onEdgesChangeProp]
  );

  // Handle chat message send (WebSocket-based)
  const handleSendChatMessage = useCallback(() => {
    if (!chatInput.trim() || isSending || !selectedAIAgent) return;

    const currentInput = chatInput.trim();
    setChatInput('');
    
    console.log('🚀 Sending message via WebSocket:', {
      message_length: currentInput.length,
      provider: selectedAIAgent.data?.parameters?.provider || 'ollama',
      model: selectedAIAgent.data?.parameters?.model || 'llama3.3:70b',
    });

    sendChatMessage(currentInput);
  }, [chatInput, isSending, selectedAIAgent, sendChatMessage]);

  const handleChatKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChatMessage();
    }
  }, [handleSendChatMessage]);

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
    const nodeToDelete = nodes.find(n => n.id === nodeId);
    const connectedEdges = edges.filter(e => e.source === nodeId || e.target === nodeId);
    
    const confirmed = window.confirm(
      `Delete "${nodeToDelete?.data?.label || nodeToDelete?.data?.name || 'this node'}"?\n\n` +
      `This will also remove ${connectedEdges.length} connected edge${connectedEdges.length !== 1 ? 's' : ''}.`
    );
    
    if (confirmed) {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
      
      toast({
        title: '🗑️ Node Deleted',
        description: `Removed node and ${connectedEdges.length} connection${connectedEdges.length !== 1 ? 's' : ''}`,
        duration: 2000,
      });
    }
  }, [nodes, edges, setNodes, setEdges, toast]);

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
        onNodesChange={handleNodesChangeWithConfirm}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
        deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
        multiSelectionKeyCode={readOnly ? null : 'Shift'}
        snapToGrid={true}
        snapGrid={[15, 15]}
        defaultEdgeOptions={{
          type: 'custom',
          animated: true,
        }}
      >
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          nodeColor={(node) => {
            if (node.type === 'start') return '#10b981'; // green
            if (node.type === 'end') return '#ef4444'; // red
            if (node.type === 'agent') return '#a855f7'; // purple
            if (node.type === 'condition') return '#f59e0b'; // amber
            if (node.type === 'trigger') return '#eab308'; // yellow
            if (node.type === 'block') return '#3b82f6'; // blue
            if (node.type === 'loop') return '#8b5cf6'; // violet
            if (node.type === 'parallel') return '#06b6d4'; // cyan
            if (node.type === 'delay') return '#64748b'; // slate
            if (node.type === 'try_catch') return '#dc2626'; // red
            if (node.type === 'switch') return '#f97316'; // orange
            if (node.type === 'merge') return '#14b8a6'; // teal
            return '#94a3b8'; // gray
          }}
          nodeBorderRadius={8}
          maskColor="rgba(0, 0, 0, 0.1)"
          zoomable
          pannable
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        
        {!readOnly && (
          <Panel position="top-right" className="flex gap-2">
            <div className="flex gap-1 bg-background/95 backdrop-blur-sm border rounded-lg p-1 shadow-lg">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleUndo}
                disabled={!canUndo}
                title="Undo (Ctrl+Z)"
                className={cn(
                  'transition-all',
                  canUndo ? 'hover:bg-blue-100 hover:text-blue-600' : 'opacity-40'
                )}
              >
                <Undo className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRedo}
                disabled={!canRedo}
                title="Redo (Ctrl+Y)"
                className={cn(
                  'transition-all',
                  canRedo ? 'hover:bg-blue-100 hover:text-blue-600' : 'opacity-40'
                )}
              >
                <Redo className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex gap-1 bg-background/95 backdrop-blur-sm border rounded-lg p-1 shadow-lg">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.zoomIn()}
                title="Zoom In (+)"
                className="hover:bg-blue-100 hover:text-blue-600 transition-all"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.zoomOut()}
                title="Zoom Out (-)"
                className="hover:bg-blue-100 hover:text-blue-600 transition-all"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => reactFlowInstance?.fitView()}
                title="Fit View (F)"
                className="hover:bg-blue-100 hover:text-blue-600 transition-all"
              >
                <Maximize className="h-4 w-4" />
              </Button>
            </div>
          </Panel>
        )}
      </ReactFlow>
      </div>
      
      {/* Node Configuration Panel */}
      {(() => {
        const shouldShow = selectedNode && !readOnly && !showExecutionDetails;
        console.log('🎨 Properties Panel render check:', {
          hasSelectedNode: !!selectedNode,
          selectedNodeId: selectedNode?.id,
          readOnly,
          showExecutionDetails,
          shouldShow
        });
        return shouldShow;
      })() && (
        <SimplifiedPropertiesPanel
          node={selectedNode}
          isOpen={true}
          onClose={() => {
            console.log('🚪 Closing properties panel');
            setSelectedNode(null);
          }}
          onUpdate={(nodeId, updates) => {
            // Check if this is a delete operation
            if ((updates as any)._delete) {
              setNodes((nds) => nds.filter((n) => n.id !== nodeId));
              setEdges((eds) =>
                eds.filter((e) => e.source !== nodeId && e.target !== nodeId)
              );
              setSelectedNode(null);
              return;
            }
            
            handleNodeUpdate(nodeId, updates);
          }}
        />
      )}
      
      {/* Old NodeConfigurationPanel - Keeping for reference but hidden */}
      {false && selectedNode && !readOnly && !showExecutionDetails && (
        <NodeConfigurationPanel
          node={{
            id: selectedNode.id,
            type: selectedNode.type || 'custom',
            label: selectedNode.data?.name || selectedNode.data?.label || 'Node',
            tool_id: selectedNode.data?.tool_id || selectedNode.data?.type || selectedNode.data?.blockType,
            config: selectedNode.data?.config
          }}
          onClose={() => setSelectedNode(null)}
          onSave={(config) => {
            handleNodeUpdate(selectedNode.id, { config });
            setSelectedNode(null);
          }}
          onTest={async (config) => {
            const response = await fetch('/api/v1/agent-builder/tool-execution/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tool_id: selectedNode.data?.tool_id || selectedNode.data?.type || selectedNode.data?.blockType,
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

      {/* Execution Details Panel */}
      {showExecutionDetails && executionData && (
        <ExecutionDetailsPanel
          executionId={executionData.executionId}
          workflowName={executionData.workflowName}
          status={executionData.status}
          startTime={executionData.startTime}
          endTime={executionData.endTime}
          totalDuration={executionData.totalDuration}
          nodeExecutions={executionData.nodeExecutions || []}
          onClose={() => setShowExecutionDetails(false)}
        />
      )}
      
      {/* Execution Control Panel - Left side when AI Agent exists */}
      {executionMode && workflowId && typeof window !== 'undefined' && createPortal(
        <div
          id="execution-control-panel"
          style={{
            position: 'fixed',
            bottom: '0px',
            left: '0px',
            height: 'clamp(300px, 35vh, 450px)',
            width: showAIChatPanel && aiAgentNodes.length > 0 ? 'calc(50% - 1px)' : '100%',
            zIndex: 99999,
            background: 'linear-gradient(to top, rgba(15, 23, 42, 0.98), rgba(15, 23, 42, 0.95))',
            backdropFilter: 'blur(20px) saturate(180%)',
            WebkitBackdropFilter: 'blur(20px) saturate(180%)',
            borderTop: '1px solid rgba(148, 163, 184, 0.1)',
            borderRight: showAIChatPanel && aiAgentNodes.length > 0 ? '1px solid rgba(148, 163, 184, 0.1)' : 'none',
            boxShadow: '0 -4px 24px rgba(0, 0, 0, 0.12), 0 -1px 3px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <div style={{ padding: '16px', flex: 1, overflow: 'auto' }}>
            <ExecutionControlPanel
              nodeStatuses={nodeStatuses}
              isConnected={isExecutionConnected}
              isComplete={isExecutionComplete}
              executionStatus={executionStatus}
              retryCount={retryCount}
              maxRetries={maxRetries}
              onStart={onExecutionStart}
              onStop={onExecutionStop}
              onReset={() => {
                resetExecution();
                setSelectedExecutionNode(null);
                // Reset node styles
                setNodes((nds) =>
                  nds.map((node) => ({
                    ...node,
                    className: 'node-idle',
                    data: {
                      ...node.data,
                      executionStatus: undefined,
                      executionError: undefined,
                      executionOutput: undefined,
                    },
                  }))
                );
              }}
            />
          </div>
        </div>,
        document.body
      )}
      
      {/* Node Execution Details Panel */}
      {selectedExecutionNode && nodeStatuses[selectedExecutionNode.id] && (
        <NodeExecutionDetailsPanel
          nodeId={selectedExecutionNode.id}
          nodeName={selectedExecutionNode.data?.label || selectedExecutionNode.data?.name || 'Node'}
          status={nodeStatuses[selectedExecutionNode.id].status}
          startTime={nodeStatuses[selectedExecutionNode.id].startTime}
          endTime={nodeStatuses[selectedExecutionNode.id].endTime}
          error={nodeStatuses[selectedExecutionNode.id].error}
          input={selectedExecutionNode.data?.input}
          output={nodeStatuses[selectedExecutionNode.id].output}
          logs={selectedExecutionNode.data?.logs || []}
          onClose={() => setSelectedExecutionNode(null)}
        />
      )}

      {/* Node Debug Panel (Floating) */}
      {debugNodeId && nodeStatuses[debugNodeId] && (
        <div className="absolute top-4 right-4 z-50">
          <NodeDebugPanel
            nodeId={debugNodeId}
            nodeName={nodes.find(n => n.id === debugNodeId)?.data?.name || 'Node'}
            executionData={{
              input: nodeStatuses[debugNodeId].input || {},
              output: nodeStatuses[debugNodeId].output,
              error: nodeStatuses[debugNodeId].error,
              duration: nodeStatuses[debugNodeId].endTime && nodeStatuses[debugNodeId].startTime
                ? nodeStatuses[debugNodeId].endTime! - nodeStatuses[debugNodeId].startTime!
                : 0,
              timestamp: new Date(nodeStatuses[debugNodeId].startTime || Date.now()).toISOString(),
              status: nodeStatuses[debugNodeId].status
            }}
            onClose={() => setDebugNodeId(null)}
          />
        </div>
      )}

      {/* Node Search Dialog */}
      <NodeSearch
        nodes={nodes}
        open={searchOpen}
        onOpenChange={setSearchOpen}
        onSelectNode={handleSelectNode}
      />

      {/* AI Agent Chat Panel - Auto-shown when AI Agent tools exist (Edit & View mode) */}
      {isMounted && showAIChatPanel && aiAgentNodes.length > 0 && createPortal(
        <div
          id="ai-agent-chat-panel"
          style={{
            position: 'fixed',
            bottom: '0px',
            right: '0px',
            height: 'clamp(300px, 35vh, 450px)',
            width: 'clamp(400px, 50%, 900px)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 99999,
            background: 'linear-gradient(to top, rgba(17, 24, 39, 0.98), rgba(17, 24, 39, 0.95))',
            backdropFilter: 'blur(20px) saturate(180%)',
            WebkitBackdropFilter: 'blur(20px) saturate(180%)',
            borderTop: '1px solid rgba(59, 130, 246, 0.2)',
            borderLeft: '1px solid rgba(59, 130, 246, 0.2)',
            boxShadow: '-4px -4px 24px rgba(0, 0, 0, 0.12), 0 -1px 3px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(59, 130, 246, 0.1)',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          {/* Chat Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-md">
                <Bot className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm">
                    {selectedAIAgent?.data?.label || selectedAIAgent?.data?.name || 'AI Agent Chat'}
                  </h3>
                  <div className={`w-2 h-2 rounded-full ${isChatConnected ? 'bg-green-500' : 'bg-red-500'}`} title={isChatConnected ? 'Connected' : 'Disconnected'} />
                </div>
                <p className="text-xs text-muted-foreground">
                  {selectedAIAgent?.data?.parameters?.provider || 'ollama'} • {selectedAIAgent?.data?.parameters?.model || 'llama3.3:70b'}
                  {!isChatConnected && ' • Disconnected'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {aiAgentNodes.length > 1 && (
                <select
                  value={selectedAIAgent?.id || ''}
                  onChange={(e) => {
                    const node = aiAgentNodes.find(n => n.id === e.target.value);
                    if (node) {
                      setSelectedAIAgent(node);
                      clearChatMessages();
                    }
                  }}
                  className="text-xs border rounded px-2 py-1 bg-background"
                >
                  {aiAgentNodes.map((node) => (
                    <option key={node.id} value={node.id}>
                      {node.data?.label || node.data?.name || 'AI Agent'}
                    </option>
                  ))}
                </select>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearChatMessages}
                className="h-8 text-xs"
                disabled={chatMessages.length === 0}
              >
                Clear
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAIChatPanel(false)}
                className="h-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-auto p-4 space-y-4">
            {!isChatConnected && chatError && (
              <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-red-700 dark:text-red-300 font-medium">Connection Lost</p>
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">{chatError}</p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={reconnectChat}
                    className="text-xs"
                  >
                    Reconnect
                  </Button>
                </div>
              </div>
            )}
            {chatMessages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                  <p className="text-sm text-muted-foreground">
                    Start a conversation with {selectedAIAgent?.data?.label || 'AI Agent'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {isChatConnected ? 'Type your message below to begin' : 'Connecting to chat server...'}
                  </p>
                </div>
              </div>
            ) : (
              <>
                {chatMessages.map((msg, idx) => {
                  const isError = msg.role === 'assistant' && msg.content.startsWith('❌ Error:');
                  return (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                            : isError
                            ? 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800'
                            : 'bg-muted border'
                        }`}
                      >
                        <p className={`text-sm whitespace-pre-wrap break-words ${isError ? 'text-red-700 dark:text-red-300' : ''}`}>
                          {msg.content}
                        </p>
                        <p className={`text-xs mt-1 ${
                          msg.role === 'user' 
                            ? 'text-blue-100' 
                            : isError 
                            ? 'text-red-500 dark:text-red-400' 
                            : 'text-muted-foreground'
                        }`}>
                          {msg.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {isSending && (
                  <div className="flex justify-start">
                    <div className="bg-muted border rounded-2xl px-4 py-2.5">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </>
            )}
          </div>

          {/* Chat Input */}
          <div className="border-t bg-muted/20 p-4">
            <div className="flex gap-3 max-w-4xl mx-auto">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                placeholder={isChatConnected ? "Type your message..." : "Connecting..."}
                disabled={isSending || !isChatConnected}
                className="flex-1 px-4 py-2.5 border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <Button
                onClick={handleSendChatMessage}
                disabled={!chatInput.trim() || isSending || !isChatConnected}
                className="px-6 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
              >
                {isSending ? (
                  <div className="animate-spin">⏳</div>
                ) : (
                  'Send'
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>,
        document.body
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
