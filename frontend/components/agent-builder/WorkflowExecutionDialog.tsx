'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, XCircle, Loader2, Clock, Zap, Activity } from 'lucide-react';

interface ExecutionStep {
  step_id: string;
  type: string;
  content: string;
  timestamp: string;
  metadata?: any;
}

interface ExecutionMetrics {
  duration: number;
  tokens: number;
  toolCalls: number;
  status: 'running' | 'completed' | 'failed';
}

interface WorkflowExecutionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  executionId: string | null;
  workflowName: string;
}

export default function WorkflowExecutionDialog({
  isOpen,
  onClose,
  executionId,
  workflowName,
}: WorkflowExecutionDialogProps) {
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    if (!executionId || !isOpen) return;

    setIsExecuting(true);
    
    // Connect to SSE endpoint for real-time updates
    const eventSource = new EventSource(
      `/api/agent-builder/executions/${executionId}/stream`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'step') {
          setSteps((prev) => [...prev, data.step]);
          
          // Update active nodes
          if (data.step.metadata?.node_id) {
            setActiveNodes((prev) => new Set(prev).add(data.step.metadata.node_id));
          }
        } else if (data.type === 'metrics') {
          setMetrics(data.metrics);
        } else if (data.type === 'complete') {
          setIsExecuting(false);
          setMetrics(data.metrics);
          eventSource.close();
        } else if (data.type === 'error') {
          setIsExecuting(false);
          setMetrics({ ...data.metrics, status: 'failed' });
          eventSource.close();
        }
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
      }
    };

    eventSource.onerror = () => {
      setIsExecuting(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [executionId, isOpen]);

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'agent_execution':
        return <Activity className="h-4 w-4 text-blue-500" />;
      case 'block_execution':
        return <Zap className="h-4 w-4 text-green-500" />;
      case 'control_flow':
        return <CheckCircle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Workflow Execution: {workflowName}</DialogTitle>
          <DialogDescription>
            {isExecuting ? 'Execution in progress...' : 'Execution completed'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Execution Status */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                {isExecuting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : metrics?.status === 'completed' ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    Completed
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-red-500" />
                    Failed
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isExecuting && (
                <Progress value={undefined} className="w-full" />
              )}
              
              {metrics && (
                <div className="grid grid-cols-3 gap-4 mt-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      Duration
                    </div>
                    <div className="text-lg font-semibold">
                      {(metrics.duration / 1000).toFixed(2)}s
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Zap className="h-3 w-3" />
                      Tokens
                    </div>
                    <div className="text-lg font-semibold">{metrics.tokens}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Activity className="h-3 w-3" />
                      Tool Calls
                    </div>
                    <div className="text-lg font-semibold">{metrics.toolCalls}</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Separator />

          {/* Execution Steps */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Execution Steps</h4>
            <ScrollArea className="h-[400px]">
              {steps.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Activity className="h-8 w-8 mb-2" />
                  <p className="text-sm">Waiting for execution to start...</p>
                </div>
              ) : (
                <div className="space-y-3 pr-4">
                  {steps.map((step, index) => (
                    <Card key={step.step_id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {getStepIcon(step.type)}
                            <span className="text-sm font-medium capitalize">
                              {step.type.replace('_', ' ')}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              Step {index + 1}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatTimestamp(step.timestamp)}
                            </span>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm whitespace-pre-wrap">{step.content}</p>
                        {step.metadata && Object.keys(step.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-muted-foreground cursor-pointer">
                              View metadata
                            </summary>
                            <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-auto">
                              {JSON.stringify(step.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {!isExecuting && metrics?.status === 'completed' && (
              <Button onClick={() => window.open(`/agent-builder/executions/${executionId}`, '_blank')}>
                View Full Details
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
