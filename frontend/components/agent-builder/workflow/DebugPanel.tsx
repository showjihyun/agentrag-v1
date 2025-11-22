'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Play,
  Pause,
  StepForward,
  SkipForward,
  RotateCcw,
  Bug,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { Node } from 'reactflow';

interface BreakpointConfig {
  nodeId: string;
  enabled: boolean;
  condition?: string;
}

interface ExecutionState {
  nodeId: string;
  timestamp: Date;
  status: 'running' | 'success' | 'error' | 'paused';
  input?: any;
  output?: any;
  error?: string;
  duration?: number;
  memory?: number;
  cpu?: number;
}

interface DebugPanelProps {
  nodes: Node[];
  currentNodeId?: string;
  executionHistory: ExecutionState[];
  breakpoints: BreakpointConfig[];
  onBreakpointToggle: (nodeId: string) => void;
  onStepOver: () => void;
  onStepInto: () => void;
  onContinue: () => void;
  onRestart: () => void;
  onTimeTravel: (timestamp: Date) => void;
}

export function DebugPanel({
  nodes,
  currentNodeId,
  executionHistory,
  breakpoints,
  onBreakpointToggle,
  onStepOver,
  onStepInto,
  onContinue,
  onRestart,
  onTimeTravel,
}: DebugPanelProps) {
  const [selectedHistoryIndex, setSelectedHistoryIndex] = useState<number | null>(null);

  const currentState = executionHistory[executionHistory.length - 1];
  const selectedState = selectedHistoryIndex !== null 
    ? executionHistory[selectedHistoryIndex] 
    : currentState;

  const getNodeName = useCallback((nodeId: string) => {
    return nodes.find(n => n.id === nodeId)?.data.label || nodeId;
  }, [nodes]);

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatMemory = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Bug className="h-4 w-4" />
            Debug Panel
          </CardTitle>
          {currentState && (
            <Badge variant={
              currentState.status === 'success' ? 'default' :
              currentState.status === 'error' ? 'destructive' :
              currentState.status === 'paused' ? 'secondary' :
              'outline'
            }>
              {currentState.status}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4 overflow-hidden">
        {/* Debug Controls */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onContinue}
            disabled={currentState?.status !== 'paused'}
          >
            <Play className="h-3 w-3 mr-1" />
            Continue
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onStepOver}
            disabled={currentState?.status !== 'paused'}
          >
            <StepForward className="h-3 w-3 mr-1" />
            Step Over
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onStepInto}
            disabled={currentState?.status !== 'paused'}
          >
            <SkipForward className="h-3 w-3 mr-1" />
            Step Into
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onRestart}
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
        </div>

        <Tabs defaultValue="state" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="state">State</TabsTrigger>
            <TabsTrigger value="breakpoints">Breakpoints</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>

          {/* Current State */}
          <TabsContent value="state" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              {selectedState ? (
                <div className="space-y-4">
                  {/* Node Info */}
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Current Node</h4>
                    <div className="bg-muted p-3 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Node:</span>
                        <span className="text-sm font-medium">
                          {getNodeName(selectedState.nodeId)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Status:</span>
                        <Badge variant={
                          selectedState.status === 'success' ? 'default' :
                          selectedState.status === 'error' ? 'destructive' :
                          'outline'
                        }>
                          {selectedState.status}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Duration:</span>
                        <span className="text-sm">{formatDuration(selectedState.duration)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Input */}
                  {selectedState.input && (
                    <div>
                      <h4 className="text-sm font-semibold mb-2">Input</h4>
                      <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-40">
                        {JSON.stringify(selectedState.input, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Output */}
                  {selectedState.output && (
                    <div>
                      <h4 className="text-sm font-semibold mb-2">Output</h4>
                      <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-40">
                        {JSON.stringify(selectedState.output, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Error */}
                  {selectedState.error && (
                    <div>
                      <h4 className="text-sm font-semibold mb-2 text-destructive">Error</h4>
                      <div className="bg-destructive/10 border border-destructive/20 p-3 rounded-lg">
                        <p className="text-sm text-destructive">{selectedState.error}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-40 text-muted-foreground">
                  <p className="text-sm">No execution state</p>
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          {/* Breakpoints */}
          <TabsContent value="breakpoints" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="space-y-2">
                {nodes.map((node) => {
                  const breakpoint = breakpoints.find(bp => bp.nodeId === node.id);
                  const isEnabled = breakpoint?.enabled ?? false;

                  return (
                    <div
                      key={node.id}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-muted cursor-pointer"
                      onClick={() => onBreakpointToggle(node.id)}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          isEnabled ? 'bg-red-500' : 'bg-gray-300'
                        }`} />
                        <span className="text-sm">{node.data.label}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {node.type}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Execution History */}
          <TabsContent value="history" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="space-y-2">
                {executionHistory.map((state, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedHistoryIndex === index
                        ? 'bg-primary/10 border-primary'
                        : 'hover:bg-muted'
                    }`}
                    onClick={() => {
                      setSelectedHistoryIndex(index);
                      onTimeTravel(state.timestamp);
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {state.status === 'success' && (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        )}
                        {state.status === 'error' && (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        {state.status === 'running' && (
                          <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                        )}
                        {state.status === 'paused' && (
                          <Pause className="h-4 w-4 text-yellow-500" />
                        )}
                        <span className="text-sm font-medium">
                          {getNodeName(state.nodeId)}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {state.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDuration(state.duration)}
                      </span>
                      {state.error && (
                        <span className="flex items-center gap-1 text-destructive">
                          <AlertTriangle className="h-3 w-3" />
                          Error
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Performance Metrics */}
          <TabsContent value="performance" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="space-y-4">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Total Duration</div>
                    <div className="text-lg font-semibold">
                      {formatDuration(
                        executionHistory.reduce((sum, s) => sum + (s.duration || 0), 0)
                      )}
                    </div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Avg Duration</div>
                    <div className="text-lg font-semibold">
                      {formatDuration(
                        executionHistory.reduce((sum, s) => sum + (s.duration || 0), 0) /
                        (executionHistory.length || 1)
                      )}
                    </div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Success Rate</div>
                    <div className="text-lg font-semibold text-green-600">
                      {executionHistory.length > 0
                        ? Math.round(
                            (executionHistory.filter(s => s.status === 'success').length /
                              executionHistory.length) *
                              100
                          )
                        : 0}
                      %
                    </div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Error Rate</div>
                    <div className="text-lg font-semibold text-red-600">
                      {executionHistory.length > 0
                        ? Math.round(
                            (executionHistory.filter(s => s.status === 'error').length /
                              executionHistory.length) *
                              100
                          )
                        : 0}
                      %
                    </div>
                  </div>
                </div>

                {/* Node Performance */}
                <div>
                  <h4 className="text-sm font-semibold mb-2">Node Performance</h4>
                  <div className="space-y-2">
                    {nodes.map((node) => {
                      const nodeStates = executionHistory.filter(s => s.nodeId === node.id);
                      const avgDuration = nodeStates.length > 0
                        ? nodeStates.reduce((sum, s) => sum + (s.duration || 0), 0) / nodeStates.length
                        : 0;
                      const successRate = nodeStates.length > 0
                        ? (nodeStates.filter(s => s.status === 'success').length / nodeStates.length) * 100
                        : 0;

                      return (
                        <div key={node.id} className="bg-muted p-3 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">{node.data.label}</span>
                            <Badge variant={successRate > 90 ? 'default' : 'destructive'}>
                              {successRate.toFixed(0)}%
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>Avg: {formatDuration(avgDuration)}</span>
                            <span>{nodeStates.length} executions</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
