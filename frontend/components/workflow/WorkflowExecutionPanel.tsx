'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Play,
  Square,
  RotateCcw,
  ChevronRight,
  ChevronDown,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Terminal,
  Activity,
  TrendingUp,
  Download,
  Trash2
} from 'lucide-react';

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

interface NodeExecution {
  nodeId: string;
  nodeName: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
}

interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  nodeExecutions: NodeExecution[];
  logs: ExecutionLog[];
}

interface WorkflowExecutionPanelProps {
  workflowId: string;
  currentExecution?: WorkflowExecution;
  executionHistory: WorkflowExecution[];
  onExecute: () => void;
  onStop: () => void;
  onClear: () => void;
  isExecuting: boolean;
}

export function WorkflowExecutionPanel({
  workflowId,
  currentExecution,
  executionHistory,
  onExecute,
  onStop,
  onClear,
  isExecuting
}: WorkflowExecutionPanelProps) {
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current');

  useEffect(() => {
    if (currentExecution) {
      setSelectedExecution(currentExecution);
      setActiveTab('current');
    }
  }, [currentExecution]);

  const toggleNodeExpand = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getStatusIcon = (status: NodeExecution['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'skipped':
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getLogIcon = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  const getLogColor = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const exportLogs = () => {
    if (!selectedExecution) return;
    
    const data = {
      executionId: selectedExecution.id,
      workflowId: selectedExecution.workflowId,
      status: selectedExecution.status,
      duration: selectedExecution.duration,
      logs: selectedExecution.logs,
      nodeExecutions: selectedExecution.nodeExecutions
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution-${selectedExecution.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">Execution</h3>
          </div>
          
          <div className="flex items-center gap-2">
            {selectedExecution && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={exportLogs}
                  className="h-8"
                >
                  <Download className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClear}
                  className="h-8"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Execution Controls */}
        <div className="flex items-center gap-2">
          <Button
            onClick={onExecute}
            disabled={isExecuting}
            size="sm"
            className="flex-1"
          >
            {isExecuting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Execute
              </>
            )}
          </Button>
          
          {isExecuting && (
            <Button
              onClick={onStop}
              variant="destructive"
              size="sm"
            >
              <Square className="h-4 w-4" />
            </Button>
          )}
          
          <Button
            onClick={onClear}
            variant="outline"
            size="sm"
            disabled={isExecuting}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>

        {/* Execution Status */}
        {currentExecution && (
          <div className="mt-3 p-2 bg-white dark:bg-gray-950 rounded border">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    currentExecution.status === 'completed' ? 'default' :
                    currentExecution.status === 'failed' ? 'destructive' :
                    'secondary'
                  }
                >
                  {currentExecution.status}
                </Badge>
                <span className="text-muted-foreground">
                  {formatDuration(currentExecution.duration)}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {currentExecution.startTime.toLocaleTimeString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col min-h-0">
        <div className="px-4 pt-2 border-b">
          <TabsList className="w-full">
            <TabsTrigger value="current" className="flex-1">
              <Terminal className="h-4 w-4 mr-2" />
              Current
            </TabsTrigger>
            <TabsTrigger value="history" className="flex-1">
              <TrendingUp className="h-4 w-4 mr-2" />
              History ({executionHistory.length})
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Current Execution Tab */}
        <TabsContent value="current" className="flex-1 m-0 min-h-0">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-3">
              {!selectedExecution ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No execution yet</p>
                  <p className="text-xs mt-1">Click Execute to run the workflow</p>
                </div>
              ) : (
                <>
                  {/* Node Executions */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold mb-2">Node Executions</h4>
                    {selectedExecution.nodeExecutions.map((nodeExec) => (
                      <div
                        key={nodeExec.nodeId}
                        className="border rounded-lg overflow-hidden"
                      >
                        <div
                          className="p-3 bg-white dark:bg-gray-950 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                          onClick={() => toggleNodeExpand(nodeExec.nodeId)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              {getStatusIcon(nodeExec.status)}
                              <span className="font-medium text-sm truncate">
                                {nodeExec.nodeName}
                              </span>
                              {nodeExec.duration && (
                                <Badge variant="outline" className="text-xs">
                                  {formatDuration(nodeExec.duration)}
                                </Badge>
                              )}
                            </div>
                            {expandedNodes.has(nodeExec.nodeId) ? (
                              <ChevronDown className="h-4 w-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-gray-400" />
                            )}
                          </div>
                        </div>

                        {expandedNodes.has(nodeExec.nodeId) && (
                          <div className="p-3 bg-gray-50 dark:bg-gray-900 border-t space-y-2">
                            {nodeExec.input && (
                              <div>
                                <p className="text-xs font-semibold mb-1">Input:</p>
                                <pre className="text-xs bg-white dark:bg-gray-950 p-2 rounded border overflow-x-auto">
                                  {JSON.stringify(nodeExec.input, null, 2)}
                                </pre>
                              </div>
                            )}
                            
                            {nodeExec.output && (
                              <div>
                                <p className="text-xs font-semibold mb-1">Output:</p>
                                <pre className="text-xs bg-white dark:bg-gray-950 p-2 rounded border overflow-x-auto">
                                  {JSON.stringify(nodeExec.output, null, 2)}
                                </pre>
                              </div>
                            )}
                            
                            {nodeExec.error && (
                              <div>
                                <p className="text-xs font-semibold mb-1 text-red-600">Error:</p>
                                <pre className="text-xs bg-red-50 dark:bg-red-950 text-red-600 p-2 rounded border border-red-200 overflow-x-auto">
                                  {nodeExec.error}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Logs */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold mb-2">Logs</h4>
                    {selectedExecution.logs.map((log) => (
                      <div
                        key={log.id}
                        className={`p-2 rounded border ${getLogColor(log.type)}`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-sm font-mono font-bold">
                            {getLogIcon(log.type)}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-medium truncate">
                                {log.nodeName}
                              </span>
                              {log.duration && (
                                <Badge variant="outline" className="text-xs">
                                  {formatDuration(log.duration)}
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs">{log.message}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {log.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="flex-1 m-0 min-h-0">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-2">
              {executionHistory.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No execution history</p>
                </div>
              ) : (
                executionHistory.map((execution) => (
                  <div
                    key={execution.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedExecution?.id === execution.id
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900'
                    }`}
                    onClick={() => {
                      setSelectedExecution(execution);
                      setActiveTab('current');
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge
                        variant={
                          execution.status === 'completed' ? 'default' :
                          execution.status === 'failed' ? 'destructive' :
                          'secondary'
                        }
                      >
                        {execution.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {execution.startTime.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {execution.nodeExecutions.length} nodes
                      </span>
                      <span className="font-medium">
                        {formatDuration(execution.duration)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
