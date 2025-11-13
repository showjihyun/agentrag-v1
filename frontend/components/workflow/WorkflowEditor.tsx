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
import { ExecutionDetailsPanel } from './ExecutionDetailsPanel';
import { Button } from '@/components/ui/button';
import { Undo, Redo, ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

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
}

const nodeTypes: NodeTypes = {
  block: BlockNode,
  agent: AgentNode,
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
}: WorkflowEditorProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  // Initialize nodes with trigger callbacks
  const [initializedNodes] = useState(() => 
    initialNodes.map(node => {
      if (node.type === 'trigger') {
        return {
          ...node,
          data: {
            ...node.data,
            onTrigger: () => handleTriggerActionRef.current(node.id),
            onConfigure: () => handleConfigureTriggerRef.current(node.id),
            onCopyWebhook: () => handleCopyWebhookURLRef.current(node.id),
          },
        };
      }
      return node;
    })
  );
  
  const [nodes, setNodes, onNodesChange] = useNodesState(initializedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showExecutionDetails, setShowExecutionDetails] = useState(false);
  const [executionData, setExecutionData] = useState<any>(null);
  
  // Refs for callbacks to avoid circular dependencies
  const handleTriggerActionRef = useRef<(nodeId: string) => void>(() => {});
  const handleConfigureTriggerRef = useRef<(nodeId: string) => void>(() => {});
  const handleCopyWebhookURLRef = useRef<(nodeId: string) => void>(() => {});

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

  // Sync nodes changes to parent
  useEffect(() => {
    if (onNodesChangeProp && !readOnly) {
      onNodesChangeProp(nodes);
    }
  }, [nodes, onNodesChangeProp, readOnly]);

  // Sync edges changes to parent
  useEffect(() => {
    if (onEdgesChangeProp && !readOnly) {
      onEdgesChangeProp(edges);
    }
  }, [edges, onEdgesChangeProp, readOnly]);

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

  // Clipboard state
  const [copiedNodes, setCopiedNodes] = useState<Node[]>([]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
      // Copy
      else if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        const selectedNodes = nodes.filter(node => node.selected);
        if (selectedNodes.length > 0) {
          e.preventDefault();
          setCopiedNodes(selectedNodes);
          toast({
            title: '📋 Copied',
            description: `${selectedNodes.length} node${selectedNodes.length !== 1 ? 's' : ''} copied to clipboard`,
            duration: 1500,
          });
        }
      }
      // Paste
      else if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        if (copiedNodes.length > 0) {
          e.preventDefault();
          
          // Create ID mapping for copied nodes
          const idMapping = new Map<string, string>();
          const newNodes = copiedNodes.map(node => {
            const newId = generateUUID();
            idMapping.set(node.id, newId);
            
            return {
              ...node,
              id: newId,
              position: {
                x: node.position.x + 50, // Offset by 50px
                y: node.position.y + 50,
              },
              selected: true,
            };
          });
          
          // Copy edges between copied nodes
          const copiedNodeIds = new Set(copiedNodes.map(n => n.id));
          const newEdges = edges
            .filter(edge => copiedNodeIds.has(edge.source) && copiedNodeIds.has(edge.target))
            .map(edge => ({
              ...edge,
              id: generateUUID(),
              source: idMapping.get(edge.source) || edge.source,
              target: idMapping.get(edge.target) || edge.target,
            }));
          
          // Deselect existing nodes
          setNodes(nds => [
            ...nds.map(n => ({ ...n, selected: false })),
            ...newNodes,
          ]);
          
          setEdges(eds => [...eds, ...newEdges]);
          
          toast({
            title: '📋 Pasted',
            description: `${newNodes.length} node${newNodes.length !== 1 ? 's' : ''} and ${newEdges.length} connection${newEdges.length !== 1 ? 's' : ''} pasted`,
            duration: 2000,
          });
        }
      }
      // Duplicate (Ctrl+D)
      else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        const selectedNodes = nodes.filter(node => node.selected);
        if (selectedNodes.length > 0) {
          e.preventDefault();
          
          // Same as paste logic
          const idMapping = new Map<string, string>();
          const newNodes = selectedNodes.map(node => {
            const newId = generateUUID();
            idMapping.set(node.id, newId);
            
            return {
              ...node,
              id: newId,
              position: {
                x: node.position.x + 50,
                y: node.position.y + 50,
              },
              selected: true,
            };
          });
          
          const selectedNodeIds = new Set(selectedNodes.map(n => n.id));
          const newEdges = edges
            .filter(edge => selectedNodeIds.has(edge.source) && selectedNodeIds.has(edge.target))
            .map(edge => ({
              ...edge,
              id: generateUUID(),
              source: idMapping.get(edge.source) || edge.source,
              target: idMapping.get(edge.target) || edge.target,
            }));
          
          setNodes(nds => [
            ...nds.map(n => ({ ...n, selected: false })),
            ...newNodes,
          ]);
          
          setEdges(eds => [...eds, ...newEdges]);
          
          toast({
            title: '📋 Duplicated',
            description: `${newNodes.length} node${newNodes.length !== 1 ? 's' : ''} duplicated`,
            duration: 2000,
          });
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [readOnly, handleUndo, handleRedo, nodes, edges, copiedNodes, setNodes, setEdges, toast]);

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
      
      console.log('🔗 Manual connection created:', connection);
      
      const newEdge = {
        ...connection,
        type: 'custom',
        id: generateUUID(),
      };
      
      setEdges((eds) => {
        const updatedEdges = addEdge(newEdge, eds);
        console.log('📊 Total edges after manual connection:', updatedEdges.length);
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
    setSelectedNode(node);
  }, []);

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
        console.log('✨ Auto-connection created:', newEdgesCreated.length, 'new edge(s)');
        
        setEdges((eds) => {
          const updatedEdges = [...eds, ...newEdgesCreated];
          console.log('📊 Total edges after auto-connection:', updatedEdges.length);
          
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
              console.log('📤 Notifying parent of edge changes');
              onEdgesChangeProp(updatedEdges);
            }, 0);
          }
          
          return updatedEdges;
        });
      }
    },
    [readOnly, nodes, edges, setEdges, onEdgesChangeProp]
  );

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
      {selectedNode && !readOnly && !showExecutionDetails && (
        <NodeConfigPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onUpdate={handleNodeUpdate}
          onDelete={handleNodeDelete}
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
