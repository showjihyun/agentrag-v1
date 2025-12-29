'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { logger } from '@/lib/logger';
import { getAccessToken } from '@/lib/auth';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Edit, Play, Copy, Trash, GitBranch, Clock, CheckCircle, XCircle, Eye, FileText, X } from 'lucide-react';
import type { Node, Edge } from 'reactflow';
import { useWorkflowExecutionStream } from '@/hooks/useWorkflowExecutionStream';
import { ExecutionProgress } from '@/components/workflow/ExecutionProgress';
import { ExecutionLogPanel } from '@/components/workflow/ExecutionLogPanel';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface ExecutionRecord {
  id: string;
  status: 'success' | 'failed' | 'running';
  duration: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  input_data?: any;
  output_data?: any;
}

interface Workflow {
  id: string;
  name: string;
  description?: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export default function WorkflowViewPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('canvas');
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRecord | null>(null);
  const [executionDetailsOpen, setExecutionDetailsOpen] = useState(false);
  const [simulatedNodeStatuses, setSimulatedNodeStatuses] = useState<Record<string, any>>({});
  const [isSimulation, setIsSimulation] = useState(false);
  const [executionStartTime, setExecutionStartTime] = useState<number | undefined>(undefined);
  const [executionEndTime, setExecutionEndTime] = useState<number | undefined>(undefined);
  const [showExecutionLog, setShowExecutionLog] = useState(false);
  const [simulatedExecutions, setSimulatedExecutions] = useState<ExecutionRecord[]>([]);
  const [showInputDialog, setShowInputDialog] = useState(false);
  const [workflowInput, setWorkflowInput] = useState('');
  const [aiAgentMessages, setAiAgentMessages] = useState<any[]>([]); // Store AI Agent chat messages

  // SSE for real-time execution status
  const {
    nodeStatuses: sseNodeStatuses,
    isConnected,
    isComplete,
  } = useWorkflowExecutionStream({
    workflowId,
    ...(executionId && { executionId }),
    enabled: executing && !isSimulation,
    onComplete: (status) => {
      logger.log('✅ Workflow execution completed:', status);
      setExecuting(false);
      loadExecutions();
      toast({
        title: 'Execution Complete',
        description: `Workflow execution ${status}`,
      });
    },
    onError: (error) => {
      logger.error('❌ Workflow execution error:', error);
      setExecuting(false);
      toast({
        title: 'Execution Error',
        description: error,
      });
    },
  });
  
  // Use simulated statuses if in simulation mode OR if we have simulated data, otherwise use SSE statuses
  const nodeStatuses = (isSimulation || Object.keys(simulatedNodeStatuses).length > 0) 
    ? simulatedNodeStatuses 
    : sseNodeStatuses;

  // Debug: Log SSE connection status and node statuses
  useEffect(() => {
    logger.log('🔍 Status Update:', {
      executing,
      isSimulation,
      executionId,
      isConnected,
      isComplete,
      nodeStatusesCount: Object.keys(nodeStatuses).length,
      nodeStatuses: Object.keys(nodeStatuses).map(id => ({
        id,
        status: nodeStatuses[id]?.status,
      })),
    });
  }, [executing, executionId, isConnected, isComplete, nodeStatuses, isSimulation]);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  useEffect(() => {
    if (activeTab === 'executions') {
      loadExecutions();
    }
  }, [activeTab, workflowId]);

