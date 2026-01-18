'use client';

import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ImprovedBlockPalette } from '@/components/workflow/ImprovedBlockPalette';
import { WorkflowExecutionPanel } from '@/components/workflow/WorkflowExecutionPanel';
import { VisualWorkflowCanvas } from '@/components/workflow/VisualWorkflowCanvas';
import { Button } from '@/components/ui/button';
import { Play, Save, Download, Upload, Settings, Maximize2, Minimize2 } from 'lucide-react';
import { toast } from 'sonner';

interface ExecutionLog {
  id: string;
  timestamp: Date;
  nodeId: string;
  nodeName: string;
  type: 'info' | 'success' | 'error' | 'warning';
  message: string;
  duration?: number;
  data?: any;
}

interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  nodeExecutions: Array<{
    nodeId: string;
    nodeName: string;
    status: 'pending' | 'running' | 'success' | 'error' | 'skipped';
    startTime?: Date;
    endTime?: Date;
    duration?: number;
    input?: any;
    output?: any;
    error?: string;
  }>;
  logs: ExecutionLog[];
}

export default function WorkflowBuilderPage() {
  const searchParams = useSearchParams();
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<WorkflowExecution | null>(null);
  const [executionHistory, setExecutionHistory] = useState<WorkflowExecution[]>([]);
  const [showExecutionPanel, setShowExecutionPanel] = useState(true);
  const [showExecutionLogs, setShowExecutionLogs] = useState(true);
  
  const addLog = useCallback((log: Omit<ExecutionLog, 'id' | 'timestamp'>) => {
    setExecutionLogs(prev => [
      {
        ...log,
        id: `log-${Date.now()}`,
        timestamp: new Date()
      },
      ...prev
    ].slice(0, 100)); // Keep last 100 logs
  }, []);

  // Auto-execute workflow if autoExecute parameter is present
  useEffect(() => {
    const autoExecute = searchParams?.get('autoExecute');
    const workflowId = searchParams?.get('workflowId');
    
    if (autoExecute === 'true' && workflowId && nodes.length > 0 && !isExecuting) {
      // Small delay to ensure UI is ready
      const timer = setTimeout(() => {
        handleExecuteWorkflow();
        toast.success('Auto-executing workflow...');
      }, 500);
      
      return () => clearTimeout(timer);
    }
    
    return () => {}; // Return empty cleanup function for other code paths
  }, [searchParams, nodes.length]);
  
  const handleAddNode = useCallback((type: string, toolId?: string) => {
    const nodeId = `node-${Date.now()}`;
    
    // Determine node type and config based on input
    let nodeType = type;
    let config: any = {};
    
    if (type === 'tool' && toolId) {
      nodeType = 'tool';
      config = {
        toolId: toolId,
        tool_id: toolId,
        parameters: {}
      };
    } else if (type === 'trigger') {
      nodeType = 'trigger';
      config = {
        triggerType: 'manual',
        trigger_type: 'manual'
      };
    } else if (type === 'condition') {
      nodeType = 'condition';
      config = {
        condition: '',
        operator: 'equals'
      };
    } else if (type === 'loop') {
      nodeType = 'loop';
      config = {
        items: [],
        maxIterations: 100
      };
    } else if (type === 'delay') {
      nodeType = 'delay';
      config = {
        duration: 1000,
        unit: 'ms'
      };
    } else if (type === 'filter') {
      nodeType = 'filter';
      config = {
        condition: '',
        operator: 'equals'
      };
    } else {
      // Default block type
      nodeType = 'block';
      config = {
        blockId: `block-${type}`,
        block_id: `block-${type}`,
        blockType: type
      };
    }
    
    const newNode = {
      id: nodeId,
      type: nodeType,
      position: { x: 250, y: 100 + nodes.length * 100 },
      data: {
        label: toolId || type,
        type: nodeType,
        config: config
      }
    };
    
    setNodes(prev => [...prev, newNode]);
    
    // Add log
    addLog({
      nodeId: newNode.id,
      nodeName: newNode.data.label,
      type: 'info',
      message: `Added ${newNode.data.label} node to workflow`
    });
    
    toast.success(`Added ${newNode.data.label} to workflow`);
  }, [nodes.length, addLog]);
  
  const handleExecuteWorkflow = async () => {
    const executionId = `exec-${Date.now()}`;
    const workflowStartTime = Date.now();
    
    setIsExecuting(true);
    
    // Create new execution
    const execution: WorkflowExecution = {
      id: executionId,
      workflowId: 'workflow-1',
      status: 'running',
      startTime: new Date(),
      nodeExecutions: [],
      logs: []
    };
    
    setCurrentExecution(execution);
    
    const newLog = {
      id: `log-${Date.now()}`,
      timestamp: new Date(),
      nodeId: 'workflow',
      nodeName: 'Workflow',
      type: 'info' as const,
      message: 'Starting workflow execution...'
    };
    
    execution.logs.push(newLog);
    setExecutionLogs(prev => [newLog, ...prev]);
    
    try {
      // Execute each node
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        const nodeStartTime = Date.now();
        
        // Update node status to running
        const nodeExec: any = {
          nodeId: node.id,
          nodeName: node.data.label,
          status: 'running',
          startTime: new Date(),
          input: { index: i }
        };
        
        execution.nodeExecutions.push(nodeExec);
        setCurrentExecution({ ...execution });
        
        // Log start
        const startLog: ExecutionLog = {
          id: `log-${Date.now()}-${i}`,
          timestamp: new Date(),
          nodeId: node.id,
          nodeName: node.data.label,
          type: 'info',
          message: `Executing ${node.data.label}...`
        };
        execution.logs.push(startLog);
        setExecutionLogs(prev => [startLog, ...prev]);
        
        // Simulate processing
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
        
        const duration = Date.now() - nodeStartTime;
        const success = Math.random() > 0.1; // 90% success rate
        
        // Update node execution
        nodeExec.status = success ? 'success' : 'error';
        nodeExec.endTime = new Date();
        nodeExec.duration = duration;
        nodeExec.output = success ? { result: 'Success', data: `Output from ${node.data.label}` } : undefined;
        nodeExec.error = success ? undefined : 'Simulated error occurred';
        
        setCurrentExecution({ ...execution });
        
        // Log completion
        const completeLog: ExecutionLog = {
          id: `log-${Date.now()}-${i}-complete`,
          timestamp: new Date(),
          nodeId: node.id,
          nodeName: node.data.label,
          type: success ? 'success' : 'error',
          message: success 
            ? `${node.data.label} completed successfully`
            : `${node.data.label} failed: Simulated error`,
          duration
        };
        execution.logs.push(completeLog);
        setExecutionLogs(prev => [completeLog, ...prev]);
        
        if (!success) {
          throw new Error(`Node ${node.data.label} failed`);
        }
      }
      
      // Workflow completed
      const workflowDuration = Date.now() - workflowStartTime;
      execution.status = 'completed';
      execution.endTime = new Date();
      execution.duration = workflowDuration;
      
      const finalLog: ExecutionLog = {
        id: `log-${Date.now()}-final`,
        timestamp: new Date(),
        nodeId: 'workflow',
        nodeName: 'Workflow',
        type: 'success',
        message: 'Workflow execution completed successfully',
        duration: workflowDuration
      };
      execution.logs.push(finalLog);
      setExecutionLogs(prev => [finalLog, ...prev]);
      
      setCurrentExecution({ ...execution });
      setExecutionHistory(prev => [execution, ...prev].slice(0, 10)); // Keep last 10
      
      toast.success('Workflow executed successfully');
    } catch (error) {
      // Workflow failed
      const workflowDuration = Date.now() - workflowStartTime;
      execution.status = 'failed';
      execution.endTime = new Date();
      execution.duration = workflowDuration;
      
      const errorLog: ExecutionLog = {
        id: `log-${Date.now()}-error`,
        timestamp: new Date(),
        nodeId: 'workflow',
        nodeName: 'Workflow',
        type: 'error',
        message: `Workflow execution failed: ${error}`,
        duration: workflowDuration
      };
      execution.logs.push(errorLog);
      setExecutionLogs(prev => [errorLog, ...prev]);
      
      setCurrentExecution({ ...execution });
      setExecutionHistory(prev => [execution, ...prev].slice(0, 10));
      
      toast.error('Workflow execution failed');
    } finally {
      setIsExecuting(false);
    }
  };
  
  const handleSaveWorkflow = async () => {
    try {
      // Format workflow for API
      const workflowData = {
        name: 'My Workflow',
        description: 'Workflow created with improved builder',
        graph_definition: {
          nodes: nodes.map(node => ({
            id: node.id,
            type: node.type,
            position: node.position,
            data: node.data
          })),
          edges: edges.map(edge => ({
            id: edge.id || `edge-${edge.source}-${edge.target}`,
            source: edge.source,
            target: edge.target,
            type: edge.type || 'default'
          }))
        },
        is_public: false
      };
      
      // Save to localStorage for now
      localStorage.setItem('workflow', JSON.stringify(workflowData));
      
      // TODO: Save to API
      // const response = await fetch('/api/agent-builder/workflows', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(workflowData)
      // });
      
      toast.success('Workflow saved');
      
      addLog({
        nodeId: 'workflow',
        nodeName: 'Workflow',
        type: 'success',
        message: 'Workflow saved successfully'
      });
    } catch (error) {
      toast.error('Failed to save workflow');
      addLog({
        nodeId: 'workflow',
        nodeName: 'Workflow',
        type: 'error',
        message: `Failed to save: ${error}`
      });
    }
  };
  
  const handleLoadWorkflow = () => {
    const saved = localStorage.getItem('workflow');
    if (saved) {
      const workflow = JSON.parse(saved);
      setNodes(workflow.nodes);
      setEdges(workflow.edges);
      toast.success('Workflow loaded');
      
      addLog({
        nodeId: 'workflow',
        nodeName: 'Workflow',
        type: 'success',
        message: 'Workflow loaded successfully'
      });
    } else {
      toast.error('No saved workflow found');
    }
  };
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="h-16 border-b bg-white dark:bg-gray-950 px-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Workflow Builder</h1>
          <p className="text-sm text-muted-foreground">
            Build powerful automation workflows with AI agents and tools
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoadWorkflow}
          >
            <Upload className="h-4 w-4 mr-2" />
            Load
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveWorkflow}
          >
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
          
          <Button
            variant="outline"
            size="sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          
          <Button
            variant="outline"
            size="sm"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          
          <Button
            onClick={handleExecuteWorkflow}
            disabled={isExecuting || nodes.length === 0}
            className="ml-2"
          >
            <Play className="h-4 w-4 mr-2" />
            {isExecuting ? 'Executing...' : 'Execute'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExecutionPanel(!showExecutionPanel)}
            className="ml-2"
          >
            {showExecutionPanel ? (
              <>
                <Minimize2 className="h-4 w-4 mr-2" />
                Hide Logs
              </>
            ) : (
              <>
                <Maximize2 className="h-4 w-4 mr-2" />
                Show Logs
              </>
            )}
          </Button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {/* Left Sidebar - Block Palette with Logs */}
        <div className="w-80 border-r bg-gray-50 dark:bg-gray-900 flex flex-col">
          <ImprovedBlockPalette
            onAddNode={handleAddNode}
            executionLogs={executionLogs}
            showLogs={showExecutionLogs}
            onToggleLogs={() => setShowExecutionLogs(!showExecutionLogs)}
          />
        </div>
        
        {/* Center - Workflow Canvas */}
        <div className="flex-1 bg-gray-100 dark:bg-gray-950">
          <VisualWorkflowCanvas
            nodes={nodes}
            edges={edges}
            nodeExecutions={currentExecution?.nodeExecutions || []}
            isExecuting={isExecuting}
          />
        </div>
        
        {/* Right Sidebar - Execution Panel */}
        {showExecutionPanel && (
          <div className="w-96 border-l bg-white dark:bg-gray-950">
            <WorkflowExecutionPanel
              workflowId="workflow-1"
              {...(currentExecution && { currentExecution })}
              executionHistory={executionHistory}
              onExecute={handleExecuteWorkflow}
              onStop={() => setIsExecuting(false)}
              onClear={() => {
                setCurrentExecution(null);
                setExecutionLogs([]);
              }}
              isExecuting={isExecuting}
            />
          </div>
        )}
      </div>
    </div>
  );
}