  const loadExecutions = async () => {
    try {
      setLoadingExecutions(true);
      
      // Call API to get executions
      const data = await agentBuilderAPI.getWorkflowExecutions(workflowId, {
        limit: 50,
        offset: 0,
      });
      
      // Transform API response to match our interface
      const executionRecords: ExecutionRecord[] = (data.executions || []).map((exec: any) => ({
        id: exec.id,
        status: exec.status,
        duration: exec.duration || 0,
        started_at: exec.started_at,
        completed_at: exec.completed_at,
        error_message: exec.error_message,
        input_data: exec.input_data,
        output_data: exec.output_data,
      }));
      
      // Merge with simulated executions
      const allExecutions = [...simulatedExecutions, ...executionRecords].sort((a, b) => 
        new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
      );
      
      setExecutions(allExecutions);
    } catch (error: any) {
      logger.error('Failed to load executions:', error);
      
      // If API fails, show only simulated executions
      if (simulatedExecutions.length > 0) {
        setExecutions(simulatedExecutions);
      } else {
        toast({
          title: 'Error',
          description: error.message || 'Failed to load executions',
        });
        setExecutions([]);
      }
    } finally {
      setLoadingExecutions(false);
    }
  };

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getWorkflow(workflowId);
      logger.log('📊 Workflow loaded:', {
        id: data.id,
        name: data.name,
        nodesCount: data.graph_definition?.nodes?.length || 0,
        edgesCount: data.graph_definition?.edges?.length || 0,
        nodes: data.graph_definition?.nodes,
        edges: data.graph_definition?.edges,
      });
      setWorkflow(data);
    } catch (error: any) {
      console.error('❌ Failed to load workflow:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load workflow',
      });
    } finally {
      setLoading(false);
    }
  };

  // Stream workflow execution and update node statuses
  const streamWorkflowExecution = async (execId: string, inputData: string) => {
    try {
      let token = getAccessToken();
      
      // In development mode, token should already be set by startExecution
      // But double-check just in case
      if (!token && process.env.NODE_ENV === 'development') {
        logger.warn('⚠️ No token in streamWorkflowExecution, this should not happen after auto-login');
      }
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }
      
      // SSE endpoint expects token as query parameter, not header
      const response = await fetch(
        `/api/agent-builder/workflows/${workflowId}/execute/stream?input_data=${encodeURIComponent(JSON.stringify({ user_query: inputData }))}&token=${encodeURIComponent(token)}`,
        {
          method: 'GET',
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        }
        const errorText = await response.text();
        throw new Error(`Failed to stream workflow execution: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is null');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              logger.log('✅ Workflow execution stream completed');
              setExecuting(false);
              setExecutionEndTime(Date.now());
              toast({
                title: '✅ Execution Complete',
                description: 'Workflow executed successfully',
              });
              return;
            }

            try {
              const event = JSON.parse(data);
              logger.log('📡 Stream event:', event);
              logger.log(`📊 Event type: ${event.type}, Node: ${event.data?.node_id || 'N/A'}`);

              // Handle different event types
              if (event.type === 'start') {
                logger.log('🎬 Workflow execution started');
              } else if (event.type === 'node_start') {
                logger.log('🔵 Node start:', event.data);
                const nodeName = event.data.label || event.data.node_name || event.data.node_type || 'Unknown';
                logger.log(`📝 Node name: "${nodeName}" (from label: ${event.data.label}, type: ${event.data.node_type})`);
                
                setSimulatedNodeStatuses(prev => ({
                  ...prev,
                  [event.data.node_id]: {
                    nodeId: event.data.node_id,
                    nodeName: nodeName,
                    nodeType: event.data.node_type,
                    status: 'running',
                    startTime: Date.now(),
                    timestamp: Date.now(),
                    input: event.data.input,
                  },
                }));
              } else if (event.type === 'node_complete') {
                logger.log('✅ Node complete:', event.data);
                setSimulatedNodeStatuses(prev => {
                  const prevNode: any = prev[event.data.node_id] || {};
                  const updated: any = {
                    ...prev,
                    [event.data.node_id]: {
                      ...prevNode,
                      nodeId: event.data.node_id,
                      nodeName: prevNode.nodeName || event.data.node_type,
                      nodeType: prevNode.nodeType || event.data.node_type,
                      status: 'success' as const,
                      endTime: Date.now(),
                      output: event.data.output,
                    },
                  };
                  logger.log('📊 Updated node statuses:', Object.keys(updated).map(id => {
                    const node = updated[id];
                    return {
                      id,
                      status: node?.status,
                      name: node?.nodeName
                    };
                  }));
                  return updated;
                });
                
                // If it's an AI Agent node, add messages to chat
                if (event.data.node_type === 'ai_agent' && event.data.output) {
                  const output = event.data.output;
                  
                  // Extract AI Agent config and response
                  const aiConfig = output.ai_agent_config || {};
                  const execDetails = output.execution_details || {};
                  const inputInfo = output.input || {};
                  
                  const userMessage = {
                    id: `user-${Date.now()}`,
                    role: 'user' as const,
                    content: inputInfo.processed_task || aiConfig.user_message || event.data.input?.user_query || inputData,
                    timestamp: new Date(),
                  };
                  
                  // Build detailed assistant message with config info
                  let responseContent = output.response || output.content || 'No response';
                  
                  // Add config info as metadata display
                  const configInfo = `\n\n---\n**AI Agent Config:**\n- Provider: ${aiConfig.provider || 'unknown'}\n- Model: ${aiConfig.model || 'unknown'}\n- Temperature: ${aiConfig.temperature || 0.7}\n- Max Tokens: ${aiConfig.max_tokens || 2000}\n- Execution Time: ${execDetails.execution_time_ms || 0}ms`;
                  
                  const assistantMessage = {
                    id: `assistant-${Date.now()}`,
                    role: 'assistant' as const,
                    content: responseContent,
                    timestamp: new Date(),
                    metadata: {
                      model: aiConfig.model,
                      provider: aiConfig.provider,
                      temperature: aiConfig.temperature,
                      max_tokens: aiConfig.max_tokens,
                      execution_time_ms: execDetails.execution_time_ms,
                      memory_type: aiConfig.memory_type,
                      success: output.success,
                    },
                  };
                  
                  setAiAgentMessages(prev => [...prev, userMessage, assistantMessage]);
                  
                  logger.log('✅ Added AI Agent messages to chat:', { 
                    userMessage, 
                    assistantMessage,
                    config: aiConfig,
                    executionDetails: execDetails
                  });
                }
              } else if (event.type === 'node_error') {
                setSimulatedNodeStatuses(prev => ({
                  ...prev,
                  [event.data.node_id]: {
                    ...prev[event.data.node_id],
                    status: 'failed',
                    endTime: Date.now(),
                    error: event.data.error,
                  },
                }));
              } else if (event.type === 'complete') {
                logger.log('🏁 Workflow execution completed');
                setExecuting(false);
                setExecutionEndTime(Date.now());
                toast({
                  title: '✅ Execution Complete',
                  description: 'Workflow executed successfully',
                });
              } else if (event.type === 'error') {
                logger.error('❌ Workflow error:', event.data);
                throw new Error(event.data.message || 'Workflow execution failed');
              } else {
                logger.warn('⚠️ Unknown event type:', event.type);
              }
            } catch (e) {
              logger.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    } catch (error: any) {
      logger.error('❌ Stream error:', error);
      setExecuting(false);
      toast({
        title: 'Stream Error',
        description: error.message || 'Failed to stream execution',
      });
    }
  };

  const handleExecute = async () => {
    // Show input dialog first
    setShowInputDialog(true);
  };
  
  const startExecution = async (inputData: string) => {
    logger.log('🚀 Starting workflow execution:', workflowId);
    logger.log('📊 Current nodes:', nodes.length);
    logger.log('📝 Input data:', inputData);
    
    // Clear previous execution data
    setSimulatedNodeStatuses({});
    setExecutionEndTime(undefined);
    setAiAgentMessages([]); // Clear AI Agent chat messages
    
    // Switch to canvas tab to show execution animation
    setActiveTab('canvas');
    setExecuting(true);
    setExecutionStartTime(Date.now());
    setShowExecutionLog(true); // Auto-show log panel when execution starts
    
    toast({
      title: '🎬 Starting Execution',
      description: 'Executing workflow with real API calls...',
    });
    
    try {
      let token = getAccessToken();
      
      logger.log('🔑 Token check:', token ? `Token exists (${token.substring(0, 20)}...)` : 'No token found');
      
      // In development mode, auto-login with test account if no token
      if (!token && process.env.NODE_ENV === 'development') {
        logger.log('🔧 Development mode: Auto-logging in with test account...');
        
        try {
          const loginResponse = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: 'test@example.com',
              password: 'test123',
            }),
          });
          
          if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            const { setTokens } = await import('@/lib/auth');
            setTokens(loginData.access_token, loginData.refresh_token || '');
            token = loginData.access_token;
            
            logger.log('✅ Auto-login successful');
            toast({
              title: 'Development Mode',
              description: 'Auto-logged in with test account',
            });
          } else {
            const errorText = await loginResponse.text();
            logger.error('❌ Auto-login failed:', errorText);
            
            // Show detailed error in development
            toast({
              title: 'Auto-login Failed',
              description: 'Check backend server and test user. See console for details.',
            });
          }
        } catch (loginError) {
          logger.error('❌ Auto-login error:', loginError);
          toast({
            title: 'Auto-login Error',
            description: 'Backend server may not be running. Check console for details.',
          });
        }
      }
      
      if (!token) {
        const errorMessage = 'Authentication required. Please log in again.';
        
        toast({
          title: 'Authentication Required',
          description: process.env.NODE_ENV === 'development' 
            ? 'Auto-login failed. Please check backend server.'
            : 'Please log in to execute workflows.',
        });
        
        // Only redirect to login in production mode
        if (process.env.NODE_ENV !== 'development') {
          setTimeout(() => {
            router.push('/login');
          }, 2000);
        }
        
        throw new Error(errorMessage);
      }
      
      // Use agentBuilderAPI for consistent authentication
      const data = await agentBuilderAPI.executeWorkflow(workflowId, {
        input_data: { user_query: inputData },
      });
      
      const execId = data.execution_id || data.id;
      
      logger.log('✅ Workflow execution started:', execId);
      setExecutionId(execId);
      
      // Start listening to execution stream
      await streamWorkflowExecution(execId, inputData);
      
    } catch (error: any) {
      logger.error('❌ Failed to start execution:', error);
      toast({
        title: 'Execution Failed',
        description: error.message || 'Failed to execute workflow',
      });
      setExecuting(false);
    }
  };
  
  // Generate simulated output based on node type
  const generateSimulatedOutput = (nodeType: string, nodeName: string, config: any, input?: any) => {
    switch (nodeType) {
      case 'start':
      case 'trigger':
        return {
          message: 'Workflow started successfully',
          timestamp: new Date().toISOString(),
        };
      
      case 'ai_agent':
        const userQuery = input?.user_query || input?.workflow_input || 'No query provided';
        const aiResponse = `This is a simulated AI response from ${nodeName}. In production, this would be the actual LLM output based on your query: "${userQuery}"`;
        
        // Add to AI Agent chat messages
        const userMessage = {
          id: `user-${Date.now()}`,
          role: 'user' as const,
          content: userQuery,
          timestamp: new Date(),
        };
        
        const assistantMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant' as const,
          content: aiResponse,
          timestamp: new Date(),
          metadata: {
            model: config?.model || 'unknown',
            provider: config?.provider || 'unknown',
          },
        };
        
        // Update AI Agent messages
        setAiAgentMessages(prev => [...prev, userMessage, assistantMessage]);
        
        return {
          response: aiResponse,
          model: config?.model || 'unknown',
          provider: config?.provider || 'unknown',
          tokens_used: Math.floor(Math.random() * 500) + 100,
          simulation: true,
          user_query: userQuery,
        };
      
      case 'http_request':
        return {
          status_code: 200,
          data: { message: 'Simulated HTTP response', success: true },
          url: config?.url || 'https://example.com',
          method: config?.method || 'GET',
          simulation: true,
        };
      
      case 'condition':
        return {
          condition_met: true,
          branch_taken: 'true',
          evaluation: 'Simulated condition evaluation',
        };
      
      case 'tool':
        return {
          tool_output: `Simulated output from ${nodeName}`,
          tool_id: config?.tool_id || 'unknown',
          execution_time_ms: Math.floor(Math.random() * 1000) + 100,
          simulation: true,
        };
      
      case 'end':
        return {
          message: 'Workflow completed successfully',
          final_output: 'All nodes executed',
          timestamp: new Date().toISOString(),
        };
      
      default:
        return {
          message: `Simulated output from ${nodeName}`,
          node_type: nodeType,
          processed: true,
          simulation: true,
        };
    }
  };

  // Simulate execution for testing animation
  const simulateExecution = (inputData: string = '') => {
    if (!workflow) {
      logger.error('❌ No workflow found');
      return;
    }
    
    if (nodes.length === 0) {
      logger.error('❌ No nodes found');
      toast({
        title: 'No Nodes',
        description: 'This workflow has no nodes to execute',
      });
      setExecuting(false);
      return;
    }
    
    setIsSimulation(true);
    
    const nodeIds = nodes.map(n => n.id);
    const nodeNames = nodes.map(n => n.data?.name || n.data?.label || n.type || 'Node');
    const nodeTypes = nodes.map(n => n.type || 'unknown');
    const nodeConfigs = nodes.map(n => n.data?.config || {});
    
    logger.log('🎬 Starting simulation with nodes:', {
      count: nodeIds.length,
      ids: nodeIds,
      names: nodeNames,
      types: nodeTypes,
    });
    
    // Initialize all nodes as pending
    const initialStatuses: Record<string, any> = {};
    nodeIds.forEach((id, idx) => {
      initialStatuses[id] = {
        nodeId: id,
        nodeName: nodeNames[idx],
        nodeType: nodeTypes[idx],
        status: 'pending',
        timestamp: Date.now(),
        config: nodeConfigs[idx],
      };
    });
    
    logger.log('📊 Initial statuses:', initialStatuses);
    setSimulatedNodeStatuses({ ...initialStatuses });
    
    // Use a counter that persists across interval calls
    let currentIndex = 0;
    
    // Start simulation after a short delay
    setTimeout(() => {
      logger.log('⏰ Starting simulation interval');
      
      const simulationInterval = setInterval(() => {
        logger.log(`⏱️ Interval tick - currentIndex: ${currentIndex}, total: ${nodeIds.length}`);
        
        if (currentIndex >= nodeIds.length) {
          logger.log('🏁 Reached end of nodes, clearing interval');
          clearInterval(simulationInterval);
          
          // Mark last node as success
          setTimeout(() => {
            const lastNodeId = nodeIds[nodeIds.length - 1];
            if (lastNodeId) {
              logger.log('✅ Marking last node as success:', lastNodeId);
              
              setSimulatedNodeStatuses(prev => {
                const updated = {
                  ...prev,
                  [lastNodeId]: {
                    ...prev[lastNodeId],
                    status: 'success',
                    endTime: Date.now(),
                  },
                };
                logger.log('✅ Final statuses:', updated);
                return updated;
              });
            }
            
            setTimeout(() => {
              logger.log('🎉 Simulation complete, cleaning up');
              const endTimeMs = Date.now();
              setExecutionEndTime(endTimeMs);
              setExecuting(false);
              setIsSimulation(false);
              
              const duration = executionStartTime ? endTimeMs - executionStartTime : 0;
              const endTime = new Date(endTimeMs);
              const startTime = new Date(executionStartTime || Date.now());
              
              // Create execution record for simulated run
              const simulatedExecution: ExecutionRecord = {
                id: executionId || `sim-${Date.now()}`,
                status: 'success',
                duration: duration / 1000, // Convert to seconds
                started_at: startTime.toISOString(),
                completed_at: endTime.toISOString(),
                input_data: {},
                output_data: {
                  simulation: true,
                  nodes_executed: nodeIds.length,
                  node_statuses: Object.keys(simulatedNodeStatuses).map(id => ({
                    id,
                    name: simulatedNodeStatuses[id]?.nodeName,
                    status: simulatedNodeStatuses[id]?.status,
                  })),
                },
              };
              
              // Add to simulated executions
              setSimulatedExecutions(prev => [simulatedExecution, ...prev]);
              
              toast({
                title: '✅ Simulation Complete',
                description: `Successfully executed ${nodeIds.length} nodes in ${(duration / 1000).toFixed(1)}s!`,
              });
              
              // Reload executions to show the new record
              if (activeTab === 'executions') {
                loadExecutions();
              }
            }, 1000);
          }, 1500);
          
          return;
        }
        
        const nodeId = nodeIds[currentIndex];
        const nodeName = nodeNames[currentIndex];
        
        if (!nodeId) {
          logger.error('❌ No nodeId found for index:', currentIndex);
          return;
        }
        
        logger.log(`🔵 Processing node ${currentIndex + 1}/${nodeIds.length}:`, {
          id: nodeId,
          name: nodeName,
          currentIndex,
        });
        
        setSimulatedNodeStatuses(prev => {
          const updated = { ...prev };
          
          const currentNodeType = nodeTypes[currentIndex];
          const currentNodeConfig = nodeConfigs[currentIndex];
          
          // Generate simulated input/output based on node type
          const simulatedInput = currentIndex === 0 
            ? { 
                workflow_input: inputData || 'No input provided',
                user_query: inputData || '',
                timestamp: new Date().toISOString()
              }
            : { previous_output: `Output from ${nodeNames[currentIndex - 1]}` };
          
          // Set current node to running first
          updated[nodeId] = {
            ...updated[nodeId],
            nodeId,
            nodeName,
            nodeType: currentNodeType,
            status: 'running',
            startTime: Date.now(),
            timestamp: Date.now(),
            input: simulatedInput,
            config: currentNodeConfig,
          };
          
          // Generate output (this may update AI Agent messages)
          const simulatedOutput = generateSimulatedOutput(
            currentNodeType || 'unknown', 
            nodeName || 'Unknown Node', 
            currentNodeConfig, 
            simulatedInput
          );
          
          logger.log(`🔵 Set node ${nodeId} to RUNNING`);
          
          // Update previous node to success with output
          if (currentIndex > 0) {
            const prevNodeId = nodeIds[currentIndex - 1];
            if (prevNodeId) {
              const prevNodeType = nodeTypes[currentIndex - 1];
              const prevNodeConfig = nodeConfigs[currentIndex - 1];
              const prevInput = updated[prevNodeId]?.input;
              const prevOutput = generateSimulatedOutput(
                prevNodeType || 'unknown', 
                nodeNames[currentIndex - 1] || 'Unknown Node', 
                prevNodeConfig, 
                prevInput
              );
              
              logger.log(`🟢 Marking previous node ${prevNodeId} as SUCCESS`);
              updated[prevNodeId] = {
                ...updated[prevNodeId],
                status: 'success',
              endTime: Date.now(),
              output: prevOutput,
            };
            }
          }
          
          logger.log('📊 Current statuses:', Object.keys(updated).map(id => ({
            id,
            status: updated[id].status,
          })));
          
          return updated;
        });
        
        logger.log(`➡️ Incrementing currentIndex from ${currentIndex} to ${currentIndex + 1}`);
        currentIndex++; // This will now properly increment
      }, 2000); // 2 seconds per node
      
      logger.log('✅ Simulation interval created');
    }, 500); // Initial delay
  };

  const handleDuplicate = async () => {
    if (!workflow) return;

    try {
      // Use the new duplicate endpoint
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/duplicate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate workflow');
      }

      const newWorkflow = await response.json();

      toast({
        title: '✅ Workflow Duplicated',
        description: 'Successfully created a copy of the workflow',
      });

      // Navigate to the new workflow
      router.push(`/agent-builder/workflows/${newWorkflow.id}`);
    } catch (error: any) {
      toast({
        title: '❌ Error',
        description: error.message || 'Failed to duplicate workflow',
      });
    }
  };

  const handleDelete = async () => {
    try {
      await agentBuilderAPI.deleteWorkflow(workflowId);
      toast({
        title: 'Success',
        description: 'Workflow deleted successfully',
      });
      router.push('/agent-builder/workflows');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete workflow',
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-[600px] w-full" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Workflow not found</p>
            <Button
              variant="link"
              onClick={() => router.push('/agent-builder/workflows')}
            >
              Back to Workflows
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const nodes: Node[] = workflow.graph_definition.nodes.map((node: any) => {
    // Determine node type
    let nodeType = node.node_type || node.type;
    
    // Handle control nodes - they should have a specific type in configuration
    if (nodeType === 'control') {
      nodeType = node.configuration?.type || node.configuration?.nodeType || node.data?.type || 'start';
      logger.log('🎛️ Control node detected:', {
        originalType: node.node_type,
        configType: node.configuration?.type,
        finalType: nodeType,
        configuration: node.configuration,
      });
    }
    
    // Build node data, preserving config for tool nodes
    const configuration = node.configuration || node.data || {};
    
    // Get config and parameters from saved data
    const savedConfig = configuration.config || {};
    const savedParameters = configuration.parameters || {};
    
    // Build unified config from multiple sources (parameters > config > top-level)
    const aiAgentConfig = {
      llm_provider: savedParameters.provider || savedConfig.llm_provider || configuration.llm_provider,
      model: savedParameters.model || savedConfig.model || configuration.model,
      system_prompt: savedParameters.system_prompt || savedConfig.system_prompt || configuration.system_prompt,
      user_message: savedParameters.user_message || savedConfig.user_message || configuration.user_message,
      temperature: savedParameters.temperature || savedConfig.temperature || configuration.temperature,
      max_tokens: savedParameters.max_tokens || savedConfig.max_tokens || configuration.max_tokens,
      memory_type: savedParameters.memory_type || savedConfig.memory_type || configuration.memory_type,
      api_key: savedParameters.api_key || savedConfig.api_key || configuration.api_key,
    };
    
    // Build parameters for UI compatibility
    const parameters = {
      ...savedParameters,
      provider: savedParameters.provider || savedConfig.llm_provider || configuration.llm_provider,
      model: savedParameters.model || savedConfig.model || configuration.model,
      system_prompt: savedParameters.system_prompt || savedConfig.system_prompt || configuration.system_prompt,
      user_message: savedParameters.user_message || savedConfig.user_message || configuration.user_message,
      temperature: savedParameters.temperature || savedConfig.temperature || configuration.temperature,
      max_tokens: savedParameters.max_tokens || savedConfig.max_tokens || configuration.max_tokens,
      memory_type: savedParameters.memory_type || savedConfig.memory_type || configuration.memory_type,
      api_key: savedParameters.api_key || savedConfig.api_key || configuration.api_key,
    };
    
    const nodeData = {
      ...configuration,
      // Ensure tool_id is preserved
      tool_id: configuration.tool_id || node.tool_id,
      // Ensure config is preserved (for AI Agent and other tools)
      config: aiAgentConfig,
      // Ensure parameters is preserved for UI
      parameters: parameters,
      // Also store at top level for compatibility
      ...aiAgentConfig,
    };
    
    const transformedNode = {
      id: node.id,
      type: nodeType,
      position: node.position || { x: node.position_x || 0, y: node.position_y || 0 },
      data: nodeData,
    };
    
    logger.log('🔄 Node transformation:', {
      original: { id: node.id, type: node.node_type, config: node.configuration },
      transformed: { id: transformedNode.id, type: transformedNode.type, data: transformedNode.data },
      aiAgentConfig,
    });
    
    return transformedNode;
  });

  const edges: Edge[] = workflow.graph_definition.edges.map((edge: any) => ({
    id: edge.id,
    source: edge.source_node_id || edge.source,
    target: edge.target_node_id || edge.target,
    sourceHandle: edge.source_handle || edge.sourceHandle,
    targetHandle: edge.target_handle || edge.targetHandle,
  }));

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="container mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/agent-builder/workflows')}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <div className="flex items-center gap-2">
                  <GitBranch className="h-6 w-6" />
                  <h1 className="text-2xl font-bold">{workflow.name}</h1>
                  {workflow.is_active && (
                    <Badge variant="default">Active</Badge>
                  )}
                </div>
                {workflow.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {workflow.description}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleDuplicate}
              >
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </Button>
              <Button
                variant="default"
                onClick={handleExecute}
                disabled={executing}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Play className="mr-2 h-4 w-4" />
                {executing ? 'Executing...' : 'Execute'}
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push(`/agent-builder/workflows/${workflowId}/edit`)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <Button
                variant="destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash className="mr-2 h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{nodes.length} nodes</span>
            <span>•</span>
            <span>{edges.length} connections</span>
            <span>•</span>
            <span>Created {new Date(workflow.created_at).toLocaleDateString()}</span>
            {workflow.updated_at && (
              <>
                <span>•</span>
                <span>Updated {new Date(workflow.updated_at).toLocaleDateString()}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="border-b px-4">
            <TabsList>
              <TabsTrigger value="canvas">Canvas</TabsTrigger>
              <TabsTrigger value="executions">Executions</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="canvas" className="flex-1 m-0 bg-muted/20 flex overflow-hidden relative">
            {/* Canvas Area */}
            <div className="flex-1 overflow-hidden">
              <WorkflowEditor
                workflowId={workflowId}
                initialNodes={nodes}
                initialEdges={edges}
                readOnly={true}
                executionMode={executing}
                nodeStatuses={nodeStatuses}
                isExecutionConnected={isConnected}
                isExecutionComplete={isComplete}
                onExecutionStart={handleExecute}
                onExecutionStop={() => {
                  setExecuting(false);
                  setExecutionId(null);
                }}
                aiAgentMessages={aiAgentMessages}
              />
            </div>
            
            {/* Toggle Button - Show when there are logs */}
            {Object.keys(nodeStatuses).length > 0 && !showExecutionLog && (
              <Button
                variant="default"
                size="sm"
                onClick={() => setShowExecutionLog(true)}
                className="absolute bottom-4 right-4 z-50 shadow-lg"
              >
                <FileText className="mr-2 h-4 w-4" />
                Show Execution Log
              </Button>
            )}
            
            {/* Execution Log Panel - Show when toggled on and has logs */}
            {showExecutionLog && Object.keys(nodeStatuses).length > 0 && (
              <div className="w-96 border-l bg-background overflow-hidden flex flex-col relative">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowExecutionLog(false)}
                  className="absolute top-2 right-2 z-10 h-8 w-8"
                  title="Hide execution log"
                >
                  <X className="h-4 w-4" />
                </Button>
                <ExecutionLogPanel
                  nodeStatuses={nodeStatuses}
                  isExecuting={executing}
                  {...(executionStartTime !== undefined && { startTime: executionStartTime })}
                  {...(executionEndTime !== undefined && { endTime: executionEndTime })}
                />
              </div>
            )}
          </TabsContent>

          <TabsContent value="executions" className="flex-1 m-0 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-auto">
              <div className="container mx-auto p-6">
                {/* Real-time Execution Progress */}
                {executing && (
                  <div className="mb-4">
                    <ExecutionProgress
                      workflowId={workflowId}
                      {...(executionId && { executionId })}
                      isExecuting={executing}
                      nodeStatuses={nodeStatuses}
                      onNodeClick={(nodeId) => {
                        logger.log('Node clicked:', nodeId);
                        // Could highlight node in canvas
                      }}
                    />
                  </div>
                )}
                
                <Card>
                  <CardHeader>
                    <CardTitle>Execution History</CardTitle>
                    <CardDescription>
                      View past workflow executions and their results
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                  {loadingExecutions ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                      <p className="mt-4 text-muted-foreground">Loading executions...</p>
                    </div>
                  ) : executions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No executions yet</p>
                      <p className="text-sm mt-2">Run this workflow to see execution history</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Status</TableHead>
                          <TableHead>Execution ID</TableHead>
                          <TableHead>Duration</TableHead>
                          <TableHead>Started At</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {executions.map((exec) => (
                          <TableRow key={exec.id} className={exec.status === 'failed' ? 'bg-destructive/5' : ''}>
                            <TableCell>
                              <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                  {exec.status === 'success' ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : null}
                                  {exec.status === 'failed' && (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                  {exec.status === 'running' && (
                                    <Clock className="h-4 w-4 text-blue-500 animate-spin" />
                                  )}
                                  <Badge
                                    variant={
                                      exec.status === 'success'
                                        ? 'default'
                                        : exec.status === 'failed'
                                        ? 'destructive'
                                        : 'secondary'
                                    }
                                  >
                                    {exec.status}
                                  </Badge>
                                  {exec.output_data?.simulation && (
                                    <Badge variant="outline" className="text-xs">
                                      Simulation
                                    </Badge>
                                  )}
                                </div>
                                {exec.status === 'failed' && exec.error_message && (
                                  <div className="text-xs text-destructive truncate max-w-xs" title={exec.error_message}>
                                    {exec.error_message}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="font-mono text-sm">
                              {exec.id.startsWith('sim-') ? (
                                <span className="text-muted-foreground" title={exec.id}>
                                  {exec.id.substring(0, 12)}...
                                </span>
                              ) : (
                                <span title={exec.id}>
                                  {exec.id.substring(0, 8)}...
                                </span>
                              )}
                            </TableCell>
                            <TableCell>{exec.duration.toFixed(2)}s</TableCell>
                            <TableCell>
                              {new Date(exec.started_at).toLocaleString()}
                            </TableCell>
                            <TableCell>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => {
                                  setSelectedExecution(exec);
                                  setExecutionDetailsOpen(true);
                                }}
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="flex-1 m-0 overflow-auto">
            <div className="container mx-auto p-6">
              <Card>
                <CardHeader>
                  <CardTitle>Workflow Settings</CardTitle>
                  <CardDescription>
                    Configure workflow behavior and notifications
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">Active Status</div>
                        <div className="text-sm text-muted-foreground">
                          Enable or disable this workflow
                        </div>
                      </div>
                      <Badge variant={workflow?.is_active ? 'default' : 'secondary'}>
                        {workflow?.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <div className="font-medium mb-2">Workflow Information</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Created:</span>
                          <span>{new Date(workflow?.created_at || '').toLocaleString()}</span>
                        </div>
                        {workflow?.updated_at && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Last Updated:</span>
                            <span>{new Date(workflow.updated_at).toLocaleString()}</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Nodes:</span>
                          <span>{nodes.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Connections:</span>
                          <span>{edges.length}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workflow</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{workflow.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Execution Details Dialog */}
      <AlertDialog open={executionDetailsOpen} onOpenChange={setExecutionDetailsOpen}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Execution Details</AlertDialogTitle>
            <AlertDialogDescription>
              Detailed information about this workflow execution
            </AlertDialogDescription>
          </AlertDialogHeader>
          {selectedExecution && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Execution ID</div>
                  <div className="font-mono text-sm mt-1">{selectedExecution.id}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Status</div>
                  <div className="mt-1">
                    <Badge
                      variant={
                        selectedExecution.status === 'success'
                          ? 'default'
                          : selectedExecution.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {selectedExecution.status}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Duration</div>
                  <div className="text-sm mt-1">{selectedExecution.duration.toFixed(2)}s</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Started At</div>
                  <div className="text-sm mt-1">
                    {new Date(selectedExecution.started_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {selectedExecution.error_message && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Error Message</div>
                  <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
                    {selectedExecution.error_message}
                  </div>
                </div>
              )}

              {selectedExecution.input_data && Object.keys(selectedExecution.input_data).length > 0 && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Input Data</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-40">
                    {JSON.stringify(selectedExecution.input_data, null, 2)}
                  </pre>
                </div>
              )}

              {selectedExecution.output_data && Object.keys(selectedExecution.output_data).length > 0 && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">Output Data</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-40">
                    {JSON.stringify(selectedExecution.output_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>Close</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Workflow Input Dialog */}
      <Dialog open={showInputDialog} onOpenChange={setShowInputDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Workflow Input</DialogTitle>
            <DialogDescription>
              Enter the input data for this workflow execution. This will be passed to the first node.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="workflow-input">Input Data</Label>
              <Textarea
                id="workflow-input"
                placeholder="Enter your query or input data here..."
                value={workflowInput}
                onChange={(e) => setWorkflowInput(e.target.value)}
                rows={6}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                This input will be available to all nodes in the workflow as the initial data.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowInputDialog(false);
                setWorkflowInput('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                setShowInputDialog(false);
                startExecution(workflowInput);
              }}
            >
              <Play className="mr-2 h-4 w-4" />
              Execute
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
